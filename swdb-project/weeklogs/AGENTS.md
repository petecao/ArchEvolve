- Weekly working logs

## Weekly progress (read before planning a deck)

1. `git log --since=<previous weeklog date> -- swdb-project`: commit and merge subjects name the efforts.
2. The current-state section of each `.scratch/*/map.md` that the log touches.
3. The previous week's `speaker-notes.md`: last week's next steps.

## Making Slides
- The target audience is my professor, an expert in compiler and computer architecture.

- **Core parts**: cover Yan-Ru's own core parts of the week, one section each.

- **Sparse**: one claim per slide, at most 55 body words; every detail goes to the speaker notes. Before export run `python3 weeklogs/tools/check_slide_words.py <project>/svg_output` (from `swdb-project/`).

- The slides must be easy to follow, better with illustration and example.

- Nice to include benchmark results and analysis.

- When illustrate concepts or features, it's good to mention the motivation, the problem, the solution, and the result.

- For benchmark, show the setup, the result, and the analysis.

- It's not bad to show our limitations and what we have learned from it.

- The smallest font is 15pt.

- Footers to specify the slide numbers.

- Make the slide styles consistent across folders.

- Everthing in the slides must be valid and verified. You cannot put fake things.

- Make it top-tier conference level.

- Do not use very big texts to highlight things.

- It's great to use simple examples to explain things.

- Do not show too much details as audience do not konw too much exact technical details about the codebase.

- Everything must be factual with real reference and actually implementaion

- Pay attention to logical and information flow. Logical change is continuous. Not flip flopping. 

- Before relying on a term, abbreviation, symbol, concept, or distinction, introduce enough information for the reader to understand it.

- Never make the reader work harder than necessary to understand your argument.

- Make the reader spend as little mental effort as possible to reconstruct your intended meaning. 

- Assume your reader is intelligent but attention-constrained. Make the path to understanding as short and frictionless as possible.


## Building a deck

Build each deck fresh with ppt-master. Its preview pages cannot bind a port in the sandbox:
confirm in chat and check pages with `rsvg-convert`.

## Visual style — UMich palette (use this for all decks under weeklyLogs/)

### Palette
- `blue: 00274C` — Michigan Blue, the primary color (header bar, primary box borders, body emphasis text)
- `maize: FFCB05` — Michigan Maize, the accent color (left edge stripe on header, callout banners, headline highlights)
- `blueIce: E8F0F9` — pale blue tint for soft backgrounds
- `blueLt: 4A6FA5` — muted blue for secondary accents
- `maizeLt: FFF4CC` — pale maize for callout-banner backgrounds
- `body: 1A1A1A` — body text
- `muted: 555555` — captions, italics, footer
- `border: BDC3C7` — neutral table/box borders
- `alt: F4F4F4` — alternating table row fill
- `codeBg: F4F4F4` — code-block background
- Status: `green: 27AE60` (wins) · `red: E74C3C` (losses, problems) · `amber: F39C12` (in-progress)
- Header text on blue bar: white `FFFFFF`