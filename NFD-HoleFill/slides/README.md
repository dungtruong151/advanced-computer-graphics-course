# Slides

`presentation.md` is a [Marp](https://marp.app/) slide deck — Markdown with a
YAML frontmatter. 13 slides total (12 content + Thank You), paced for ~10 minutes.

## Preview in VS Code

Install the **Marp for VS Code** extension (`marp-team.marp-vscode`), then
open `presentation.md`. Marp shows a live-preview pane on the right.

## Export to PDF / PPTX / HTML

With the Marp VS Code extension:

- `Ctrl+Shift+P` → `Marp: Export slide deck...` → choose format.

Or from the Marp CLI (`npm install -g @marp-team/marp-cli`):

```bash
marp presentation.md -o presentation.pdf
marp presentation.md -o presentation.pptx
marp presentation.md -o presentation.html
```

## Screenshots you need to capture

All images go in **this folder** (`NFD-HoleFill/slides/`) so Marp's relative
paths in `presentation.md` resolve cleanly. Use **PNG** (sharp wireframe).

### Required for slide 7 (Delaunay Edge Flipping)

Referenced in the deck as `delaunay_off.png` and `delaunay_on.png`:

| File | How to produce it |
|------|------------------|
| `delaunay_off.png` | Load `data/input/sphere_large_hole.ply` → `Filters > NFD Hole Filling` → **uncheck `Use Delaunay edge flipping`** → Apply → enable wireframe (`Render > Render Mode > Wireframe` or `W`) → zoom into the patch → screenshot just the patch region |
| `delaunay_on.png`  | Same mesh, same camera. Undo (Ctrl+Z) the previous fill, re-run the filter with **`Use Delaunay edge flipping` checked**, screenshot with the same zoom |

**Tips for a clean capture**
- Use the **same camera** for both shots so the comparison is fair. MeshLab's
  `View > Copy Camera` / `Paste Camera` works well, or just don't touch the
  viewport between captures.
- Turn wireframe on — the sliver difference is only visible with edges drawn.
- Crop to roughly 880×660 px before saving so the two side-by-side images
  at `width:440px` in the slide remain sharp.

### Required for slide 10 (Visual Results)

Referenced in the deck as `result_before.png` and `result_after.png`:

| File | How to produce it |
|------|------------------|
| `result_before.png` | Load any `data/input/<name>_hole.ply` (bunny is the most visually impressive) → frame the hole in the viewport → screenshot |
| `result_after.png`  | **Same camera.** Run `Filters > NFD Hole Filling` with defaults → screenshot |

Pick **one** model — the deck shows a single before/after pair, not a row
per model. Bunny or cow gives the most dramatic result; sphere_large is
the cleanest showcase of the patch quality.

**Same-camera trick:** in MeshLab use `View > Copy Shot` before filtering
and `View > Paste Shot` after so the camera is identical.

## Folder layout Marp expects

```
NFD-HoleFill/slides/
  presentation.md       # deck (references images by filename only)
  README.md             # this file
  delaunay_off.png      # <- slide 7, Delaunay off
  delaunay_on.png       # <- slide 7, Delaunay on
  result_before.png     # <- slide 10, mesh with hole
  result_after.png      # <- slide 10, after NFD fill
```
