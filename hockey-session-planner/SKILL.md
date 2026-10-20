---
name: hockey-session-planner
description: Turn a coach's rough voice-memo or typed notes into a complete field hockey training session plan, delivered as a printable PDF with drill diagrams (pitch layouts showing players, cones, passes, runs). Covers three teams - the men's 1st team, the ladies' 1st team, and the minis (U5-U10) - using the coach's fixed 75-minute session structure (10-min warm-up, 15-min technical, 15-min small-sided, 15-min live game-scenario, then a full game). Use this whenever the user mentions a hockey session, training plan, practice plan, drills, a theme to coach (e.g. pressing, tackling, outletting, 3D skills, penalty corners, eliminations), or pastes/dictates notes about what they want to work on at training - even if they don't say "session plan" or "PDF".
---

# Hockey Session Planner

The user is a field hockey coach who runs three teams on different nights. They'll send you a messy memo, often dictated by voice, so expect run-on sentences, repetition and transcription errors such as "rondo" coming through as "round o", or "eliminations" as "illuminations". Your job is to turn that memo into a session plan they can print and take to the pitch. The plan follows their fixed structure and has a clear diagram for every drill.

## Step 1 - Work out what they're asking for

Extract the following from the memo:

| Field | Notes |
|---|---|
| **Team** | Men's 1st team, Ladies' 1st team, or Minis (and which age band, U5-U10). This decides which reference file you read. |
| **Theme(s)** | What the session coaches. If there are two themes, find the link between them (e.g. "pressing" + "transition" = win it, then go). |
| **Criteria / constraints** | Numbers, GKs, space (full/half/quarter pitch), session length, kit, anything to avoid, players returning from injury, match coming up. |
| **Date / opposition** | Optional. Use it if given. |

Next, read the profile for that team, which holds defaults and what works for that group:
- Men's 1st team → `references/team_mens.md`
- Ladies' 1st team → `references/team_ladies.md`
- Minis U5-U10 → `references/team_minis.md`

**If the team isn't clear, ask one short question** ("Which team is this for: men's, ladies or minis?") before building anything, because the team changes everything. For any other gap, use the team-profile default and list your assumptions in one line when you hand over the PDF. Don't interrogate the coach. They want a plan, not a form to fill in.

## Step 2 - Design the session using the coach's structure

This structure is the coach's own and is non-negotiable. Every block should visibly build on the one before it, so the theme grows through the session rather than appearing in disconnected chunks.

| # | Block | Time | Purpose |
|---|---|---|---|
| 1 | **Warm-up** | 10 min | Raise heart rate *and* loosely introduce the theme, e.g. a rondo, a passing pattern or a possession box carrying the day's skill. It's a warm-up, not a lecture: it should be moving within a minute. |
| 2 | **Technical** | 15 min | Fully introduce the skill. A technical walkthrough: clear model, unopposed → semi-opposed, lots of reps, specific coaching points. |
| 3 | **Small-sided** | 15 min | Put the skill into a game-type scenario, e.g. overloads (3v2, 4v3), directional games, or a small-sided game with a condition that rewards the skill. |
| 4 | **Live game scenario** | 15 min | Small-sided game played as if it's live, with as few people as possible standing around. Use multiple pitches, rolling subs, quick restarts and waves. |
| 5 | **Game** | 20 min | Full game where they apply the principles. Add one light condition or "focus" linked to the theme, and say what the coach watches for. |

Total: 75 minutes. If the coach gives a different length, keep the 10-minute warm-up and the 20-minute game, and scale blocks 2-4 evenly. For the minis, the profile explains how to keep the same structure while making it age-appropriate.

**Keeping people active is a big deal for this coach.** For every block, work out how many players are actually involved at once. If more than 2-3 are queuing, redesign the drill: run two grids, add a second ball, use waves, or turn the queue into a working role such as feeder or recovering defender. Make it explicit in `activity_notes`.

Each drill needs:
- **Organisation / set-up**: area size in metres, numbers, kit and bibs, so another coach could set it up without asking.
- **How it works**: 3-5 short bullet steps, in the order things happen.
- **Link to theme**: one line on why this block matters for today's theme.
- **Coaching points**: 3-4 specific, observable points. Use "Receive on the open stick side, body side-on to see the next pass", not "good receiving".
- **Progressions and regressions**: at least one of each, so the coach can adapt on the fly. A `step` block (Space / Task / Equipment / People, the STEP framework England Hockey coaches use) is a useful way to show adaptations, and you can include it where it helps.
- **Questions to ask** (optional): 1-2 guided-discovery questions. These suit adults especially.

The plan also needs: 2-3 session objectives, a few short key messages or trigger words the coach can shout, and safety notes where relevant (GK kit, aerials, gum shields).

## Step 3 - Draw the diagrams

Every drill in blocks 1-4 gets a diagram. The final game can have one if a condition needs explaining, such as scoring zones; otherwise leave it out. Diagrams are what make the plan usable at the pitch, so take care over them:

- Pick the right area: `grid` (give the length and width in metres) for warm-ups and technical drills, `quarter`/`23`, `half` or `full` for game-related work.
- Place players in realistic positions using metre coordinates. x runs along the length, y across the width, and (0,0) is the bottom-left corner. For `half`, `23` and `quarter`, the goal is on the right-hand side.
- Show the **key action only**: the first 1-3 passes, runs and dribbles that explain the drill. A diagram full of arrows is harder to read than one with none.
- Use the team colours consistently: blue (`A`) is usually the team practising the theme and red (`B`) is the opposition.
- Add a one-line `caption` that says what the picture shows.

The full JSON format, with every element type, is in `references/plan_schema.md`. Read it before writing the plan JSON. `examples/mens_pressing.json` is a complete worked example and a good model for the level of detail.

## Step 4 - Build the PDF

1. Write the plan as JSON (see `references/plan_schema.md`).
2. Run:
   ```bash
   python scripts/build_session_pdf.py plan.json "<output-path>/<Team>_<Theme>_session_plan.pdf"
   ```
   This needs `reportlab` (`pip install reportlab` if it isn't installed).
3. **Check the diagrams.** If you can render the pages to images (e.g. `pdftoppm -png -r 70 file.pdf page`), look at them. Check that players aren't sitting on top of each other, arrows go where you meant, and nothing is outside the playing area. Fix the coordinates and rebuild if needed. One check is enough.
4. Give the user the PDF. In chat, keep it short: a 3-5 line summary of the session flow, plus any assumptions you made (e.g. "Assumed 16 + 2 GKs and half a pitch for blocks 2-3"). The detail belongs in the PDF.

## When the coach gives feedback

If they say something like "too much standing around in block 3" or "the warm-up is too complicated for U6s", fix it and regenerate the PDF. If the feedback reveals a lasting preference (e.g. "we never have more than 12 men on a Tuesday"), suggest adding it to the relevant team profile so future plans get it right first time.
