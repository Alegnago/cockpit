"""Cockpit triathlon stampabile – modello parametrico CadQuery (v0.2, rifatto dal video a 360°).

Assi: X laterale (+ = destra), Y longitudinale (0 = fronte, + = verso il ciclista),
Z verticale (0 = asse estensioni). Unità mm.

Forma:
- vasca a barca: fondo piatto, pareti dritte svasate verso l'esterno, retro aperto
- due lobi convessi sopra le estensioni (carenatura), canale stretto tra i lobi
- dorsale piena sotto il fondo con le sedi a scatto per le estensioni

Uso:  python cockpit.py            -> esporta STEP/STL in ./out
"""
import math
from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------- parametri
P = dict(
    ext_d=22.2,          # diametro estensioni (standard)
    ext_cc=70.0,         # interasse estensioni  << MISURARE SULLA BICI
    fit=0.25,            # gioco radiale sede/estensione
    clip_open=19.0,      # apertura a scatto sotto (< ext_d) – tarare con P0
    t=2.4,               # spessore fondo e pareti
    L=360.0,             # lunghezza vassoio
    y_shoulder=15.0,     # dove iniziano le pareti
    y_split=180.0,       # giunzione tra le 2 metà
    # profilo pareti (vista laterale): (y, semi-larghezza bordo, quota bordo da asse estensioni)
    # basse in punta, salgono quasi lineari fino al retro
    wall=((15.0, 66.0, 12.0), (150.0, 92.0, 36.0), (260.0, 112.0, 56.0), (360.0, 118.0, 74.0)),
    flare=22.0,          # svasatura pareti dalla verticale (°)
    z_floor=-6.0,        # faccia inferiore del fondo
    # chiglia sotto il fondo (vista laterale): (y, quota fondo dorsale); si approfondisce fino
    # a ~75% della lunghezza, poi gradino verso una coda meno profonda
    keel=((0.0, -14.0), (280.0, -30.0), (280.0, -18.0), (360.0, -18.0)),
    # lobi (vista dall'alto): partono sui tubi e divergono verso il retro, allargandosi
    lobe_y=(0.0, 290.0, 345.0),  # sezioni lungo Y
    lobe_x=(35.0, 72.0, 76.0),   # centro lobo (|X|)
    lobe_r=(15.0, 28.0, 30.0),   # semi-larghezza lobo
    lobe_h=(18.0, 24.0, 4.0),    # quota cima lobo (da asse estensioni)
    housing_wall=2.6,            # carenatura estensioni nel canale
    rear_w=72.0,                 # larghezza blocco posteriore
    rear_y0=268.0,               # inizio blocco posteriore
    rear_z0=30.0,                # quota faccia superiore del blocco all'inizio
    arm_angle=25.0,              # braccio portaborraccia fisso: inclinazione verso l'alto andando indietro
    arm_root=275.0,              # Y dove il braccio appoggia sul blocco
    arm_len=190.0,
    arm_bolts=(15.0, 55.0),      # viti di fissaggio lungo il braccio (da radice)
    tube_od=28.0,        # tubi punta
    tube_straight=45.0,  # tratto dritto (sede estensione)
    tube_socket=40.0,    # quanto il tubo entra nel vassoio (tratto dritto nascosto)
    tube_bend_r=40.0,
    tube_angle=60.0,     # piega verso l'alto
    tube_tip=40.0,       # tratto finale (shifter)
    shifter_d=21.6,      # foro punta per shifter Di2 (SW-R9160: Ø19–22.5)
    cage_hole_cc=64.0,   # standard portaborraccia
)

OUT = Path(__file__).with_name("out")
POST_Y = (120.0, 145.0, 170.0)  # posizioni supporto computer


def r_bore(p):
    return p["ext_d"] / 2 + p["fit"]


def spine_bottom(p):
    """Quota più bassa della chiglia."""
    return min(z for _, z in p["keel"])


