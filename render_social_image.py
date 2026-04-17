#!/usr/bin/env python3
"""
Render a 1200x1200 social-share image from claude-code-stats.json.

Output: ~/linkedin-drafts/claude-code-stats.png (override with --output).
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG = (248, 246, 242)        # #F8F6F2
FG = (26, 26, 26)           # #1A1A1A
MUTED = (138, 138, 138)     # #8A8A8A
BORDER = (229, 225, 216)    # #E5E1D8
ACCENT = (232, 165, 180)    # #E8A5B4

W, H = 1200, 1200
MARGIN = 80

FONT_PATHS = [
    "/System/Library/Fonts/SFNS.ttf",
    "/Library/Fonts/Roboto-Regular.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
BOLD_PATHS = [
    "/System/Library/Fonts/SFNS.ttf",
    "/Library/Fonts/Roboto-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(paths, size):
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def fmt_month(ym: str) -> str:
    y, m = ym.split("-")
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{names[int(m) - 1]} {y}"


def render(stats_path: Path, out_path: Path) -> None:
    data = json.loads(stats_path.read_text())
    total = data["total"]
    months = data["months"]

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    f_eyebrow = load_font(FONT_PATHS, 22)
    f_title = load_font(BOLD_PATHS, 54)
    f_sub = load_font(FONT_PATHS, 28)
    f_kpi_num = load_font(BOLD_PATHS, 96)
    f_kpi_label = load_font(FONT_PATHS, 22)
    f_month = load_font(FONT_PATHS, 22)
    f_bar_val = load_font(FONT_PATHS, 20)
    f_foot = load_font(FONT_PATHS, 22)

    y = MARGIN

    d.text((MARGIN, y), "CLAUDE CODE — USAGE SO FAR", font=f_eyebrow, fill=FG)
    y += 54

    title = f"Power user since {fmt_month(total['first_month'])}"
    d.text((MARGIN, y), title, font=f_title, fill=FG)
    y += 78

    sub = "Everything I ship runs through Claude Code."
    d.text((MARGIN, y), sub, font=f_sub, fill=MUTED)
    y += 72

    d.line([(MARGIN, y), (W - MARGIN, y)], fill=BORDER, width=1)
    y += 40

    kpis = [
        (f"{int(round(total['hours']))}", "HOURS"),
        (str(total["sessions"]), "SESSIONS"),
        (str(total["commits"]), "COMMITS"),
        (str(total["days_active"]), "DAYS ACTIVE"),
    ]
    col_w = (W - 2 * MARGIN) / 4
    for i, (num, label) in enumerate(kpis):
        x = MARGIN + col_w * i
        d.text((x, y), num, font=f_kpi_num, fill=FG)
        bbox = d.textbbox((x, y), num, font=f_kpi_num)
        label_y = bbox[3] + 8
        d.text((x, label_y), label, font=f_kpi_label, fill=MUTED)
    y += 170

    d.line([(MARGIN, y), (W - MARGIN, y)], fill=BORDER, width=1)
    y += 48

    d.text((MARGIN, y), "MONTH BY MONTH (hours)", font=f_eyebrow, fill=MUTED)
    y += 46

    chart_top = y
    chart_bottom = H - MARGIN - 80
    chart_h = chart_bottom - chart_top
    chart_left = MARGIN
    chart_right = W - MARGIN

    max_hours = max((m["hours"] for m in months), default=1)
    if max_hours <= 0:
        max_hours = 1
    n = len(months)
    if n == 0:
        n = 1
    slot_w = (chart_right - chart_left) / n
    bar_w = slot_w * 0.55

    for i, m in enumerate(months):
        bar_h = int(chart_h * (m["hours"] / max_hours))
        x0 = chart_left + slot_w * i + (slot_w - bar_w) / 2
        x1 = x0 + bar_w
        y0 = chart_bottom - bar_h
        y1 = chart_bottom
        color = ACCENT if m.get("partial") else FG
        d.rectangle([x0, y0, x1, y1], fill=color)

        val = f"{m['hours']:.0f}h"
        vb = d.textbbox((0, 0), val, font=f_bar_val)
        vw = vb[2] - vb[0]
        d.text((x0 + bar_w / 2 - vw / 2, y0 - 30), val, font=f_bar_val, fill=FG)

        lbl = fmt_month(m["month"])
        lb = d.textbbox((0, 0), lbl, font=f_month)
        lw = lb[2] - lb[0]
        d.text((x0 + bar_w / 2 - lw / 2, chart_bottom + 10), lbl, font=f_month, fill=MUTED)

    d.text((MARGIN, H - MARGIN - 30), "schlacter.me/claude-code", font=f_foot, fill=MUTED)
    ln = "github.com/hbschlac/claude-code-insights-dashboard"
    lb = d.textbbox((0, 0), ln, font=f_foot)
    d.text((W - MARGIN - (lb[2] - lb[0]), H - MARGIN - 30), ln, font=f_foot, fill=MUTED)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    print(f"Wrote {out_path}")


def main():
    default_stats = Path.home() / "schlacter-me" / "public" / "claude-code-stats.json"
    default_out = Path.home() / "linkedin-drafts" / "claude-code-stats.png"
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", default=str(default_stats))
    ap.add_argument("--output", default=str(default_out))
    args = ap.parse_args()
    render(Path(args.stats), Path(args.output))


if __name__ == "__main__":
    main()
