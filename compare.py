"""Scarto tra contorno del modello (vassoio) e contorno dalle foto, a stazioni lungo Y.

alto/sotto: semi-larghezze sinistra/destra; lato: quota massima (bordo pareti) e minima (chiglia).
"""
import json
from pathlib import Path

import numpy as np
import trimesh

import cadquery as cq
import cockpit as c

DRAW = Path(__file__).with_name("viewer") / "draw"
STATIONS = [20, 60, 100, 140, 180, 220, 260, 300, 340]


def cut_poly(pts, along, val):
    """Intersezioni del poligono chiuso con la retta coord[along] == val -> valori dell'altra coordinata."""
    other = 1 - along
    out = []
    P = np.vstack([pts, pts[:1]])
    for a, b in zip(P[:-1], P[1:]):
        if (a[along] - val) * (b[along] - val) < 0:
            t = (val - a[along]) / (b[along] - a[along])
            out.append(a[other] + t * (b[other] - a[other]))
    return out


def model_mesh(p):
    full, _ = c.build(p)
    tmp = DRAW / "_tray.stl"
    cq.exporters.export(full, str(tmp), tolerance=0.3, angularTolerance=0.3)
    m = trimesh.load(tmp)
    tmp.unlink()
    return m


def model_section(m, y):
    s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    v = s.vertices
    return v[:, 0].min(), v[:, 0].max(), v[:, 2].min(), v[:, 2].max()


def main(p=c.P):
    m = model_mesh(p)
    tr = {v: np.array(json.loads((DRAW / f"trace_{v}.json").read_text())["pts"]) for v in ("lato", "alto", "sotto")}
    print(f"{'Y':>4} | {'alto: sx foto/mod':>18} {'dx foto/mod':>14} | {'sotto: sx':>11} {'dx':>11} | {'lato: top foto/mod':>19} {'fondo foto/mod':>15}")
    rows = []
    for y in STATIONS:
        x0, x1, z0, z1 = model_section(m, y)
        a = cut_poly(tr["alto"], 1, y); b = cut_poly(tr["sotto"], 1, y); l = cut_poly(tr["lato"], 0, y)
        ta = (min(a), max(a)) if len(a) >= 2 else (np.nan, np.nan)
        tb = (min(b), max(b)) if len(b) >= 2 else (np.nan, np.nan)
        tl = (-min(l), -max(l)) if len(l) >= 2 else (np.nan, np.nan)  # lato: y disegno = -Z
        rows.append(dict(y=y, alto=ta, sotto=tb, lato=tl, mod=(x0, x1, z0, z1)))
        print(f"{y:4d} | {ta[0]:7.1f}/{x0:7.1f}  {ta[1]:6.1f}/{x1:6.1f} | {tb[0]:5.0f}/{x0:4.0f} {tb[1]:5.0f}/{x1:4.0f} | "
              f"{tl[0]:8.1f}/{z1:7.1f}   {tl[1]:6.1f}/{z0:6.1f}")
    return rows


if __name__ == "__main__":
    main()
