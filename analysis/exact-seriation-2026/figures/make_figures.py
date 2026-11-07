"""Figures for the exact seriation paper.

Figure numbers follow the paper: Fig. 1 = minimum sample size, Fig. 2 = minmax graphs,
Fig. 3 = largest solutions. Inside this script the functions are fig1 (minmax graphs),
fig2 (largest solutions) and fig3 (minimum sample size).

Fig 1  Minmax graphs for the PFG table at site coordinates: IDSS v2.0 and the corrected IDSS
       under three configurations (published settings: threshold 0.30, 95% intervals).
Fig 2  Centered-bar plots of one largest solution from each corrected configuration with
       percentile intervals.
Fig 3  Effect of a minimum sample size on the largest seriable subset and on the number of
       valid orderings (exact search, 95% bootstrap criterion; the runs behind Table 2).
"""
import csv
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PFG = os.path.join(REPO, "testdata", "pfg", "pfg-cpl.txt")
PFGXY = os.path.join(REPO, "testdata", "pfg", "pfgXY.txt")
OUTPUTS = os.path.join(HERE, "..", "idss_comparison", "outputs")
RESULTS = os.path.join(HERE, "..", "results")
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.6, "savefig.dpi": 300,
})


def read_counts(path):
    names, rows, header = [], [], None
    with open(path) as fh:
        r = csv.reader(fh, delimiter="\t" if path.endswith(".txt") else ",")
        header = next(r)[1:]
        for row in r:
            if row and row[0].strip():
                names.append(row[0].strip())
                rows.append([float(v) for v in row[1:]])
    return names, np.array(rows), header


# ---------------------------------------------------------------- Fig 1
def fig1():
    xy = {}
    with open(PFGXY) as fh:
        next(fh)
        for line in fh:
            p = line.split()
            if len(p) >= 3:
                xy[p[0]] = (float(p[2]) / 1000.0, float(p[1]) / 1000.0)  # easting, northing in km
    G = json.load(open(os.path.join(HERE, "minmax_edges.json")))
    names, _, _ = read_counts(PFG)
    x0 = min(xy[n][0] for n in names)
    y0 = min(xy[n][1] for n in names)
    pos = {n: (xy[n][0] - x0, xy[n][1] - y0) for n in names}
    ref = {tuple(e) for e in G["v20"]["edges"]}
    panels = [("v20", "(a) IDSS v2.0 (tagged release),\n     seed 1"),
              ("nb_leg", "(b) Corrected, original interval,\n     neighbour rule"),
              ("nb_pct", "(c) Corrected, percentile interval,\n     neighbour rule"),
              ("tr_pct", "(d) Corrected, percentile interval,\n     every-triple rule")]
    # label placement (offset in points, horizontal alignment) chosen by hand to avoid overlaps
    off = {"10-P-1": (-5, -3, "right"), "11-O-10": (5, 2, "left"), "11-N-9": (5, -3, "left"),
           "11-N-4": (-4, 4, "right"), "11-N-1": (5, -3, "left"), "Holden_Lake": (5, -3, "left"),
           "12-N-3": (-3, -10, "left"), "12-O-5": (5, 3, "left"), "13-P-1": (5, 3, "left"),
           "13-N-21": (-3, 5, "left"), "13-N-15": (-5, -9, "right"), "13-O-5": (3, 4, "left"),
           "13-O-7": (5, -9, "left"), "13-P-8": (-8, -10, "left"), "13-P-10": (5, -3, "left"),
           "13-N-5": (-5, -1, "right"), "13-N-4": (5, -4, "left"), "13-O-11": (5, 2, "left"),
           "13-O-10": (5, -6, "left"), "13-N-16": (-3, -10, "left")}
    fig, axes = plt.subplots(2, 2, figsize=(6.6, 8.2))
    for ax, (tag, title) in zip(axes.ravel(), panels):
        edges = {tuple(e) for e in G[tag]["edges"]}
        used = {n for e in edges for n in e}
        if tag != "v20":
            for a, b in sorted(ref - edges):
                ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color=INK2, lw=0.9,
                        ls=(0, (2, 2)), zorder=1)
        for a, b in sorted(edges):
            col = BLUE if (a, b) in ref else ORANGE
            ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color=col, lw=2.0,
                    solid_capstyle="round", zorder=2)
        for n in names:
            filled = n in used
            ax.scatter(*pos[n], s=26, zorder=3, facecolor=INK if filled else "white",
                       edgecolor=INK, linewidth=0.9)
            dx, dy, ha = off[n]
            ax.annotate(n.replace("_", " "), pos[n], xytext=(dx, dy), textcoords="offset points",
                        ha=ha, fontsize=6.2, color=INK if filled else INK2)
        ax.set_title(title, fontsize=8, loc="left", color=INK)
        ax.set_aspect("equal")
        ax.set_xlim(-6, 62)
        ax.set_ylim(-6, 99)
        ax.tick_params(labelsize=6.5)
        ax.grid(color=GRID, lw=0.4)
        ax.set_axisbelow(True)
        ax.set_xlabel("Easting (km, relative)", fontsize=7)
        ax.set_ylabel("Northing (km, relative)", fontsize=7)
    handles = [Line2D([], [], color=BLUE, lw=2, label="Edge also in the v2.0 graph"),
               Line2D([], [], color=ORANGE, lw=2, label="Edge not in the v2.0 graph"),
               Line2D([], [], color=INK2, lw=0.9, ls=(0, (2, 2)), label="v2.0 edge absent from this graph"),
               Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor=INK,
                      label="Assemblage in no solution")]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=7)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(HERE, "Fig2_minmax_maps.png"))
    plt.close(fig)