def keel_z(p, y):
    """Quota del fondo chiglia alla coordinata y (primo tratto che contiene y)."""
    k = p["keel"]
    for (y0, z0), (y1, z1) in zip(k, k[1:]):
        if y0 <= y <= y1 and y1 > y0:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return k[-1][1]


def spine_half(p):
    return p["ext_cc"] / 2 + r_bore(p) + 3.5


# ---------------------------------------------------------------- vasca
def tub_section(p, W, H):
    """Poligono (x,z) del guscio destro: fondo da x=0 a Wf, poi parete svasata fino a (W, H)."""
    t, zf = p["t"], p["z_floor"]
    k = math.tan(math.radians(p["flare"]))
    Wf = W - (H - zf) * k                 # spigolo esterno fondo
    r = 6.0                               # raccordo fondo/parete
    pts_out = [(0, zf), (Wf - r * 0.4, zf)]
    for i in range(1, 6):                 # raccordo esterno
        a = math.radians(90 * i / 5) * (1 - p["flare"] / 90)
        pts_out.append((Wf - r * 0.4 + r * math.sin(a) * 0.6, zf + r * (1 - math.cos(a)) * 0.6))
    pts_out.append((W, H))
    # lato interno: offset di t verso l'alto/l'interno
    tn = t / math.cos(math.radians(p["flare"]))
    pts_in = [(W - tn, H), (Wf - tn * 0.6 + 0.6, zf + t + 1.2), (Wf - r, zf + t), (0, zf + t)]
    return pts_out + pts_in


def tub(p):
    secs = list(p["wall"])
    def loft(s0, s1):
        wires = [cq.Wire.makePolygon([cq.Vector(x, y, z) for x, z in tub_section(p, W, H)], close=True)
                 for y, W, H in (s0, s1)]
        return cq.Workplane().add(cq.Solid.makeLoft(wires, ruled=True))
    right = loft(secs[0], secs[1])
    for a, b in zip(secs[1:], secs[2:]):
        right = right.union(loft(a, b))
    half = right.union(right.mirror("YZ"))
    # parete frontale: chiude la vasca alla spalla fino al bordo
    y0, W, H = secs[0]
    Wf = W - (H - p["z_floor"]) * math.tan(math.radians(p["flare"]))
    cap = (cq.Workplane("XZ", origin=(0, y0 + p["t"], 0))
           .polyline([(-Wf, p["z_floor"]), (Wf, p["z_floor"]), (W, H), (-W, H)]).close()
           .extrude(p["t"]))
    # piano fondo davanti alla spalla (sotto la piastra frontale)
    nose = (cq.Workplane("XY", origin=(0, 0, p["z_floor"])).center(0, y0 / 2)
            .rect(2 * spine_half(p), y0).extrude(p["t"]))
    return half.union(cap).union(nose)


# ---------------------------------------------------------------- lobi + dorsale
def lobes(p):
    """Lobi convessi divergenti (loft di semiellissi appoggiate al fondo)."""
    zf = p["z_floor"]
    out = None
    for sx in (-1, 1):
        wires = []
        for y, cx, rx, rz in zip(p["lobe_y"], p["lobe_x"], p["lobe_r"], p["lobe_h"]):
            n = 24
            pts = [cq.Vector(sx * cx + rx * math.cos(math.pi * i / n), y, zf + (rz - zf) * math.sin(math.pi * i / n))
                   for i in range(n + 1)]
            wires.append(cq.Wire.makePolygon(pts, close=True))
        lo = (cq.Workplane().add(cq.Solid.makeLoft(wires[:2], ruled=True))
              .union(cq.Workplane().add(cq.Solid.makeLoft(wires[1:], ruled=True))))
        out = lo if out is None else out.union(lo)
    return out


def housings(p):
    """Carenature cilindriche attorno alle estensioni, visibili come nervature nel canale."""
    r = r_bore(p) + p["housing_wall"]
    out = None
    for sx in (-1, 1):
        h = (cq.Workplane("XZ", origin=(0, 0, 0)).center(sx * p["ext_cc"] / 2, 0)
             .circle(r).extrude(-p["L"]))
        out = h if out is None else out.union(h)
    return out


