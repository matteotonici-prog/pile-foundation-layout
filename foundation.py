import itertools

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Polygon

# ====================================================
# INPUT SHEET
# ====================================================
REQUIRED_COLUMNS = [
    "Column ID", "X", "Y", "Dead Load", "Live Load", "Wind Load"
]
OPTIONAL_COLUMNS = ["Moment X", "Moment Y"]  # filled with 0 if missing


def load_columns_sheet(df):
    """Validate / clean the 'Columns' sheet. Returns (clean_df, error_message)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return None, (
            "Missing column(s) in 'Columns' sheet: " + ", ".join(missing)
        )
    df = df.copy()
    for c in OPTIONAL_COLUMNS:
        if c not in df.columns:
            df[c] = 0.0
    num_cols = ["X", "Y", "Dead Load", "Live Load", "Wind Load"] + OPTIONAL_COLUMNS
    df[num_cols] = (
        df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    )
    df["Column ID"] = df["Column ID"].astype(str)
    return df, None


# ====================================================
# STANDARD PILE PATTERNS
# 1 UNIT = 1 PILE SPACING
# ====================================================
PILE_PATTERNS = {
    1: [(0, 0)],
    2: [(-0.5, 0), (0.5, 0)],
    3: [(-0.5, -0.289), (0.5, -0.289), (0.0, 0.577)],
    4: [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)],
    5: [(-0.5, -0.5), (0.5, -0.5), (0.0, 0.0), (-0.5, 0.5), (0.5, 0.5)],
    6: [(-1.0, -0.5), (0.0, -0.5), (1.0, -0.5),
        (-1.0, 0.5), (0.0, 0.5), (1.0, 0.5)],
    7: [(0.0, 0.0), (1.0, 0.0), (0.5, 0.866), (-0.5, 0.866),
        (-1.0, 0.0), (-0.5, -0.866), (0.5, -0.866)],
    8: [(-1.5, -0.5), (-0.5, -0.5), (0.5, -0.5), (1.5, -0.5),
        (-1.5, 0.5), (-0.5, 0.5), (0.5, 0.5), (1.5, 0.5)],
    9: [(-1.0, -1.0), (0.0, -1.0), (1.0, -1.0),
        (-1.0, 0.0), (0.0, 0.0), (1.0, 0.0),
        (-1.0, 1.0), (0.0, 1.0), (1.0, 1.0)],
}


# ====================================================
# REQUIRED PILES
# ====================================================
def required_piles(load, capacity):
    n = 1
    while True:
        total_load = load + n * 50.0
        if total_load / n <= capacity:
            return n
        n += 1


# ====================================================
# PILE REACTIONS
# ====================================================
def calculate_pile_reactions(coordinates, total_load, mx, my):
    x = np.array([c[0] for c in coordinates])
    y = np.array([c[1] for c in coordinates])
    n = len(coordinates)

    reactions = np.full(n, total_load / n)

    ix = np.sum(y ** 2)
    iy = np.sum(x ** 2)

    if ix > 0:
        reactions += mx * y / ix
    if iy > 0:
        reactions += my * x / iy

    return reactions.tolist()


# ====================================================
# PILE CAP GEOMETRY
# ====================================================
def cap_polygon(coords, edge):
    """
    Pile cap outline in plan, relative to the column. Counter-clockwise.

    3 piles   -> triangle with flat (cut-off) ends: the three sides sit `edge`
                 outside the lines between pile centres, and each corner is cut
                 flat, square to the line from the cap centre to the pile,
                 `edge` beyond the pile centre.
    otherwise -> rectangle around the piles, `edge` outside the outer centres.
    """
    pts = np.array(coords, dtype=float)

    if len(pts) != 3:
        x0, y0 = pts.min(axis=0) - edge
        x1, y1 = pts.max(axis=0) + edge
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    centre = pts.mean(axis=0)
    lines = []  # half-planes  n . p <= d
    for i in range(3):
        pi, pj = pts[i], pts[(i + 1) % 3]

        # side, parallel to the line between two pile centres
        e = pj - pi
        n = np.array([e[1], -e[0]]) / np.hypot(*e)
        if n @ (pi - centre) < 0:
            n = -n
        lines.append((n, n @ pi + edge))

        # flat end at pile i
        n = (pi - centre) / np.hypot(*(pi - centre))
        lines.append((n, n @ pi + edge))

    lines.sort(key=lambda l: np.arctan2(l[0][1], l[0][0]))

    verts = []
    for k in range(len(lines)):
        (n1, d1), (n2, d2) = lines[k], lines[(k + 1) % len(lines)]
        det = n1[0] * n2[1] - n1[1] * n2[0]
        verts.append((
            (d1 * n2[1] - d2 * n1[1]) / det,
            (n1[0] * d2 - n2[0] * d1) / det,
        ))
    return verts


def polygon_area(poly):
    """Shoelace formula."""
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def polygons_overlap(a, b, tol=1e-9):
    """Separating-axis test for two convex polygons (touching = no overlap)."""
    for poly in (a, b):
        for i in range(len(poly)):
            p1, p2 = poly[i], poly[(i + 1) % len(poly)]
            ax_, ay_ = p1[1] - p2[1], p2[0] - p1[0]
            norm = np.hypot(ax_, ay_)
            if norm == 0:
                continue
            ax_, ay_ = ax_ / norm, ay_ / norm
            pa = [ax_ * x + ay_ * y for x, y in a]
            pb = [ax_ * x + ay_ * y for x, y in b]
            if max(pa) <= min(pb) + tol or max(pb) <= min(pa) + tol:
                return False
    return True


def overlapping_caps(results, tol=1e-9):
    """Pairs of columns whose pile caps overlap in plan."""
    pairs = []
    for a, b in itertools.combinations(results, 2):
        ax0, ay0, ax1, ay1 = a["Bbox"]
        bx0, by0, bx1, by1 = b["Bbox"]
        # quick reject on bounding boxes, then exact polygon test
        if (
            min(ax1, bx1) - max(ax0, bx0) <= tol
            or min(ay1, by1) - max(ay0, by0) <= tol
        ):
            continue
        if polygons_overlap(a["Cap"], b["Cap"], tol):
            pairs.append((a["Column ID"], b["Column ID"]))
    return pairs


# ====================================================
# FOUNDATION DESIGN
# ====================================================
def design_foundation(
    row,
    pile_capacity,
    spacing_factor,
    pile_diameter,
    load_increase_percent=0,
    edge_factor=1.0,
):
    """
    edge_factor: pile centre to cap edge, as a multiple of the pile diameter.
    Raises ValueError if more than 9 piles are needed.
    """
    service_load = (
        float(row["Dead Load"])
        + float(row["Live Load"])
        + float(row["Wind Load"])
    )
    service_load *= 1.0 + load_increase_percent / 100.0

    mx = float(row["Moment X"])
    my = float(row["Moment Y"])

    n = required_piles(service_load, pile_capacity)

    if n > 9:
        raise ValueError("More than 9 piles required")

    dia_m = pile_diameter / 1000.0
    pile_spacing = dia_m * spacing_factor

    coordinates = [
        (x * pile_spacing, y * pile_spacing) for x, y in PILE_PATTERNS[n]
    ]

    total_load = service_load + n * 50.0
    reactions = calculate_pile_reactions(coordinates, total_load, mx, my)

    x0, y0 = float(row["X"]), float(row["Y"])
    cap_local = cap_polygon(coordinates, edge_factor * dia_m)
    cap = [(x0 + x, y0 + y) for x, y in cap_local]
    xs = [p[0] for p in cap]
    ys = [p[1] for p in cap]

    return {
        "Column ID": row["Column ID"],
        "X": x0,
        "Y": y0,
        "Load": total_load,
        "Piles": n,
        "Pile Diameter": dia_m,
        "Coordinates": coordinates,
        "Max Pile Load": max(reactions),
        "Min Pile Load": min(reactions),
        "Pile Reactions": reactions,
        "Cap Local": cap_local,
        "Cap": cap,
        "CapArea": polygon_area(cap),
        "Bbox": (min(xs), min(ys), max(xs), max(ys)),
    }


# ====================================================
# FOUNDATION PLOT
# ====================================================
def plot_foundation(foundation):
    fig, ax = plt.subplots(figsize=(6, 6))

    d = foundation["Pile Diameter"]

    ax.add_patch(
        Polygon(
            foundation["Cap Local"], closed=True,
            facecolor="whitesmoke", edgecolor="grey", linewidth=1.5
        )
    )

    for px, py in foundation["Coordinates"]:
        ax.add_patch(
            Circle((px, py), d / 2, facecolor="steelblue", edgecolor="black")
        )

    ax.plot(0, 0, marker="s", color="red", markersize=10)

    xs = [p[0] for p in foundation["Cap Local"]]
    ys = [p[1] for p in foundation["Cap Local"]]
    m = 0.1 * max(max(xs) - min(xs), max(ys) - min(ys), d)
    ax.set_xlim(min(xs) - m, max(xs) + m)
    ax.set_ylim(min(ys) - m, max(ys) + m)

    ax.grid(True)
    ax.set_aspect("equal")
    ax.set_title(foundation["Column ID"])

    return fig


# ====================================================
# BUILDING PLAN
# ====================================================
def plot_building_plan(results):
    overlaps = overlapping_caps(results)
    in_overlap = {c for pair in overlaps for c in pair}

    fig, ax = plt.subplots(figsize=(10, 8))

    for f in results:
        clash = f["Column ID"] in in_overlap
        ax.add_patch(
            Polygon(
                f["Cap"], closed=True, fill=False,
                edgecolor="red" if clash else "grey",
                linewidth=1.8 if clash else 1.0,
            )
        )

        for px, py in f["Coordinates"]:
            ax.add_patch(
                Circle(
                    (f["X"] + px, f["Y"] + py), f["Pile Diameter"] / 2,
                    facecolor="steelblue", edgecolor="black", linewidth=0.5
                )
            )

        ax.plot(f["X"], f["Y"], marker="s", color="red", markersize=4)
        ax.text(
            f["X"], f["Bbox"][3], f["Column ID"],
            ha="center", va="bottom", fontsize=8
        )

    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_title("Foundation Layout Plan (red cap outline = overlaps a neighbour)")

    return fig
