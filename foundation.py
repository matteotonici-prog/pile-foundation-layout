import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------
# PILE PATTERNS
# --------------------------------------------------

PILE_PATTERNS = {

    1: [
        (0, 0)
    ],

    2: [
        (-1, 0),
        (1, 0)
    ],

    3: [
        (-1, -0.577),
        (1, -0.577),
        (0, 1.155)
    ],

    4: [
        (-1, -1),
        (1, -1),
        (-1, 1),
        (1, 1)
    ],

    # central pile
    5: [
        (-1, -1),
        (1, -1),
        (0, 0),
        (-1, 1),
        (1, 1)
    ],

    6: [
        (-1, -0.5),
        (0, -0.5),
        (1, -0.5),
        (-1, 0.5),
        (0, 0.5),
        (1, 0.5)
    ],

    # hexagon + centre pile
    7: [
        (0, 0),
        (1, 0),
        (0.5, 0.866),
        (-0.5, 0.866),
        (-1, 0),
        (-0.5, -0.866),
        (0.5, -0.866)
    ],

    8: [
        (-1.5, -1),
        (-0.5, -1),
        (0.5, -1),
        (1.5, -1),
        (-1.5, 1),
        (-0.5, 1),
        (0.5, 1),
        (1.5, 1)
    ],

    # 3x3 with centre pile
    9: [
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (0, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1)
    ]
}

# --------------------------------------------------
# NUMBER OF PILES REQUIRED
# --------------------------------------------------

def required_piles(load, pile_capacity):

    n = 1

    while True:

        total_load = load + n * 50

        reaction = total_load / n

        if reaction <= pile_capacity:
            return n

        n += 1


# --------------------------------------------------
# PILE REACTIONS
# --------------------------------------------------

def pile_reactions(coords, total_load, mx, my):

    n = len(coords)

    x = np.array([c[0] for c in coords])
    y = np.array([c[1] for c in coords])

    ix = np.sum(y**2)
    iy = np.sum(x**2)

    reactions = []

    for xi, yi in zip(x, y):

        r = total_load / n

        if ix > 0:
            r += mx * yi / ix

        if iy > 0:
            r += my * xi / iy

        reactions.append(r)

    return reactions


# --------------------------------------------------
# FOUNDATION DESIGN
# --------------------------------------------------

def design_foundation(
    row,
    pile_capacity,
    spacing_factor,
    pile_diameter
):

    load = (
        row["Dead Load"] +
        row["Live Load"] +
        row["Wind Load"]
    )

    mx = row["Moment X"]
    my = row["Moment Y"]

    n = required_piles(
        load,
        pile_capacity
    )

    if n > 9:
        raise ValueError(
            "Current version supports up to 9 piles"
        )

    spacing = (
        pile_diameter / 1000
    ) * spacing_factor

    coords = []

    for x, y in PILE_PATTERNS[n]:

        coords.append(
            (
                x * spacing,
                y * spacing
            )
        )

    total_load = load + n * 50

    reactions = pile_reactions(
        coords,
        total_load,
        mx,
        my
    )

    return {

        "Column ID": row["Column ID"],

        "X": row["X"],

        "Y": row["Y"],

        "Load": total_load,

        "Piles": n,

        "Coordinates": coords,

        "Max Pile Load": max(reactions),

        "Min Pile Load": min(reactions)
    }


# --------------------------------------------------
# INDIVIDUAL FOUNDATION PLOT
# --------------------------------------------------

def plot_foundation(foundation):

    fig, ax = plt.subplots(
        figsize=(6, 6)
    )

    x = [p[0] for p in foundation["Coordinates"]]
    y = [p[1] for p in foundation["Coordinates"]]

    ax.scatter(
        x,
        y,
        s=500,
        color="steelblue"
    )

    ax.scatter(
        0,
        0,
        s=300,
        marker="s",
        color="red"
    )

    ax.set_title(
        f"Column {foundation['Column ID']}"
    )

    ax.set_aspect("equal")

    ax.grid(True)

    return fig


# --------------------------------------------------
# WHOLE BUILDING PLAN
# --------------------------------------------------

def plot_building_plan(results):

    fig, ax = plt.subplots(
        figsize=(10, 8)
    )

    for foundation in results:

        x0 = foundation["X"]
        y0 = foundation["Y"]

        # column

        ax.scatter(
            x0,
            y0,
            s=120,
            marker="s",
            color="red"
        )

        ax.text(
            x0,
            y0,
            foundation["Column ID"]
        )

        # piles

        for px, py in foundation["Coordinates"]:

            ax.scatter(
                x0 + px,
                y0 + py,
                s=80,
                color="steelblue"
            )

    ax.set_title(
        "Foundation Layout Plan"
  t_aspect("equal")

    ax.grid(True)

    return fig