def spine(p):
    """Dorsale piena a chiglia sotto il fondo: profilo laterale estruso in X."""
    sh = spine_half(p)
    ztop = p["z_floor"] + p["t"]
    prof = [(y, z) for y, z in p["keel"]] + [(p["L"], ztop), (0.0, ztop)]
    body = (cq.Workplane("YZ", origin=(-sh, 0, 0)).polyline(prof).close().extrude(2 * sh))
    return body


def ext_seats(p):
    """Sedi estensioni: foro passante + apertura a scatto verso il basso."""
    cut = None
    for sx in (-1, 1):
        cx = sx * p["ext_cc"] / 2
        b = cq.Workplane("XZ", origin=(0, -1, 0)).center(cx, 0).circle(r_bore(p)).extrude(-(p["L"] + 2))
        o = (cq.Workplane("XZ", origin=(0, -1, 0)).center(cx, (spine_bottom(p) - 1) / 2)
             .rect(p["clip_open"], -(spine_bottom(p) - 1)).extrude(-(p["L"] + 2)))
        s = b.union(o)
        cut = s if cut is None else cut.union(s)
    return cut


# ---------------------------------------------------------------- piastra frontale / blocco posteriore
def front_plate(p):
    """Piastra esagonale tra i lobi che copre l'inizio del canale."""
    top = p["lobe_h"][0]
    w = p["ext_cc"] / 2
    plate = (cq.Workplane("XY", origin=(0, 0, p["z_floor"]))
             .polyline([(-w, 0), (w, 0), (w, 26), (12, 44), (-12, 44), (-w, 26)]).close()
             .extrude(top - p["z_floor"]))
    return plate


def rear_top_z(p, y):
    """Quota della faccia superiore inclinata del blocco posteriore."""
    return p["rear_z0"] + (y - p["rear_y0"]) * math.tan(math.radians(p["arm_angle"]))


def arm_frame(p):
    """Piano locale del braccio: origine sulla radice, Y lungo il braccio, Z normale alla faccia."""
    a = math.radians(p["arm_angle"])
    y0 = p["arm_root"]
    return (0.0, y0, rear_top_z(p, y0)), (0.0, math.cos(a), math.sin(a)), (0.0, -math.sin(a), math.cos(a))


def rear_block(p):
    """Blocco posteriore sopra il canale, faccia superiore inclinata su cui si fissa il braccio."""
    zf, t = p["z_floor"], p["t"]
    y0, y1 = p["rear_y0"], p["L"]
    prof = [(y0, zf), (y1, zf), (y1, rear_top_z(p, y1)), (y0, rear_top_z(p, y0))]
    box = cq.Workplane("YZ", origin=(-p["rear_w"] / 2, 0, 0)).polyline(prof).close().extrude(p["rear_w"])
    zt = 26.0
    box = box.cut(cq.Workplane("XZ", origin=(0, y0 - 1, 0)).center(0, (zf + t + zt - 3) / 2)
                  .rect(26, zt - 3 - zf - t).extrude(-(y1 - y0) - 2))  # tunnel gel
    org, ydir, n = arm_frame(p)
    for d in p["arm_bolts"]:  # sedi inserti a caldo M5 (Ø6.4 x 12) perpendicolari alla faccia
        pt = (0.0, org[1] + d * ydir[1], org[2] + d * ydir[2])
        box = box.cut(cq.Workplane(cq.Plane(origin=pt, xDir=(1, 0, 0), normal=n)).circle(3.2).extrude(-12))
    return box


