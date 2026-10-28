"""Disegni tecnici (lato / alto / sotto) con linee nascoste, per il visualizzatore.

Proiezione HLR di OpenCASCADE con assi controllati; scrive viewer/draw/<vista>.json con
viewBox in mm e i percorsi visibili/nascosti già nelle coordinate del disegno (y verso il basso).

Assi disegno:
  lato  -> x = Y (punta a sinistra), y = -Z (alto in alto)
  alto  -> x = X, y = Y (punta in alto)
  sotto -> x = X, y = Y (punta in alto, vista da sotto)
"""
import json
from pathlib import Path

import cadquery as cq
from OCP.BRepLib import BRepLib
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape

import cockpit as c

OUT = Path(__file__).with_name("viewer") / "draw"

# vista: (direzione verso l'osservatore, asse x schermo, mappa (u,v) schermo -> (x,y) disegno)
VIEWS = {
    "lato": ((1, 0, 0), (0, 1, 0), lambda u, v: (u, -v)),
    "alto": ((0, 0, 1), (1, 0, 0), lambda u, v: (u, v)),
    "sotto": ((0, 0, -1), (1, 0, 0), lambda u, v: (u, -v)),
}


def edges_to_d(shapes, fmap):
    out, pts_all = [], []
    for s in shapes:
        for e in cq.Shape(s).Edges():
            cur = e._geomAdaptor()
            pts = GCPnts_QuasiUniformDeflection(cur, 0.05, cur.FirstParameter(), cur.LastParameter())
            if not pts.IsDone() or pts.NbPoints() < 2:
                continue
            xy = [fmap(pts.Value(i + 1).X(), pts.Value(i + 1).Y()) for i in range(pts.NbPoints())]
            pts_all += xy
            out.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in xy))
    return " ".join(out), pts_all


def project(shape, n, xdir, fmap):
    hlr = HLRBRep_Algo()
    hlr.Add(shape.wrapped)
    hlr.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(), gp_Dir(*n), gp_Dir(*xdir))))
    hlr.Update()
    hlr.Hide()
    h = HLRBRep_HLRToShape(hlr)
    vis = [x for x in (h.VCompound(), h.Rg1LineVCompound(), h.OutLineVCompound()) if not x.IsNull()]
    hid = [x for x in (h.HCompound(), h.OutLineHCompound()) if not x.IsNull()]
    for el in vis + hid:
        BRepLib.BuildCurves3d_s(el, 1e-4)
    dv, pv = edges_to_d(vis, fmap)
    dh, ph = edges_to_d(hid, fmap)
    xs = [x for x, _ in pv + ph]
    ys = [y for _, y in pv + ph]
    return dict(vis=dv, hid=dh, bbox=[min(xs), min(ys), max(xs), max(ys)])


def main(p=c.P):
    OUT.mkdir(parents=True, exist_ok=True)
    full, parts = c.build(p)
    asm = c.assembly(p, full, parts)
    comp = cq.Compound.makeCompound([w.val() for w in asm.values()])
    for name, (n, xdir, fmap) in VIEWS.items():
        d = project(comp, n, xdir, fmap)
        (OUT / f"{name}.json").write_text(json.dumps(d))
        b = d["bbox"]
        print(f"{name:6s} x {b[0]:7.1f}..{b[2]:7.1f}  y {b[1]:7.1f}..{b[3]:7.1f}  "
              f"{len(d['vis'])//1000}k/{len(d['hid'])//1000}k car.")


if __name__ == "__main__":
    main()
