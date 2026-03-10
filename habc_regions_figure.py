"""Standalone 2D schematic for HABC physical and pad regions.

This helper is meant to be pasted into or imported from a notebook without
touching the existing notebook file. It highlights:

- the physical region in the parent mesh;
- the left and right absorbing pads;
- the bottom absorbing pad, labeled ``Omega_B`` to match the notebook
  notation;
- the top boundary, labeled as a free surface.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def plot_habc_regions_2d(
    domain_length: float = 1.5,
    pad_width: float = 0.2,
    third_pad_label: str = r"$\Omega_B$" + "\nbottom pad",
) -> tuple[plt.Figure, plt.Axes]:
    """Draw a 2D schematic of the physical domain and HABC pad regions."""
    if pad_width <= 0.0:
        raise ValueError("pad_width must be positive")
    if 2.0 * pad_width >= domain_length:
        raise ValueError("pad_width must be smaller than domain_length / 2")

    L = float(domain_length)
    delta = float(pad_width)

    fig, ax = plt.subplots(figsize=(7.2, 6.8))

    colors = {
        "physical": "#f4f4f4",
        "left": "#7ec8e3",
        "right": "#f7a35c",
        "bottom": "#90be6d",
    }

    domain = Rectangle(
        (0.0, 0.0),
        L,
        L,
        facecolor="white",
        edgecolor="black",
        linewidth=2.2,
    )
    left_pad = Rectangle(
        (0.0, 0.0),
        delta,
        L,
        facecolor=colors["left"],
        edgecolor="none",
        alpha=0.9,
    )
    right_pad = Rectangle(
        (L - delta, 0.0),
        delta,
        L,
        facecolor=colors["right"],
        edgecolor="none",
        alpha=0.9,
    )
    bottom_pad = Rectangle(
        (delta, 0.0),
        L - 2.0 * delta,
        delta,
        facecolor=colors["bottom"],
        edgecolor="none",
        alpha=0.9,
    )
    physical_region = Rectangle(
        (delta, delta),
        L - 2.0 * delta,
        L - delta,
        facecolor=colors["physical"],
        edgecolor="none",
        alpha=1.0,
    )

    for patch in (domain, physical_region, left_pad, right_pad, bottom_pad):
        ax.add_patch(patch)

    ax.plot([delta, delta], [0.0, L], "--", color="0.35", linewidth=1.4)
    ax.plot([L - delta, L - delta], [0.0, L], "--", color="0.35", linewidth=1.4)
    ax.plot([delta, L - delta], [delta, delta], "--", color="0.35", linewidth=1.4)

    ax.text(
        0.5 * delta,
        0.5 * L,
        r"$\Omega_L$" + "\nleft pad",
        ha="center",
        va="center",
        fontsize=12,
        weight="bold",
    )
    ax.text(
        L - 0.5 * delta,
        0.5 * L,
        r"$\Omega_R$" + "\nright pad",
        ha="center",
        va="center",
        fontsize=12,
        weight="bold",
    )
    ax.text(
        0.5 * L,
        0.5 * delta,
        third_pad_label,
        ha="center",
        va="center",
        fontsize=12,
        weight="bold",
    )
    ax.text(
        0.5 * L,
        0.5 * (L + delta),
        r"$\Omega_{\mathrm{phys}}$" + "\nphysical region",
        ha="center",
        va="center",
        fontsize=13,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "0.65"},
    )
    ax.annotate(
        "free surface",
        xy=(0.5 * L, L),
        xytext=(0.5 * L, L + 0.08 * L),
        arrowprops={"arrowstyle": "-", "linewidth": 1.6, "color": "0.25"},
        ha="center",
        va="bottom",
        fontsize=12,
        weight="bold",
    )

    arrow_style = {
        "arrowstyle": "<|-|>",
        "mutation_scale": 12,
        "linewidth": 1.4,
        "color": "0.25",
    }

    y_offset = -0.08 * L
    ax.annotate("", xy=(0.0, y_offset), xytext=(delta, y_offset), arrowprops=arrow_style)
    ax.text(0.5 * delta, y_offset - 0.04 * L, r"$\delta$", ha="center", va="top", fontsize=12)

    ax.annotate(
        "",
        xy=(L - delta, y_offset),
        xytext=(L, y_offset),
        arrowprops=arrow_style,
    )
    ax.text(L - 0.5 * delta, y_offset - 0.04 * L, r"$\delta$", ha="center", va="top", fontsize=12)

    x_offset = L + 0.08 * L
    ax.annotate(
        "",
        xy=(x_offset, 0.0),
        xytext=(x_offset, delta),
        arrowprops=arrow_style,
    )
    ax.text(x_offset + 0.03 * L, 0.5 * delta, r"$\delta$", ha="left", va="center", fontsize=12)

    ax.annotate(
        r"$w_L: 0 \rightarrow 1$",
        xy=(0.07 * L, 0.18 * L),
        xytext=(delta + 0.06 * L, 0.18 * L),
        arrowprops={"arrowstyle": "->", "linewidth": 1.4, "color": "#1b4965"},
        ha="left",
        va="center",
        fontsize=11,
        color="#1b4965",
    )
    ax.annotate(
        r"$w_R: 0 \rightarrow 1$",
        xy=(L - 0.07 * L, 0.32 * L),
        xytext=(L - delta - 0.18 * L, 0.32 * L),
        arrowprops={"arrowstyle": "->", "linewidth": 1.4, "color": "#8a4f08"},
        ha="right",
        va="center",
        fontsize=11,
        color="#8a4f08",
    )
    ax.annotate(
        r"$w_B: 0 \rightarrow 1$",
        xy=(0.62 * L, 0.06 * L),
        xytext=(0.62 * L, delta + 0.12 * L),
        arrowprops={"arrowstyle": "->", "linewidth": 1.4, "color": "#2d6a4f"},
        ha="center",
        va="bottom",
        fontsize=11,
        color="#2d6a4f",
    )

    ax.text(
        delta,
        0.02 * L,
        r"$x=\delta$",
        ha="left",
        va="bottom",
        fontsize=10,
        color="0.3",
    )
    ax.text(
        L - delta,
        0.02 * L,
        r"$x=L-\delta$",
        ha="right",
        va="bottom",
        fontsize=10,
        color="0.3",
    )
    ax.text(
        0.98 * L,
        delta,
        r"$z=\delta$",
        ha="right",
        va="bottom",
        fontsize=10,
        color="0.3",
    )

    ax.set_xlim(-0.15 * L, 1.15 * L)
    ax.set_ylim(-0.15 * L, 1.15 * L)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("z")
    ax.set_title("Physical region and absorbing pads")
    ax.set_xticks([0.0, delta, L - delta, L])
    ax.set_xticklabels(["0", r"$\delta$", r"$L-\delta$", r"$L$"])
    ax.set_yticks([0.0, delta, L])
    ax.set_yticklabels(["0", r"$\delta$", r"$L$"])
    ax.grid(False)
    fig.subplots_adjust(left=0.12, right=0.9, bottom=0.14, top=0.9)
    return fig, ax


def main() -> None:
    """Render the figure and optionally save it to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path where the rendered figure should be saved.",
    )
    parser.add_argument(
        "--domain-length",
        type=float,
        default=1.5,
        help="Side length of the square parent domain.",
    )
    parser.add_argument(
        "--pad-width",
        type=float,
        default=0.2,
        help="Width of each absorbing pad strip.",
    )
    args = parser.parse_args()

    fig, _ = plot_habc_regions_2d(
        domain_length=args.domain_length,
        pad_width=args.pad_width,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=200, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
