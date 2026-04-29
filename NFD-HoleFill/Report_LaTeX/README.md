# NFD Hole Filling — Academic Report (LaTeX)

This directory contains the LaTeX source of the academic report for the IT516
Advanced Computer Graphics project, modelled on the style of the PhD proposal
template at `iu/Thesis/NCS/PhD_Proposal_LaTeX`.

## Directory layout

```
Report_LaTeX/
├── main.tex                      Title page, TOC, ack, abstract, appendix, bibliography include
├── references.bib                BibLaTeX database
├── chapters/
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── preliminaries.tex
│   ├── methodology.tex
│   ├── implementation.tex
│   ├── results.tex
│   ├── discussion.tex
│   └── conclusion.tex
├── figures/                      Result figures (copied from slides/)
│   ├── delaunay_off.png
│   ├── delaunay_on.png
│   ├── result_before.png
│   └── result_after.png
└── images/                       Title-page assets
    └── logo-vector-IU-01.png
```

## Build instructions

The document uses `fontspec` (requires Times New Roman on the system) and
`biblatex` with the `biber` backend. Two-pass build:

```bash
# Requires: xelatex (or lualatex) + biber + Times New Roman font

xelatex main.tex
biber   main
xelatex main.tex
xelatex main.tex    # final pass resolves refs + TOC
```

Or with `latexmk`:

```bash
latexmk -xelatex -bibtex main.tex
```

The output is `main.pdf`.

## Figures

All explanatory diagrams (cotangent weights, pipeline overview, ear clipping,
Delaunay flip, centroid refinement, heat diffusion, spherical cap, Dijkstra
distance, profile comparison, Taubin effect) are drawn **inline with TikZ**
and require no external image files — they compile straight from the `.tex`
sources.

Screenshot-based figures (MeshLab UI, per-model before/after renders,
Hausdorff heatmaps, failure cases) should be placed in `figures/` and referenced
by `\includegraphics{figures/<name>.png}`. See the parent-project figure
checklist for the complete capture list.

## Notes

- The font is set to Times New Roman via `\setmainfont{Times New Roman}`.
  If building on a system without this font, substitute in `main.tex`.
- The color scheme (`ackblue` = `#365f91`) matches the PhD-proposal template
  exactly, so the visual style is consistent across both documents.
- Figures are copied from `../slides/` at report-creation time; to refresh,
  rerun the copy step in the parent-project build pipeline.

## Chapter summary

| Chapter | Topic |
|---|---|
| 1 Introduction | Motivation, problem statement, contributions |
| 2 Related Work | Classical, variational, normal-based methods |
| 3 Preliminaries | Discrete Laplace-Beltrami, heat equation, implicit Euler, Taubin |
| 4 Methodology | Seven-stage pipeline with full mathematical formulation |
| 5 Implementation | MeshLab plugin architecture, VCGlib, Eigen, build system |
| 6 Results | Hausdorff evaluation, MeshLab comparison, timings |
| 7 Discussion | Strengths, limitations, four failure modes |
| 8 Conclusion | Summary and future-work roadmap |
