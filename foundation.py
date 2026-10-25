import numpy as np
import matplotlib.pyplot as plt

# ==================================================
# STANDARD PILE ARRANGEMENTS
# ==================================================

PILE_PATTERNS = {

    1: [
        (0.0, 0.0)
    ],

    2: [
        (-0.5, 0.0),
        (0.5, 0.0)
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

    # Central pile
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

    # Hexagon + centre pile
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

    # 3x3 grid with central pile
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


# ==================================================
# REQUIRED NUMBER OF PILES
# ==================================================

def required_piles(load_kn, pile_capacity_kn):

    n = 1

    while True:

        total_load = load_kn + n * 50.0

        load_per_pile = total_load / n

        if load_per_pile <= pile_capacity_kn:
            return n

        n += 1

        if n > 100:
            raise ValueError("Unable to determine pile count")


# ==================================================
# PILE REACTIONS
# N + Mx + My
# ==================================================

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

    iy = np.sum(x ** 2)
    ix = np.sum(y ** 2)

    if abs(ix) > 1e-9:
        reactions += mx * y / ix

    if abs(iy) > 1e-9:
        reactions += my * x / iy

    return reactions.tolist()


# ==================================================
# MAIN FOUNDATION DESIGN
# ==================================================

def design_foundation(
    row,
    pile_capacity,
    spacing_factor,
    pile_diameter
):

    service_load = (
        float(row["Dead Load"])
        + float(row["Live Load"])
        + float(row["Wind Load"])
    )

    mx = float(row["Moment X"])
    my = float(row["Moment Y"])

    n_piles = required_piles(
        service_load,
        pile_capacity
    )

    if n_piles > 9:
        raise ValueError(
            "Current version only supports up to 9 piles."
        )

    spacing = (
        pile_diameter / 1000.0
    ) * spacing_factor

    coordinates = []

    for x, y in PILE_PATTERNS[n_piles]:

        coordinates.append(
            (
                x * spacing,
                y * spacing
            )
        )

    total_load = service_load + n_piles * 50.0

    reactions = calculate_pile_reactions(
        coordinates,
        total_load,
        mx,
        my
    )

    max_reaction = max(reactions)
    min_reaction = min(reactions)

    return {

        "Column ID": row["Column ID"],

        "X": float(row["X"]),
        "Y": float(row["Y"]),

        "Load": total_load,

        "Piles": n_piles,

        "Coordinates": coordinates,

        "Pile Reactions": reactions,

        "Max Pile Load": max_reaction,

        "Min Pile Load": min_reaction
    }


# ==================================================
# INDIVIDUAL FOUNDATION PLOT
# ==================================================

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
        s=600,
        c="steelblue",
        edgecolors="black"
    )

    ax.scatter(
        0,
        0,
        s=250,
        c="red",
        marker="s",
        label="Column"
    )

    for i, (xp, yp) in enumerate(zip(x, y)):

        ax.text(
            xp,
            yp,
            str(i + 1),
            fontsize=9,
            ha="center",
            va="center"
        )

    ax.set_title(
        f"Foundation {foundation['Column ID']}"
    )

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")

    ax.grid(True)

    ax.set_aspect("equal")

    return fig


# ==================================================
# WHOLE BUILDING FOUNDATION PLAN
# ==================================================

def plot_building_plan(results):

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    for foundation in results:

        column_x = foundation["X"]
        column_y = foundation["Y"]

        ax.scatter(
            column_x,
            column_y,
            s=150,
            c="red",
            marker="s"
        )

        ax.text(
            column_x,
            column_y,
            foundation["Column ID"]
        )

        for px, py in foundation["Coordinates"]:

            ax.scatter(
                column_x + px,
                column_y + py,
                s=70,
                c="steelblue"
            )

    ax.set_title(
        "Building Foundation Layout"
    )

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")

    ax.grid(True)

    ax.set_aspect("equal")

    return fig
