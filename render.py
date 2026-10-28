"""Anteprime PNG dell'assieme (matplotlib, nessuna dipendenza GPU)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = Path(__file__).with_name("out")
VIEWS = {
    "iso": (28, -125),
    "top": (90, -90),
    "side": (0, 180),
    "front": (0, -90),
    "under": (-35, -120),
}


def render(stl, png, elev, azim, title):
    m = trimesh.load(stl)
    if len(m.faces) > 120000:
        m = m.simplify_quadric_decimation(face_count=120000)
    tris = m.vertices[m.faces]
    light = np.array([0.4, -0.5, 0.8]); light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(m.face_normals @ light, 0, 1)
    colors = np.column_stack([shade * 0.32, shade * 0.34, shade * 0.38, np.ones_like(shade)])
    fig = plt.figure(figsize=(10, 8), dpi=110)
    ax = fig.add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=colors, edgecolors="none"))
    lo, hi = m.bounds
    c, r = (lo + hi) / 2, (hi - lo).max() / 2 * 0.62
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(png)
    plt.close(fig)


if __name__ == "__main__":
    stl = OUT / (sys.argv[1] if len(sys.argv) > 1 else "assieme.stl")
    for name, (e, a) in VIEWS.items():
        render(stl, OUT / f"{stl.stem}_{name}.png", e, a, f"{stl.stem} – {name}")
