#!/usr/bin/env python3
"""Render a field hockey session plan (JSON) into a PDF with drill diagrams.

Usage:
    python build_session_pdf.py plan.json output.pdf

See references/plan_schema.md for the JSON format.
"""
import json
import math
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# ---------------------------------------------------------------- palette
NAVY = colors.HexColor("#14284B")
ACCENT = colors.HexColor("#2E7D32")
LIGHT = colors.HexColor("#EEF2F7")
MID = colors.HexColor("#C9D3E0")
TURF = colors.HexColor("#3E8E4F")
TURF_DARK = colors.HexColor("#357A44")
LINE = colors.white

TEAM_COLOURS = {
    "A": colors.HexColor("#1E5BC6"),        # blue bibs
    "B": colors.HexColor("#D32F2F"),        # red bibs
    "C": colors.HexColor("#F2C200"),        # yellow / third team
    "GK": colors.HexColor("#FFD54F"),
    "neutral": colors.HexColor("#FF8F00"),  # floaters / jokers
    "coach": colors.HexColor("#111111"),
}
CONE_COLOURS = {
    "orange": colors.HexColor("#FF7A00"),
    "yellow": colors.HexColor("#FFE000"),
    "red": colors.HexColor("#E53935"),
    "blue": colors.HexColor("#1E88E5"),
    "white": colors.white,
}
ZONE_COLOURS = {
    "blue": colors.Color(0.2, 0.45, 0.9, alpha=0.28),
    "red": colors.Color(0.9, 0.25, 0.25, alpha=0.28),
    "yellow": colors.Color(1, 0.9, 0.2, alpha=0.32),
    "white": colors.Color(1, 1, 1, alpha=0.22),
}

PHASE_COLOURS = {
    "warm-up": colors.HexColor("#F57C00"),
    "technical": colors.HexColor("#1E5BC6"),
    "skill": colors.HexColor("#1E5BC6"),
    "small-sided": colors.HexColor("#6A1B9A"),
    "game-related": colors.HexColor("#6A1B9A"),
    "conditioned": colors.HexColor("#C62828"),
    "live": colors.HexColor("#C62828"),
    "game": colors.HexColor("#2E7D32"),
}


def phase_colour(phase):
    p = (phase or "").lower()
    for key, col in PHASE_COLOURS.items():
        if key in p:
            return col
    return NAVY


# ---------------------------------------------------------------- pitch areas
FULL_L, FULL_W = 91.4, 55.0
D_RADIUS = 14.63
GOAL_W = 3.66


def area_dims(area):
    t = (area or {}).get("type", "grid")
    if t == "full":
        return FULL_L, FULL_W
    if t == "half":
        return FULL_L / 2, FULL_W
    if t in ("23", "quarter"):
        return 22.9, FULL_W
    return float(area.get("length", 30)), float(area.get("width", 20))


