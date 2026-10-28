"""Contorni reali dai frame del video (viewer/ref/*.jpg) -> viewer/draw/trace_<vista>.json.

Segmenta il pezzo (grigio scuro, poco saturo) da sfondo e mani, prende il contorno più grande
e lo porta in mm con la stessa trasformazione a due punti usata dal visualizzatore (REFS).
Coordinate come drawings.py: lato x=Y, y=-Z; alto/sotto x=X, y=Y.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).parent
REF = ROOT / "viewer" / "ref"
OUT = ROOT / "viewer" / "draw"

# punti foto (px) -> disegno (mm): punta e coda del vassoio. Tenere allineato con REFS in viewer/index.html
ANCHORS = {
    "lato": ((330, 345), (0, 0), (985, 343), (360, 0)),
    "alto": ((407, 270), (0, 0), (397, 890), (0, 360)),
    "sotto": ((459, 295), (0, 0), (409, 945), (0, 360)),
}


def similarity(p1, q1, p2, q2):
    dp = np.subtract(p2, p1); dq = np.subtract(q2, q1)
    s = np.hypot(*dq) / np.hypot(*dp)
    th = math.atan2(dq[1], dq[0]) - math.atan2(dp[1], dp[0])
    R = s * np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    return lambda pts: (np.asarray(pts, float) - p1) @ R.T + q1


# soglie (luminosità max, saturazione max) per vista: sotto ha zone del pezzo più chiare
THRESH = {"lato": (175, 70), "alto": (175, 70), "sotto": (222, 28)}


def mask_of(img, view):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    vmax, smax = THRESH[view]
    m = ((hsv[..., 2] < vmax) & (hsv[..., 1] < smax)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    return m


def trace(view, debug_dir=None):
    img = cv2.imread(str(REF / f"{view}.jpg"))
    m = mask_of(img, view)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 1.5, True)[:, 0, :]
    f = similarity(*ANCHORS[view])
    pts = f(c)
    if debug_dir:
        dbg = img.copy()
        cv2.drawContours(dbg, [c.reshape(-1, 1, 2)], -1, (0, 0, 255), 3)
        cv2.imwrite(str(Path(debug_dir) / f"trace_{view}.jpg"), dbg)
    return pts


def main(debug_dir=None):
    for v in ANCHORS:
        pts = trace(v, debug_dir)
        (OUT / f"trace_{v}.json").write_text(json.dumps({"pts": np.round(pts, 2).tolist()}))
        print(v, len(pts), "punti", np.round(pts.min(0), 1), np.round(pts.max(0), 1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
