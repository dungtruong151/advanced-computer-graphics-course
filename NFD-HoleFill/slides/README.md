# Slides

`presentation.md` is a [Marp](https://marp.app/) slide deck — Markdown with a
YAML frontmatter. 13 slides, paced for ~10 minutes.

## Preview in VS Code

Install the **Marp for VS Code** extension (`marp-team.marp-vscode`), then
open `presentation.md`. Marp shows a live-preview pane on the right.

## Export to PDF / PPTX / HTML

With the Marp VS Code extension:

- `Ctrl+Shift+P` → `Marp: Export slide deck...` → choose format.

Or from the Marp CLI (npm install -g @marp-team/marp-cli):

```bash
marp presentation.md -o presentation.pdf
marp presentation.md -o presentation.pptx
marp presentation.md -o presentation.html
```

## Inserting screenshots

Slide 9 (*Visual Results*) has a placeholder HTML comment where before/after
screenshots go. Drop the images in this folder and reference them as:

```markdown
![width:400px](sphere_before.png) ![width:400px](sphere_after.png)
```

Good shots to capture in MeshLab:

- `sphere_small_hole.ply` → NFD → filled  (simplest, good opener)
- `bunny_hole.ply` → NFD → filled  (shows 6-holes case)
- `cow_hole.ply` → NFD → filled  (second non-sphere model)
- Close-up of one patch with wireframe on (`Render > Wire Frame`) to
  demonstrate triangulation + smoothing.
