# Slides

`presentation.md` is a [Marp](https://marp.app/) slide deck — Markdown with a
YAML frontmatter. 13 slides total (12 content + Thank You), paced for ~10 minutes.

## Preview in VS Code

Install the **Marp for VS Code** extension (`marp-team.marp-vscode`), then
open `presentation.md`. Marp shows a live-preview pane on the right.

## Export to PDF / PPTX / HTML

The deck uses `html: true` in its frontmatter (needed for the big
Thank-You slide and the image-pair layout). Pass `--html` to the CLI or
enable **"Enable HTML"** in the VS Code Marp extension so those elements
survive export.

### Marp CLI (recommended — no global install needed)

From `NFD-HoleFill/slides/`:

```bash
# PPTX (PowerPoint)
npx --yes @marp-team/marp-cli@latest presentation.md -o presentation.pptx --html --allow-local-files

# PDF
npx --yes @marp-team/marp-cli@latest presentation.md -o presentation.pdf --html --allow-local-files

# Standalone HTML
npx --yes @marp-team/marp-cli@latest presentation.md -o presentation.html --html --allow-local-files
```

- `--html` keeps the raw HTML (flex layouts, centered headings).
- `--allow-local-files` lets Marp pull in the PNGs from this folder.

Global install (optional, skips `npx` prompt each run):

```bash
npm install -g @marp-team/marp-cli
marp presentation.md -o presentation.pptx --html --allow-local-files
```

### VS Code Marp extension

1. Install `marp-team.marp-vscode`.
2. Settings → search **Marp: Enable HTML** → tick it.
3. Open `presentation.md`.
4. `Ctrl+Shift+P` → `Marp: Export slide deck...` → choose PowerPoint Document (.pptx).

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
