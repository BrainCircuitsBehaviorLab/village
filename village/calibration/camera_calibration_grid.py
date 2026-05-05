import math
from pathlib import Path

import matplotlib.pyplot as plt


def make_circle_grid(page_w_mm: float = 210.0, page_h_mm: float = 297.0,
                     spacing_mm: float = 50.0, circle_radius_mm: float = 10.0,
                     margin_mm: float = 5.0,
                     out_path: str = "calibration_grid.pdf", dpi: int = 300,
                     rotated_45: bool = False) -> Path:
    mm_per_inch = 25.4

    fig, ax = plt.subplots(figsize=(page_w_mm / mm_per_inch,
                                    page_h_mm / mm_per_inch))
    ax.set_xlim(0, page_w_mm)
    ax.set_ylim(0, page_h_mm)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    draw_w = page_w_mm - 2 * margin_mm
    draw_h = page_h_mm - 2 * margin_mm

    if rotated_45:
        diag = spacing_mm / math.sqrt(2)
        cx_center = page_w_mm / 2
        cy_center = page_h_mm / 2
        temp = max(draw_w, draw_h) * math.sqrt(2)
        half_extent = math.ceil(temp / diag) + 2
        for row in range(-half_extent, half_extent + 1):
            for col in range(-half_extent, half_extent + 1):
                cx = cx_center + (col * diag - row * diag)
                cy = cy_center + (col * diag + row * diag)
                cond1 = (margin_mm - circle_radius_mm
                         <= cx <= page_w_mm - margin_mm + circle_radius_mm)
                cond2 = (margin_mm - circle_radius_mm
                         <= cy <= page_h_mm - margin_mm + circle_radius_mm)
                if cond1 and cond2:
                    ax.add_patch(plt.Circle((cx, cy), circle_radius_mm,
                                            color="black"))
    else:
        cols = int(draw_w / spacing_mm)
        rows = int(draw_h / spacing_mm)
        for row in range(rows + 2):
            ax.plot([margin_mm - spacing_mm, margin_mm + (cols + 1)* spacing_mm],
                    [margin_mm  + row * spacing_mm] * 2, color="lightgray",
                    linewidth=1, zorder=1)
            for col in range(cols + 1):
                cx = margin_mm + col * spacing_mm
                cy = margin_mm + row * spacing_mm
                ax.add_patch(plt.Circle((cx, cy), circle_radius_mm,
                                        color="black"))
                ax.plot([margin_mm + col * spacing_mm] * 2,
                        [margin_mm - spacing_mm, margin_mm + (rows + 1) * spacing_mm],
                        color="lightgray", linewidth=1, zorder=1)

                ax.plot([cx - circle_radius_mm, cx + circle_radius_mm],
                        [cy, cy], color="w", linewidth=1, zorder=2)
                ax.plot([cx, cx], [cy - circle_radius_mm, cy + circle_radius_mm],
                        color="w", linewidth=1, zorder=2)

    out = Path(out_path)
    fig.savefig(out, dpi=dpi, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return out


if __name__ == "__main__":
    make_circle_grid()
    make_circle_grid(rotated_45=True, out_path="calibration_grid_rotated.pdf")