class Diagram(Flowable):
    """Top-down drill diagram. Coordinates are metres: x along length, y across width."""

    def __init__(self, spec, width, max_height):
        super().__init__()
        self.spec = spec or {}
        self.area = self.spec.get("area", {"type": "grid", "length": 30, "width": 20})
        self.L, self.W = area_dims(self.area)
        self.pad = 4 * mm
        self.legend_h = 0
        avail_w = width - 2 * self.pad
        avail_h = max_height - 2 * self.pad
        self.scale = min(avail_w / self.L, avail_h / self.W)
        self.width = width
        self.height = self.W * self.scale + 2 * self.pad

    # coordinate transform (y=0 at the bottom touchline)
    def P(self, x, y):
        ox = (self.width - self.L * self.scale) / 2
        return ox + x * self.scale, self.pad + y * self.scale

    def draw(self):
        c = self.canv
        c.saveState()
        self._draw_surface(c)
        for el in self.spec.get("elements", []):
            if el.get("type") == "zone":
                self._zone(c, el)
        for el in self.spec.get("elements", []):
            t = el.get("type")
            if t == "arrow":
                self._arrow(c, el)
        for el in self.spec.get("elements", []):
            t = el.get("type")
            try:
                if t == "cone":
                    self._cone(c, el)
                elif t == "goal":
                    self._mini_goal(c, el)
                elif t == "ball":
                    self._ball(c, el)
                elif t == "player":
                    self._player(c, el)
                elif t == "text":
                    self._text(c, el)
            except Exception:
                pass  # never let one bad element kill the whole plan
        c.restoreState()

    # ---- surface
    def _draw_surface(self, c):
        x0, y0 = self.P(0, 0)
        x1, y1 = self.P(self.L, self.W)
        # run-off border
        c.setFillColor(TURF_DARK)
        c.roundRect(x0 - 3 * mm, y0 - 3 * mm, (x1 - x0) + 6 * mm, (y1 - y0) + 6 * mm, 2 * mm, stroke=0, fill=1)
        # stripes
        n = 8
        sw = (x1 - x0) / n
        for i in range(n):
            c.setFillColor(TURF if i % 2 == 0 else colors.HexColor("#449757"))
            c.rect(x0 + i * sw, y0, sw, y1 - y0, stroke=0, fill=1)
        c.setStrokeColor(LINE)
        c.setLineWidth(1.1)
        c.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=0)

        t = self.area.get("type", "grid")
        if t == "full":
            self._vline(FULL_L / 2)
            self._vline(22.9, dashed=False)
            self._vline(FULL_L - 22.9, dashed=False)
            self._d(0, facing="right")
            self._d(FULL_L, facing="left")
        elif t == "half":
            self._vline(FULL_L / 2 - 22.9)
            self._d(self.L, facing="left")
        elif t in ("23", "quarter"):
            self._d(self.L, facing="left")
        else:
            # plain grid: corner cones
            for (cx, cy) in ((0, 0), (self.L, 0), (0, self.W), (self.L, self.W)):
                self._cone(self.canv, {"x": cx, "y": cy, "color": "orange"})

    def _vline(self, x, dashed=False):
        c = self.canv
        a, b = self.P(x, 0), self.P(x, self.W)
        if dashed:
            c.setDash(3, 2)
        c.line(a[0], a[1], b[0], b[1])
        c.setDash()

    def _d(self, goal_x, facing):
        """Shooting circle, dotted 5m line, goal and penalty spot."""
        c = self.canv
        s = self.scale
        sign = 1 if facing == "right" else -1
        cy = self.W / 2
        p1, p2 = cy - GOAL_W / 2, cy + GOAL_W / 2

        def arc_points(r):
            pts = []
            # lower arc around post p1, then straight, then upper arc around p2
            for i in range(0, 46):
                a = math.radians(-90 + i * 2)
                pts.append((goal_x + sign * r * math.cos(a), p1 + r * math.sin(a)))
            for i in range(0, 46):
                a = math.radians(0 + i * 2)
                pts.append((goal_x + sign * r * math.cos(a), p2 + r * math.sin(a)))
            return pts

        for r, dash in ((D_RADIUS, None), (D_RADIUS + 5, (2, 3))):
            pts = [self.P(x, y) for x, y in arc_points(r)]
            path = c.beginPath()
            path.moveTo(*pts[0])
            for p in pts[1:]:
                path.lineTo(*p)
            if dash:
                c.setDash(*dash)
            c.setLineWidth(1.0)
            c.drawPath(path, stroke=1, fill=0)
            c.setDash()
        # goal
        gx, gy1 = self.P(goal_x, p1)
        _, gy2 = self.P(goal_x, p2)
        depth = 1.2 * s
        c.setFillColor(colors.white)
        c.setLineWidth(1.4)
        c.rect(gx if sign < 0 else gx - depth, gy1, depth, gy2 - gy1, stroke=1, fill=0)
        # penalty spot
        sx, sy = self.P(goal_x + sign * 6.475, cy)
        c.circle(sx, sy, 0.9, stroke=0, fill=1)

    # ---- elements
    def _zone(self, c, el):
        x, y = self.P(el["x"], el["y"])
        w, h = el["w"] * self.scale, el["h"] * self.scale
        c.setFillColor(ZONE_COLOURS.get(el.get("color", "white"), ZONE_COLOURS["white"]))
        c.setStrokeColor(colors.white)
        c.setDash(2, 2)
        c.setLineWidth(0.8)
        c.rect(x, y, w, h, stroke=1, fill=1)
        c.setDash()
        if el.get("label"):
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 6.5)
            c.drawCentredString(x + w / 2, y + h - 8, el["label"])

    def _cone(self, c, el):
        x, y = self.P(el["x"], el["y"])
        col = CONE_COLOURS.get(el.get("color", "orange"), CONE_COLOURS["orange"])
        r = 2.3
        p = c.beginPath()
        p.moveTo(x, y + r * 1.3)
        p.lineTo(x - r, y - r * 0.8)
        p.lineTo(x + r, y - r * 0.8)
        p.close()
        c.setFillColor(col)
        c.setStrokeColor(colors.HexColor("#333333"))
        c.setLineWidth(0.4)
        c.drawPath(p, stroke=1, fill=1)

    def _ball(self, c, el):
        x, y = self.P(el["x"], el["y"])
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#222222"))
        c.setLineWidth(0.5)
        c.circle(x, y, 1.9, stroke=1, fill=1)

    def _mini_goal(self, c, el):
        size = el.get("size", "mini")
        width_m = GOAL_W if size == "full" else float(el.get("width", 2.0))
        facing = el.get("facing", "left")
        s = self.scale
        x, y = self.P(el["x"], el["y"])
        half = width_m * s / 2
        depth = max(4, 0.9 * s)
        c.setStrokeColor(colors.white)
        c.setFillColor(colors.Color(1, 1, 1, alpha=0.35))
        c.setLineWidth(1.3)
        if facing in ("left", "right"):
            dx = depth if facing == "left" else -depth
            c.rect(min(x, x + dx), y - half, abs(dx), 2 * half, stroke=1, fill=1)
        else:
            dy = -depth if facing == "up" else depth
            c.rect(x - half, min(y, y + dy), 2 * half, abs(dy), stroke=1, fill=1)

    def _player(self, c, el):
        x, y = self.P(el["x"], el["y"])
        team = el.get("team", "A")
        col = TEAM_COLOURS.get(team, TEAM_COLOURS["A"])
        r = 4.2
        c.setFillColor(col)
        c.setStrokeColor(colors.white)
        c.setLineWidth(0.9)
        if team == "coach":
            c.rect(x - r, y - r, 2 * r, 2 * r, stroke=1, fill=1)
        else:
            c.circle(x, y, r, stroke=1, fill=1)
        label = str(el.get("label", "GK" if team == "GK" else ("C" if team == "coach" else "")))
        if label:
            c.setFillColor(colors.black if team in ("GK", "C", "neutral") else colors.white)
            c.setFont("Helvetica-Bold", 5.2 if len(label) > 1 else 6)
            c.drawCentredString(x, y - 2, label[:3])

    def _text(self, c, el):
        x, y = self.P(el["x"], el["y"])
        c.setFont("Helvetica-Bold", 6.5)
        tw = c.stringWidth(el["text"], "Helvetica-Bold", 6.5)
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.45))
        c.roundRect(x - tw / 2 - 2, y - 3, tw + 4, 9, 2, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.drawCentredString(x, y, el["text"])

    def _arrow(self, c, el):
        pts = [self.P(px, py) for px, py in el.get("points", [])]
        if len(pts) < 2:
            return
        style = el.get("style", "pass")
        col = {"pass": colors.white, "run": colors.HexColor("#FFE082"),
               "dribble": colors.HexColor("#B3E5FC"), "shot": colors.HexColor("#FF8A80")}.get(style, colors.white)
        c.setStrokeColor(col)
        c.setFillColor(col)
        c.setLineWidth(1.2 if style != "shot" else 1.6)
        path = c.beginPath()
        if style == "dribble":
            wavy = self._wavy(pts)
            path.moveTo(*wavy[0])
            for p in wavy[1:]:
                path.lineTo(*p)
        else:
            path.moveTo(*pts[0])
            for p in pts[1:]:
                path.lineTo(*p)
        if style == "run":
            c.setDash(3, 2.2)
        c.drawPath(path, stroke=1, fill=0)
        c.setDash()
        # arrowhead
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        ang = math.atan2(by - ay, bx - ax)
        size = 5
        head = c.beginPath()
        head.moveTo(bx, by)
        head.lineTo(bx - size * math.cos(ang - 0.4), by - size * math.sin(ang - 0.4))
        head.lineTo(bx - size * math.cos(ang + 0.4), by - size * math.sin(ang + 0.4))
        head.close()
        c.drawPath(head, stroke=0, fill=1)

    @staticmethod
    def _wavy(pts, amp=1.8, wavelength=7.0):
        out = []
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            seg = math.hypot(bx - ax, by - ay)
            if seg == 0:
                continue
            ux, uy = (bx - ax) / seg, (by - ay) / seg
            nx, ny = -uy, ux
            steps = max(2, int(seg / 1.2))
            for i in range(steps + 1):
                t = i / steps
                d = t * seg
                # taper the wave to zero at the end so the arrowhead lines up
                taper = min(1.0, (seg - d) / 6.0)
                off = amp * math.sin(2 * math.pi * d / wavelength) * taper
                out.append((ax + ux * d + nx * off, ay + uy * d + ny * off))
        return out or pts


# ---------------------------------------------------------------- legend
class Legend(Flowable):
    ITEMS = [
        ("player", "A", "Team A"), ("player", "B", "Team B"), ("player", "GK", "Goalkeeper"),
        ("player", "neutral", "Floater"), ("player", "coach", "Coach"), ("cone", None, "Cone"),
        ("ball", None, "Ball"), ("pass", None, "Pass"), ("run", None, "Run (off ball)"),
        ("dribble", None, "Dribble / carry"), ("shot", None, "Shot"),
    ]

    def __init__(self, width):
        super().__init__()
        self.width = width
        self.height = 13 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(TURF)
        c.roundRect(0, 0, self.width, self.height, 2 * mm, stroke=0, fill=1)
        per_row = 6
        col_w = self.width / per_row
        for i, (kind, team, label) in enumerate(self.ITEMS):
            row, col = divmod(i, per_row)
            x = col * col_w + 6 * mm
            y = self.height - (row + 1) * 6 * mm + 1.6 * mm
            if kind == "player":
                c.setFillColor(TEAM_COLOURS[team])
                c.setStrokeColor(colors.white)
                if team == "coach":
                    c.rect(x - 3.5, y - 3.5, 7, 7, stroke=1, fill=1)
                else:
                    c.circle(x, y, 3.5, stroke=1, fill=1)
            elif kind == "cone":
                c.setFillColor(CONE_COLOURS["orange"])
                p = c.beginPath(); p.moveTo(x, y + 3.5); p.lineTo(x - 3, y - 2.5); p.lineTo(x + 3, y - 2.5); p.close()
                c.drawPath(p, stroke=0, fill=1)
            elif kind == "ball":
                c.setFillColor(colors.white); c.circle(x, y, 2.2, stroke=0, fill=1)
            else:
                col_ = {"pass": colors.white, "run": colors.HexColor("#FFE082"),
                        "dribble": colors.HexColor("#B3E5FC"), "shot": colors.HexColor("#FF8A80")}[kind]
                c.setStrokeColor(col_); c.setFillColor(col_); c.setLineWidth(1.2)
                if kind == "run":
                    c.setDash(3, 2)
                if kind == "dribble":
                    p = c.beginPath(); p.moveTo(x - 5, y)
                    for k in range(1, 11):
                        p.lineTo(x - 5 + k, y + 1.6 * math.sin(k * 1.2))
                    c.drawPath(p, stroke=1, fill=0)
                else:
                    c.line(x - 5, y, x + 5, y)
                c.setDash()
                h = c.beginPath(); h.moveTo(x + 7, y); h.lineTo(x + 3.5, y + 2); h.lineTo(x + 3.5, y - 2); h.close()
                c.drawPath(h, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica", 7)
            c.drawString(x + 9, y - 2.4, label)


# ---------------------------------------------------------------- text styles
BASE = ParagraphStyle("base", fontName="Helvetica", fontSize=8.6, leading=11.2, alignment=TA_LEFT)
SMALL = ParagraphStyle("small", parent=BASE, fontSize=7.8, leading=10)
H_LABEL = ParagraphStyle("hlabel", parent=BASE, fontName="Helvetica-Bold", fontSize=8, textColor=NAVY,
                         spaceBefore=3, spaceAfter=1)
TITLE = ParagraphStyle("title", parent=BASE, fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.white)
SUB = ParagraphStyle("sub", parent=BASE, fontSize=10, leading=13, textColor=colors.white)
BLOCK_T = ParagraphStyle("blockt", parent=BASE, fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.white)
CELL_B = ParagraphStyle("cellb", parent=BASE, fontName="Helvetica-Bold")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def bullets(items, style=BASE):
    if not items:
        return []
    if isinstance(items, str):
        items = [items]
    return [Paragraph("• " + esc(i), style) for i in items]


def section(label, content, style=BASE):
    if not content:
        return []
    out = [Paragraph(esc(label).upper(), H_LABEL)]
    if isinstance(content, str):
        out.append(Paragraph(esc(content), style))
    else:
        out += bullets(content, style)
    return out


# ---------------------------------------------------------------- page furniture
def make_on_page(plan):
    team = plan.get("team", "")
    theme = plan.get("theme", "")

    def on_page(canv, doc):
        canv.saveState()
        w, h = A4
        canv.setFillColor(NAVY)
        canv.rect(0, 0, w, 9 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont("Helvetica", 7.5)
        canv.drawString(15 * mm, 3.4 * mm, f"{team}  |  {theme}")
        canv.drawRightString(w - 15 * mm, 3.4 * mm, f"Page {doc.page}")
        canv.restoreState()

    return on_page


# ---------------------------------------------------------------- build
def build(plan, out_path):
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=12 * mm, bottomMargin=14 * mm,
                            title=f"{plan.get('team', 'Hockey')} session plan - {plan.get('theme', '')}",
                            author=plan.get("coach", ""))
    W = A4[0] - 30 * mm
    story = []

    # --- header banner
    banner = Table([
        [Paragraph("SESSION PLAN", ParagraphStyle("k", parent=SUB, fontSize=8, textColor=colors.HexColor("#9FB4D6")))],
        [Paragraph(esc(plan.get("theme", "Training session")), TITLE)],
        [Paragraph(esc(plan.get("team", "")) + (f"  ·  {esc(plan['date'])}" if plan.get("date") else ""), SUB)],
    ], colWidths=[W])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (0, 0), 9), ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("TOPPADDING", (0, 1), (-1, -1), 1),
    ]))
    story += [banner, Spacer(1, 4 * mm)]

    # --- session details grid
    blocks = plan.get("blocks", [])
    total = plan.get("duration") or sum(int(b.get("minutes", 0)) for b in blocks)
    details = [
        ("Team / age group", plan.get("team", "")),
        ("Coach", plan.get("coach", "")),
        ("Date / time", plan.get("date", "")),
        ("Venue / space", plan.get("venue", "")),
        ("Duration", f"{total} mins" if total else ""),
        ("Players", plan.get("players", "")),
        ("Equipment", ", ".join(plan["equipment"]) if isinstance(plan.get("equipment"), list) else plan.get("equipment", "")),
        ("Session focus", plan.get("focus", plan.get("theme", ""))),
    ]
    rows, row = [], []
    for k, v in details:
        row += [Paragraph(esc(k), CELL_B), Paragraph(esc(v) if v else "&nbsp;", BASE)]
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row + ["", ""])
    dt = Table(rows, colWidths=[28 * mm, W / 2 - 28 * mm, 28 * mm, W / 2 - 28 * mm])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT), ("BACKGROUND", (2, 0), (2, -1), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, MID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [dt, Spacer(1, 4 * mm)]

    # --- objectives + overview side by side
    obj = [Paragraph("SESSION OBJECTIVES", H_LABEL)] + bullets(plan.get("objectives", []))
    if plan.get("key_messages"):
        obj += [Spacer(1, 2 * mm), Paragraph("KEY MESSAGES / TRIGGER WORDS", H_LABEL)] + bullets(plan["key_messages"])
    ov_rows = [[Paragraph("<b>Time</b>", SMALL), Paragraph("<b>Block</b>", SMALL), Paragraph("<b>Mins</b>", SMALL)]]
    t = 0
    for b in blocks:
        m = int(b.get("minutes", 0))
        ov_rows.append([Paragraph(f"{t}–{t + m}", SMALL),
                        Paragraph(f"<b>{esc(b.get('phase', ''))}</b><br/>{esc(b.get('title', ''))}", SMALL),
                        Paragraph(str(m), SMALL)])
        t += m
    ov = Table(ov_rows, colWidths=[14 * mm, 52 * mm, 11 * mm])
    ov_style = [("GRID", (0, 0), (-1, -1), 0.5, MID), ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i, b in enumerate(blocks, start=1):
        ov_style.append(("LINEBEFORE", (0, i), (0, i), 3, phase_colour(b.get("phase"))))
    ov.setStyle(TableStyle(ov_style))
    two = Table([[obj, [Paragraph("SESSION OVERVIEW", H_LABEL), ov]]], colWidths=[W - 80 * mm, 80 * mm])
    two.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [two, Spacer(1, 4 * mm), Paragraph("DIAGRAM KEY", H_LABEL), Legend(W), Spacer(1, 5 * mm)]

    # --- each block
    t = 0
    diag_w = 92 * mm
    for i, b in enumerate(blocks, start=1):
        m = int(b.get("minutes", 0))
        col = phase_colour(b.get("phase"))
        head = Table([[Paragraph(f"{i}. {esc(b.get('phase', '')).upper()} — {esc(b.get('title', ''))}", BLOCK_T),
                       Paragraph(f"<b>{t}–{t + m} min</b>  ({m}')", ParagraphStyle("r", parent=SUB, alignment=2))]],
                     colWidths=[W - 38 * mm, 38 * mm])
        head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), col), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        t += m

        left = []
        if b.get("diagram"):
            left.append(Diagram(b["diagram"], diag_w, 70 * mm))
            if b["diagram"].get("caption"):
                left.append(Paragraph("<i>" + esc(b["diagram"]["caption"]) + "</i>", SMALL))
        left += section("Organisation / set-up", b.get("setup"))
        if b.get("step"):
            step = b["step"]
            left.append(Paragraph("ADAPT IT (STEP)", H_LABEL))
            for k in ("space", "task", "equipment", "people"):
                if step.get(k):
                    left.append(Paragraph(f"<b>{k[0].upper()}</b> {k.title()}: {esc(step[k])}", SMALL))

        right = []
        right += section("How it works", b.get("how"))
        right += section("Link to theme", b.get("link_to_theme"))
        right += section("Coaching points", b.get("coaching_points"))
        right += section("Questions to ask", b.get("questions"))
        right += section("Progressions (harder)", b.get("progressions"))
        right += section("Regressions (easier)", b.get("regressions"))
        right += section("Keeping everyone active", b.get("activity_notes"))

        body = Table([[left, right]], colWidths=[diag_w + 4 * mm, W - diag_w - 4 * mm])
        body.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("LEFTPADDING", (0, 0), (0, 0), 0),
                                  ("BOX", (0, 0), (-1, -1), 0.6, MID),
                                  ("TOPPADDING", (0, 0), (-1, -1), 5),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story.append(KeepTogether([head, body]))
        story.append(Spacer(1, 5 * mm))

    # --- reflection
    refl = plan.get("reflection_prompts") or [
        "What went well against today's objectives?",
        "Which players stood out / need follow-up?",
        "What would I change next time (space, numbers, timings)?",
        "Carry-over theme for next session:",
    ]
    rt = Table([[Paragraph("<b>" + esc(q) + "</b>", BASE), ""] for q in refl], colWidths=[75 * mm, W - 75 * mm],
               rowHeights=[12 * mm] * len(refl))
    rt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, MID), ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(KeepTogether([Paragraph("POST-SESSION REFLECTION", H_LABEL), rt]))
    if plan.get("safety"):
        story += [Spacer(1, 3 * mm)] + section("Safety / welfare notes", plan["safety"])

    doc.build(story, onFirstPage=make_on_page(plan), onLaterPages=make_on_page(plan))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: build_session_pdf.py plan.json output.pdf")
    with open(sys.argv[1]) as f:
        build(json.load(f), sys.argv[2])
    print(f"Wrote {sys.argv[2]}")
