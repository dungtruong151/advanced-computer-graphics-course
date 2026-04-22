# Slides

`presentation.md` is a [Marp](https://marp.app/) slide deck — Markdown with a
YAML frontmatter. 13 slides, paced for ~10 minutes.

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

### Optional for slide 10 (Visual Results)

Not referenced by the deck yet — add them later if you want to replace the
plain table with images. Suggested naming if you do:

```
sphere_small_before.png    sphere_small_after.png
sphere_large_before.png    sphere_large_after.png
torus_before.png           torus_after.png
bunny_before.png           bunny_after.png
cow_before.png             cow_after.png
```

Edit slide 10 to embed them as e.g.
```markdown
![width:400px](bunny_before.png) ![width:400px](bunny_after.png)
```

## Folder layout Marp expects

```
NFD-HoleFill/slides/
  presentation.md       # deck (references images by filename only)
  README.md             # this file
  delaunay_off.png      # <- drop here
  delaunay_on.png       # <- drop here
  ...any other screenshots you add
```
