# Assignment 2 - Advancing Front Hole Filling Plugin

**Student:** Truong Tri Dung - MITIU25208  
**Course:** Advanced Computer Graphics (IT516)

---

## Overview

A MeshLab C++ filter plugin that fills holes in 3D triangle meshes using the
**Advancing Front** method. The algorithm progressively grows triangles from
the hole boundary inward, selecting vertices by smallest angle and applying
three angle-based rules to produce well-shaped triangles.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Visual Studio | 2022+ (v18) with C++ Desktop workload | MSVC compiler |
| CMake | 3.18+ | Build system |
| Qt | 5.15.2 (msvc2019_64) | GUI framework |
| Ninja | (bundled with VS) | Build backend |

---

## Project Structure

```
Assignment 2/
  plugin/
    filter_advancing_front.h       # Plugin class declaration
    filter_advancing_front.cpp     # Algorithm implementation
    CMakeLists.txt                 # Build config
  BUILD_AND_RUN.md                 # This file
  Assignment2_MITIU25208_TruongTriDung.docx   # Report
```

The plugin source must be placed inside the MeshLab source tree at:
```
meshlab-src/src/meshlabplugins/filter_advancing_front/
```

---

## Build Instructions

### 1. Place plugin in MeshLab source tree

Copy the plugin source files into the MeshLab build tree:

```cmd
xcopy /E /I "Assignment 2\plugin" "meshlab-src\src\meshlabplugins\filter_advancing_front"
```

### 2. Register the plugin in CMakeLists

Edit `meshlab-src/src/CMakeLists.txt` and add this line in the `MESHLAB_PLUGINS` list
under the "Filter plugins" section:

```cmake
meshlabplugins/filter_advancing_front
```

### 3. First-time full build (if not done yet)

```cmd
cd meshlab-src
mkdir build2 && cd build2
cmake "..\src" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="C:\Qt\5.15.2\msvc2019_64"
cmake --build .
```

### 4. Rebuild only this plugin (after code changes)

Open a **Developer Command Prompt** or run `vcvarsall.bat`:

```cmd
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
cd /d "meshlab-src\build2"
cmake --build . --target filter_advancing_front
```

Build output: `build2/src/distrib/plugins/filter_advancing_front.dll`

---

## Run Instructions

### Launch MeshLab from build directory

```cmd
meshlab-src\build2\src\distrib\meshlab.exe
```

> **Important:** Always run MeshLab from the build directory to ensure ABI
> compatibility between the plugin DLL and MeshLab executable.

### Use the Plugin

1. **Import mesh:** `File > Import Mesh` -- load a mesh with holes (`.ply`, `.obj`)

2. **Open filter:** `Filters > Remeshing, Simplification and Reconstruction > Advancing Front Hole Filling`

3. **Parameters:**

   | Parameter | Default | Description |
   |-----------|---------|-------------|
   | Max Hole Size | 100 | Maximum boundary edges per hole |
   | Smoothing Iterations | 3 | Laplacian smoothing passes on filled patch |

4. **Click Apply.**

5. **Export result:** `File > Export Mesh As`

### Test Data

Test meshes with holes are available in `NFD-HoleFill/data/input/`:

- `sphere_small_hole.ply` -- simplest test case (1 hole, ~6 edges)
- `sphere_large_hole.ply` -- larger hole
- `sphere_two_holes.ply` -- 2 holes
- `torus_hole.ply` -- non-planar hole on torus

---

## Algorithm

### Pipeline

```
Input mesh with hole(s)
        |
   [Step 1] Hole Detection
        |   Find boundary edges (edges with exactly 1 adjacent face)
        |   and trace them into closed loops
        |
   [Step 2] Advancing Front Triangulation
        |   While front has > 3 vertices:
        |     - Find vertex with smallest angle between adjacent edges
        |     - Rule 1 (angle < 75 deg):  1 triangle, remove vertex
        |     - Rule 2 (75-135 deg):      1 new vertex, 2 triangles
        |     - Rule 3 (>= 135 deg):      2 new vertices, 3 triangles
        |   Close final triangle
        |
   [Step 3] Laplacian Smoothing
        |   Smooth interior vertices while holding boundary fixed
        |
   Output: filled mesh
```

### Angle-Based Rules

**Rule 1** -- Small angle (< 75 deg):
The gap is narrow. Simply connect the two neighboring boundary vertices
with a single triangle and remove the current vertex from the front.

**Rule 2** -- Medium angle (75 - 135 deg):
Create one new interior vertex at the angle bisector direction, at a
distance equal to the average boundary edge length. Form two triangles.

**Rule 3** -- Large angle (>= 135 deg):
Create two new interior vertices at 1/3 and 2/3 of the angle span.
Form three triangles. This prevents long, thin triangles.

### Comparison with NFD Hole Filling (Final Project)

| Aspect | Advancing Front | NFD Hole Filling |
|--------|----------------|-----------------|
| Triangulation | Angle-based rules | Ear clipping + refinement |
| Normal handling | Average normal | Cotangent heat diffusion |
| Displacement | None | Curvature-guided geodesic |
| Complexity | Simple (~300 LOC) | Complex (~650 LOC) |
| Dependencies | VCG only | VCG + Eigen |
| Quality | Good for simple holes | Better for complex geometry |

---

## Dependencies

- **VCG Library** -- mesh data structures, topology, normals
- **Qt 5** -- plugin interface (QObject, QAction, RichParameterList)
- No Eigen dependency (unlike NFD plugin)

---

## Important Notes

- **Ocf Components:** The plugin enables VCG Optional Component Framework (Ocf)
  for FF/VF adjacency before computing topology (`m.face.EnableFFAdjacency()` etc.)
- **Winding order:** A post-hoc check ensures face normals align with the
  average boundary normal
