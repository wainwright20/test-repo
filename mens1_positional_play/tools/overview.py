import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

NAVY = colors.HexColor("#14284b")
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=20, textColor=NAVY, leading=24)
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=10.5, textColor=colors.HexColor("#444444"), leading=14)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, textColor=NAVY, leading=15, spaceBefore=6)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=9, leading=12)
BB = ParagraphStyle("bb", parent=B, fontName="Helvetica-Bold")
TH = ParagraphStyle("th", parent=B, fontName="Helvetica-Bold", textColor=colors.white)

def p(t, s=B): return Paragraph(t, s)

rows = [
    [p("Week", TH), p("Principle", TH), p("What the players learn", TH), p("Trigger words", TH)],
    [p("1", BB), p("<b>Two players in every lane</b>", B),
     p("The 5 lanes. FB inverts into the half-space as the CB receives, 8 drifts wide on the blind side of their winger. 2v1 on their centre mid; find the free player.", B),
     p("Two in a lane / FB in, 8 out / Who's free?", B)],
    [p("2", BB), p("<b>The rotation chain</b>", B),
     p("FB in, 8 out, W in. Their FB, CB and CM have to decide who follows. Diagonal into the inside W, reverse pass behind a jumping FB, and the ladder (8 to 9, set, W in behind).", B),
     p("8 out, W in / Who follows? / Reverse it / Ladder", B)],
    [p("3", BB), p("<b>Occupy and vacate</b>", B),
     p("8 drags their CM, 9 drops, 8 runs beyond on the blind side as the temporary 9. Diagonal passes onto the back foot. Far 8 fills the centre; 9 plays round the corner.", B),
     p("Someone moves, I move / Drop and go / Diagonal", B)],
    [p("4", BB), p("<b>Breaking a mid-block</b>", B),
     p("Against a 4-4-2 style block: FB high, W inside, 8 drops on an angle = 5v4 on their last line. CB drops to question their forward. 6 switches in one action for the far-side 2v1. Central 3v2 (8, 9, W) on their CBs.", B),
     p("Five on four / Open up, switch / Three on two", B)],
]
t = Table(rows, colWidths=[13*mm, 38*mm, 92*mm, 37*mm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), NAVY),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f2f5fa"), colors.white]),
    ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#c9d2e0")),
    ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))

def bl(items):
    return [p("&bull; " + i) for i in items]

story = [
    p("Men's 1st XI: Positional Play Block", H1), Spacer(1, 2*mm),
    p("4 weeks x 90 minutes. Each session follows the usual structure: Warm-up 10 / Technical 20 / Small-sided 20 / Live game scenario 20 / Game 20. Each week builds on the one before, and the earlier principles still apply in every game block.", SUB),
    Spacer(1, 5*mm), t, Spacer(1, 4*mm),
    p("The one idea behind all four weeks", H2),
    p("Two players in every lane. When someone moves, someone else moves into their space. The timing (moving as the ball travels, not after it arrives) and ball speed (2-3 touches) are what turn the rotation into a free player."),
    p("Shape and labels used in the diagrams", H2),
] + bl([
    "Back 4 (LB, LCB, RCB, RB), a holding 6, two inside mids (8s), LW, 9 (centre forward), RW. Blue is always us, red is the opposition.",
    "Lanes, viewed from our goal: left wide lane, left half-space, centre, right half-space, right wide lane. Mark them with cones on both sidelines every week.",
    "\"Back foot\" in the source video means receiving on an open body (shoulders turned so you can see forward and play first time).",
    "No offside in hockey: the 9 can stay high and pin both CBs, which makes the 5v4 and central 3v2 even easier to set up than in the video.",
]) + [
    p("How to run the block", H2),
] + bl([
    "Before Week 1: 5-minute whiteboard or video clip showing the 5 lanes and the FB-in/8-out picture. Show it once; let the drills do the rest.",
    "Run every technical block on the left side first, then switch to the right, so both sides of the team learn it.",
    "Use the same trigger words every week so they become match language.",
    "Track the same 3 numbers in every final game: rotations completed, switches of play, circle entries from them. Compare Week 1 to Week 4.",
    "If Week 2 or 3 doesn't stick, repeat that week rather than moving on. Week 4 relies on everything before it.",
]) + [
    p("Assumptions", H2),
    p("16 outfield + 2 GKs, half pitch for most of each session and the full pitch for the live game scenario and game, 20+ balls, 3 sets of bibs, 4 mini goals. Every drill lists a regression if numbers are down."),
]

doc = SimpleDocTemplate(sys.argv[1], pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=14*mm, bottomMargin=14*mm)
doc.build(story)