# ---------------------------------------------------------------- Fig 2
def battleship(ax, order, names, f, lo, hi, types, title):
    """Centered bars, one column per type. Within each column the bar width is scaled to the
    largest upper bound of that type in the solution, so rare types remain visible; the black
    whisker on each side spans the bootstrap interval."""
    idx = [names.index(a) for a in order]
    keep = [t for t in range(len(types)) if f[idx, t].max() > 0]
    half = 0.44  # half of the maximum bar width, in column units
    for col, t in enumerate(keep):
        scale = max(hi[a][t] for a in order)
        for row, a in enumerate(order):
            i = names.index(a)
            y = len(order) - 1 - row
            w = f[i, t] / scale * half
            ax.barh(y, 2 * w, left=col - w, height=0.7, color=BLUE, edgecolor="white", linewidth=0.5)
            l, h = lo[a][t] / scale * half, hi[a][t] / scale * half
            for sgn in (-1, 1):
                ax.plot([col + sgn * l, col + sgn * h], [y, y], color=INK, lw=0.9, solid_capstyle="butt")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([a.replace("_", " ") for a in reversed(order)], fontsize=6.5)
    ax.set_xticks(range(len(keep)))
    ax.set_xticklabels([types[t].replace("_", " ") for t in keep], rotation=50, ha="right", fontsize=6.5)
    ax.set_xlim(-0.6, len(keep) - 0.4)
    ax.set_ylim(-0.6, len(order) + 0.2)
    for c in range(len(keep)):
        ax.axvline(c, color=GRID, lw=0.4, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title(title, fontsize=8, loc="left", pad=10)


def fig2():
    names, counts, types = read_counts(PFG)
    f = counts / counts.sum(axis=1, keepdims=True)
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.6), gridspec_kw={"width_ratios": [1, 1]})
    for ax, (fn, title) in zip(axes, [
            ("c15_percentile_neighbor.json", "(a) Neighbour rule: one of 3 largest orderings (13)"),
            ("c15_percentile_triple.json", "(b) Every-triple rule: one of 132 largest orderings (9)")]):
        d = json.load(open(os.path.join(OUTPUTS, fn)))
        order = sorted(d["all_max_orderings"])[0]
        battleship(ax, order, names, f, d["lowerCI"], d["upperCI"], types, title)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "Fig3_largest_solutions.png"))
    plt.close(fig)


# ---------------------------------------------------------------- Fig 3
def fig3():
    rows = json.load(open(os.path.join(RESULTS, "table2_runs.json")))
    tables = [("cpl-pfg", "cpl-pfg (20)", BLUE, "o"),
              ("pfg-cpl-mainfort", "pfg-cpl-mainfort (55)", ORANGE, "s"),
              ("mainfort-data-collapsed", "mainfort-data-collapsed (54)", AQUA, "D")]
    levels = [0, 100, 200]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    for k, (t, label, col, mk) in enumerate(tables):
        xs = np.arange(3) + (k - 1) * 0.12
        for ax, key in zip(axes, ["largest", "orderings"]):
            med, lo, hi = [], [], []
            for m in levels:
                v = [r[key] for r in rows if r["table"] == t and r["minsample"] == m]
                med.append(np.median(v)); lo.append(min(v)); hi.append(max(v))
            med, lo, hi = map(np.array, (med, lo, hi))
            ax.errorbar(xs, med, yerr=[med - lo, hi - med], color=col, marker=mk, ms=5, lw=2,
                        capsize=0, elinewidth=1.2, label=label)
            if key == "largest":
                ax.annotate(label, (xs[-1], med[-1]), xytext=(7, 0), textcoords="offset points",
                            ha="left", va="center", fontsize=6.5, color=INK)
    axes[0].set_ylabel("Largest seriable subset (assemblages)")
    axes[1].set_ylabel("Valid orderings of largest subsets")
    axes[1].set_yscale("log")
    for ax, title in zip(axes, ["(a) Largest subset size", "(b) Number of valid orderings"]):
        ax.set_xticks(range(3))
        ax.set_xticklabels(["None", "100", "200"])
        ax.set_xlabel("Minimum sample size (sherds)")
        ax.set_xlim(-0.4, 3.4 if ax is axes[0] else 2.4)
        ax.grid(axis="y", color=GRID, lw=0.4)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_title(title, fontsize=8, loc="left")
    axes[1].legend(frameon=False, fontsize=6.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "Fig1_minimum_sample.png"))
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    print("written:", [f for f in sorted(os.listdir(HERE)) if f.endswith(".png")])
