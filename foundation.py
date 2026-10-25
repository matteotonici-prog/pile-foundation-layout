import numpy as np
import matplotlib.pyplot as plt

# ====================================================
# STANDARD PILE PATTERNS
# 1 UNIT = 1 PILE SPACING
# ====================================================

PILE_PATTERNS = {

    1: [
        (0, 0)
    ],

    2: [
        (-0.5, 0),
        (0.5, 0)
    ],

    3: [
        (-0.5, -0.289),
        (0.5, -0.289),
        (0.0, 0.577)
    ],

    4: [
        (-0.5, -0.5),
        (0.5, -0.5),
        (-0.5, 0.5),
        (0.5, 0.5)
    ],

    5: [
        (-0.5, -0.5),
        (0.5, -0.5),
        (0.0, 0.0),
        (-0.5, 0.5),
        (0.5, 0.5)
    ],

    6: [
        (-1.0, -0.5),
        (0.0, -0.5),
        (1.0, -0.5),
        (-1.0, 0.5),
        (0.0, 0.5),
        (1.0, 0.5)
    ],

    7: [
        (0.0, 0.0),
        (1.0, 0.0),
        (0.5, 0.866),
        (-0.5, 0.866),
        (-1.0, 0.0),
        (-0.5, -0.866),
        (0.5, -0.866)
    ],

    8: [
        (-1.5, -0.5),
        (-0.5, -0.5),
        (0.5, -0.5),
        (1.5, -0.5),
        (-1.5, 0.5),
        (-0.5, 0.5),
        (0.5, 0.5),
        (1.5, 0.5)
    ],

    9: [
        (-1.0, -1.0),
        (0.0, -1.0),
        (1.0, -1.0),
        (-1.0, 0.0),
        (0.0, 0.0),
        (1.0, 0.0),
        (-1.0, 1.0),
        (0.0, 1.0),
        (1.0, 1.0)
    ]
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

def calculate_pile_reactions(
    coordinates,
    total_load,
    mx,
    my
):

    x = np.array([c[0] for c in coordinates])
    y = np.array([c[1] for c in coordinates])

    n = len(coordinates)

    reactions = np.full(
        n,
        total_load / n
    )

    ix = np.sum(y ** 2)
    iy = np.sum(x ** 2)

    if ix > 0:
        reactions += mx * y / ix

    if iy > 0:
        reactions += my * x / iy

    return reactions.tolist()

# ====================================================
# FOUNDATION DESIGN
# ====================================================

def design_foundation(
    row,
    pile_capacity,
    spacing_factor,
    pile_diameter,
    load_increase_percent=0
):

    service_load = (
        float(row["Dead Load"])
        + float(row["Live Load"])
        + float(row["Wind Load"])
    )

    service_load *= (
        1.0 + load_increase_percent / 100.0
    )

    mx = float(row["Moment X"])
    my = float(row["Moment Y"])

    n = required_piles(
        service_load,
        pile_capacity
    )

    if n > 9:
        raise ValueError(
            "More than 9 piles required"
        )

    pile_spacing = (
        pile_diameter / 1000.0
    ) * spacing_factor

    coordinates = []

    for x, y in PILE_PATTERNS[n]:

        coordinates.append(
            (
                x * pile_spacing,
                y * pile_spacing
            )
        )

    total_load = service_load + n * 50.0

    reactions = calculate_pile_reactions(
        coordinates,
        total_load,
        mx,
        my
    )

    return {

        "Column ID": row["Column ID"],

        "X": float(row["X"]),
        "Y": float(row["Y"]),

        "Load": total_load,

        "Piles": n,

        "Coordinates": coordinates,

        "Max Pile Load": max(reactions),

        "Min Pile Load": min(reactions),

        "Pile Reactions": reactions
    }

# ====================================================
# FOUNDATION PLOT
# ====================================================

def plot_foundation(foundation):

    fig, ax = plt.subplots(
        figsize=(6, 6)
    )

    x = [
        p[0]
        for p in foundation["Coordinates"]
    ]

    y = [
        p[1]
        for p in foundation["Coordinates"]
    ]

    ax.scatter(
        x,
        y,
        s=500,
        color="steelblue"
    )

    ax.scatter(
        0,
        0,
        s=250,
        color="red",
        marker="s"
    )

    ax.grid(True)

    ax.set_aspect("equal")

    ax.set_title(
        foundation["Column ID"]
    )

    return fig

# ======================================
# BUILDING PLAN
# ====================================================

def plot_building_plan(results):

    fig, ax = plt.subplots(
        figsize=(10, 8)
    )

    for f in results:

        x0 = f["X"]
        y0 = f["Y"]

        ax.scatter(
            x0,
            y0,
            s=80,
            color="red",
            marker="s"
        )

        ax.text(
            x0,
            y0,
            f["Column ID"]
        )

        for px, py in f["Coordinates"]:

            ax.scatter(
                x0 + px,
                y0 + py,
                s=50,
                color="steelblue"
            )

    ax.set_aspect("equal")

    ax.grid(True)

    ax.set_title(
        "Foundation Layout Plan"
    )

    return fig