def holes(p):
    zb, zf, t = spine_bottom(p), p["z_floor"], p["t"]
    cut = None
    def add(s):
        nonlocal cut
        cut = s if cut is None else cut.union(s)
    for sx in (-1, 1):  # asole cinghia posteriori
        add(cq.Workplane("XY", origin=(0, 0, zf - 1)).center(sx * 86, 338).rect(8, 12).extrude(t + 2))
    for y in POST_Y:    # supporto computer: M5 passante nella dorsale + sede dado sotto + perno
        zk = keel_z(p, y)
        add(cq.Workplane("XY", origin=(0, 0, zk - 1)).center(0, y).circle(2.75).extrude(zf + t - zk + 2))
        add(cq.Workplane("XY", origin=(0, 0, zk - 1)).center(0, y).polygon(6, 9.4).extrude(5))
        add(cq.Workplane("XY", origin=(0, 0, zf + t - 4)).center(0, y + 9).circle(2.1).extrude(5))
    return cut


def tube_sockets(p):
    """Sedi nel muso dove si infilano i tubi punta."""
    cut = None
    for sx in (-1, 1):
        c = (cq.Workplane("XZ", origin=(0, -1, 0)).center(sx * p["ext_cc"] / 2, 0)
             .circle(p["tube_od"] / 2 + 0.2).extrude(-(p["tube_socket"] + 1)))
        cut = c if cut is None else cut.union(c)
    return cut


def tray(p):
    t = (tub(p).union(lobes(p)).union(housings(p)).union(spine(p))
         .union(front_plate(p)).union(rear_block(p)))
    return t.cut(ext_seats(p)).cut(tube_sockets(p)).cut(holes(p))


def split(p, solid):
    """Due metà + fori spine di allineamento Ø4.2 nella dorsale."""
    big = 1000
    front = solid.intersect(cq.Workplane("XY").box(big, p["y_split"] + 50, big, centered=(True, False, True))
                            .translate((0, -50, 0)))
    rear = solid.intersect(cq.Workplane("XY").box(big, big, big, centered=(True, False, True))
                           .translate((0, p["y_split"], 0)))
    zp = (keel_z(p, p["y_split"]) + p["z_floor"]) / 2
    pins = None
    for x in (-12.0, 12.0):
        c = cq.Workplane("XZ", origin=(0, p["y_split"] + 12, 0)).center(x, zp).circle(2.1).extrude(24)
        pins = c if pins is None else pins.union(c)
    return front.cut(pins), rear.cut(pins)


# ---------------------------------------------------------------- tubi punta
def tip_tube(p):
    """Tubo punta (destro). Calza sull'estremità dell'estensione; lo shifter entra in punta."""
    a = math.radians(p["tube_angle"])
    R, s0, s1 = p["tube_bend_r"], p["tube_straight"], p["tube_tip"]
    def path(ext=0.0, start=0.0):
        return (cq.Workplane("YZ").moveTo(start, 0).lineTo(-s0, 0)
                .radiusArc((-s0 - R * math.sin(a), R * (1 - math.cos(a))), R)
                .lineTo(-s0 - R * math.sin(a) - (s1 + ext) * math.cos(a), R * (1 - math.cos(a)) + (s1 + ext) * math.sin(a)))
    outer = cq.Workplane("XZ").circle(p["tube_od"] / 2).sweep(path())
    inner = cq.Workplane("XZ", origin=(0, 1, 0)).circle(p["shifter_d"] / 2).sweep(path(2.0, 1.0))
    seat = cq.Workplane("XZ", origin=(0, 1, 0)).circle(r_bore(p)).extrude(s0 - 4)  # l'estensione finisce qui
    tube = outer.cut(inner).cut(seat)
    # inserto a caldo M4 per grano di bloccaggio (sotto)
    return tube.cut(cq.Workplane("XY", origin=(0, -18, -p["tube_od"] / 2 - 1)).circle(2.8).extrude(6))


