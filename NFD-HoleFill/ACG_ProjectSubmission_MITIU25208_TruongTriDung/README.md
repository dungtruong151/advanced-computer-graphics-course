# NFD Hole Filling --- Project Submission

**Course:** Advanced Computer Graphics
**Author:** Truong Tri Dung
**Student ID:** MITIU25208
**Submission date:** April 2026

---

## Contents of this folder

| File / folder | Description |
|---|---|
| `report.pdf` | Final report (37 pages) |
| `slide.pptx` | Presentation slides |
| `demo/` | Plugin source code, test data, build scripts |
| `demo/README.md` | Build and run instructions |

---

## Overview

This project implements a **Normal Field Diffusion (NFD)** hole-filling algorithm
as a native C++ plugin for MeshLab. Unlike the built-in `Close Holes` filter,
which produces flat patches, NFD uses a discrete heat equation to propagate
boundary normals into the patch interior, then displaces interior vertices
along the diffused field with an amplitude derived from a spherical-cap fit
to the boundary. The result is a curved patch that follows the surrounding
surface.

See the report (`report.pdf`) for the full description
of the seven-stage pipeline, the mathematical background, and the experimental
evaluation (six test meshes, symmetric Hausdorff distance against ground truth,
comparison with MeshLab `Close Holes`).

---

## Quick start

To build and run the plugin, please follow the instructions in
`demo/README.md`. A summary:

1. Install Visual Studio 2022 (with the C++ Desktop workload), CMake 3.18+,
   Qt 5.15.2 (`msvc2019_64`), and clone the MeshLab source tree.
2. Place the `plugin/` subfolder inside MeshLab's `src/meshlabplugins/`
   directory and add it to MeshLab's plugin list in `CMakeLists.txt`.
3. Build MeshLab once with `cmake --build .` from a Ninja-configured build
   directory.
4. Launch MeshLab from the build tree, load any `*_hole.ply` from
   `data/input/`, and run `Filters > Remeshing, Simplification and
   Reconstruction > NFD Hole Filling`.
