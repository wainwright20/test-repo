# Session plan JSON format

The PDF builder (`scripts/build_session_pdf.py`) takes one JSON object. Every field is optional except `team`, `theme` and `blocks`, but the more you fill in, the more useful the plan is at the pitch.

## Top level

```json
{
  "team": "Ladies' 1st XI",
  "coach": "Head Coach",
  "date": "Thursday 23 Oct, 19:30",
  "venue": "Half pitch",
  "duration": 75,
  "players": "14 outfield + 1 GK",
  "equipment": ["Balls x20", "Cones", "Bibs x2 sets", "Mini goals x4"],
  "theme": "Short title shown in the banner",
  "focus": "One sentence: what the session is really about",
  "objectives": ["2-3 outcomes"],
  "key_messages": ["Short trigger words / phrases"],
  "blocks": [ ... five blocks ... ],
  "safety": ["Optional safety / welfare notes"],
  "reflection_prompts": ["Optional - replaces the default post-session questions"]
}
```

## Block

```json
{
  "phase": "Warm-up | Technical | Small-sided | Live game scenario | Game",
  "title": "Name of the drill",
  "minutes": 10,
  "diagram": { ... see below ... },
  "setup": "Area, numbers, kit - one or two sentences",
  "how": ["Step-by-step bullets"],
  "link_to_theme": "Why this block matters for today's theme",
  "coaching_points": ["3-4 specific points"],
  "questions": ["Optional guided-discovery questions"],
  "progressions": ["Make it harder"],
  "regressions": ["Make it easier"],
  "activity_notes": "How queues/standing are avoided",
  "step": {"space": "...", "task": "...", "equipment": "...", "people": "..."}
}
```

The `phase` word decides the colour of the block header: warm-up = orange, technical = blue, small-sided = purple, live game scenario = red, game = green. Use these five phase names, which match the coach's structure in SKILL.md.

## Diagram

```json
{
  "area": {"type": "grid", "length": 20, "width": 15},
  "caption": "One line describing what the picture shows",
  "elements": [ ... ]
}
```

### Area types

| type | Size (m) | Drawn automatically |
|---|---|---|
| `grid` | `length` x `width` you give | Corner cones |
| `23` / `quarter` | 22.9 x 55 | Shooting circle, dotted 5m line, goal on the **right** |
| `half` | 45.7 x 55 | 23m line, shooting circle and goal on the **right**. x=0 is the halfway line |
| `full` | 91.4 x 55 | Halfway line, both 23s, both circles and goals |

Coordinates are in **metres**: `x` runs along the length (left → right) and `y` across the width (bottom → top), with (0,0) at the bottom-left. Keep elements inside the area. For `half`, the goal mouth is at x≈45.7, y≈27.5, and the top of the shooting circle is at roughly x≈31.

Grid size guide: 10x10 (tight 1v1 / rondo for 4-5), 15x15 (rondo 5v2), 20x20 (4v4 possession), 30x20 (small-sided 3v3/4v4 with mini goals), 40x30 (6v6).

### Element types

| type | Fields | Notes |
|---|---|---|
| `player` | `x`, `y`, `team`, `label` | `team`: `A` (blue), `B` (red), `C` (yellow), `GK`, `neutral` (orange floater), `coach` (black square; use label "H" for a helper). `label` up to 3 chars, e.g. "1", "CF", "LB". Use `""` for no label. |
| `cone` | `x`, `y`, `color` | `orange`, `yellow`, `red`, `blue`, `white` |
| `ball` | `x`, `y` | Put it just beside the player who has it (~0.8m away) |
| `goal` | `x`, `y`, `size`, `facing`, `width` | `size`: `mini` (default 2m wide) or `full`. `facing` = which way the mouth opens: `left`, `right`, `up`, `down`. Full goals on `half`/`full`/`23` areas are drawn for you, so only add mini goals. |
| `arrow` | `style`, `points` | `style`: `pass` (solid white), `run` (dashed yellow = movement without the ball), `dribble` (wavy blue = carrying the ball), `shot` (red). `points` = `[[x,y],[x,y],...]`; two or more points; the arrowhead is drawn at the last point. Start arrows just off the player's dot so they don't cover the number. |
| `zone` | `x`, `y`, `w`, `h`, `color`, `label` | Shaded rectangle from bottom-left (`x`,`y`). `color`: `blue`, `red`, `yellow`, `white`. Use it for channels, scoring zones, "trap" areas. Keep `label` to 1-2 short words; it shrinks to fit narrow zones. |
| `text` | `x`, `y`, `text` | Small label, e.g. "Gate", "Start", "x2". Keep it to a word or two. |

### Tips for clear diagrams

- Draw the moment that explains the drill, not every player's every movement. 1-3 arrows is usually right.
- Space players at least ~2m apart on a 15m grid and ~4m apart on a half or full pitch, or the dots overlap.
- Show queues as 2-3 players stacked behind a cone, not the whole squad.
- For two identical grids running side by side, draw one and say "x2" in the caption.