# ---------------------------------------------------------------- supporto computer
def computer_post(p, h=52.0):
    post = cq.Workplane("XY").circle(12.5).extrude(h)
    post = post.union(cq.Workplane("XY", origin=(0, 0, h)).circle(16.5).extrude(4))
    post = post.union(cq.Workplane("XY", origin=(0, 9, -3)).circle(1.9).extrude(3))   # perno antirotazione
    post = post.cut(cq.Workplane("XY", origin=(0, 0, -1)).circle(2.75).extrude(h))     # M5 dall'alto
    post = post.cut(cq.Workplane("XY", origin=(0, 0, 8)).circle(5).extrude(h - 13))    # accesso testa vite
    for x in (-10, 10):
        post = post.cut(cq.Workplane("XY", origin=(x, 0, h)).circle(1.4).extrude(10))  # M3 puck
    return post


# ---------------------------------------------------------------- braccio portaborraccia
def cage_arm(p):
    """Braccio portaborraccia fisso (stampato in piano). Y locale = lungo il braccio, appoggio a z=0."""
    L, w, th = p["arm_len"], 24.0, 9.0
    arm = cq.Workplane("XY").center(0, L / 2).slot2D(L, w, angle=90).extrude(th)
    for d in p["arm_bolts"]:  # fissaggio sul blocco: M5 svasata
        arm = arm.cut(cq.Workplane("XY", origin=(0, d, -1)).circle(2.75).extrude(th + 2))
        arm = arm.cut(cq.Workplane("XY", origin=(0, d, th - 3)).circle(5.2).extrude(4))
    for d in (L - 20 - p["cage_hole_cc"], L - 20):  # gabbia: M5 + dado sotto
        arm = arm.cut(cq.Workplane("XY", origin=(0, d, -1)).circle(2.75).extrude(th + 2))
        arm = arm.cut(cq.Workplane("XY", origin=(0, d, -1)).polygon(6, 9.4).extrude(4.5))
    return arm


# ---------------------------------------------------------------- export
def build(p=P):
    parts = {}
    full = tray(p)
    parts["P1_vassoio_anteriore"], parts["P2_vassoio_posteriore"] = split(p, full)
    # fetta di prova 15 mm: verifica aggancio sulle estensioni prima della stampa completa
    parts["P0_test_clip"] = full.intersect(
        cq.Workplane("XY").box(400, 15, 200, centered=(True, False, True)).translate((0, 100, 0)))
    tube_r = tip_tube(p)
    parts["P3_tubo_punta_dx"] = tube_r
    parts["P3_tubo_punta_sx"] = tube_r.mirror("YZ")
    parts["P4_colonnina_computer"] = computer_post(p)
    parts["P5_braccio_borraccia"] = cage_arm(p)
    return full, parts


def assembly(p, full, parts):
    """Posiziona i pezzi per anteprima."""
    a = {"vassoio": full}
    for sx, k in ((1, "P3_tubo_punta_dx"), (-1, "P3_tubo_punta_sx")):
        a[k] = parts[k].translate((sx * p["ext_cc"] / 2, p["tube_socket"], 0))
    a["computer"] = parts["P4_colonnina_computer"].translate((0, POST_Y[1], p["z_floor"] + p["t"]))
    org, _, _ = arm_frame(p)
    a["braccio"] = (parts["P5_braccio_borraccia"].rotate((0, 0, 0), (1, 0, 0), p["arm_angle"])
                    .translate(org))
    return a


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("P4b_*"):
        f.unlink()
    full, parts = build()
    for name, wp in parts.items():
        cq.exporters.export(wp, str(OUT / f"{name}.stl"), tolerance=0.05, angularTolerance=0.1)
        cq.exporters.export(wp, str(OUT / f"{name}.step"))
    asm = assembly(P, full, parts)
    comp = cq.Workplane().add([w.val() for w in asm.values()])
    cq.exporters.export(comp, str(OUT / "assieme.step"))
    cq.exporters.export(comp, str(OUT / "assieme.stl"), tolerance=0.1, angularTolerance=0.2)
    for name, wp in parts.items():
        bb = wp.val().BoundingBox()
        print(f"{name:28s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f}  vol {wp.val().Volume()/1000:6.1f} cm3")
