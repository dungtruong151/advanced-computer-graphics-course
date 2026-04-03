# NFD Hole Filling Plugin - Build and Run Guide

**Author:** Truong Tri Dung - MITIU25208  
**Course:** Advanced Computer Graphics (IT516)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Visual Studio | 2022+ (v18) with C++ Desktop workload | C++ compiler (MSVC) |
| CMake | 3.18+ | Build system |
| Qt | 5.15.2 (msvc2019_64) | GUI framework |
| Ninja | (bundled with VS) | Build backend |

Qt installation path: `C:\Qt\5.15.2\msvc2019_64`

---

## Project Structure

```
meshlab-src/
  src/
    meshlabplugins/
      filter_nfd_holefill/
        filter_nfd_holefill.h      # Plugin class declaration
        filter_nfd_holefill.cpp    # Algorithm implementation (6 steps)
        CMakeLists.txt             # Build config
    vcglib/                        # VCG Library (mesh data structures)
  build2/                          # Build output directory
    src/distrib/
      meshlab.exe                  # MeshLab executable
      plugins/
        filter_nfd_holefill.dll    # Compiled plugin
```

---

## Build Instructions

### First-time full build (MeshLab + all plugins)

```bash
cd meshlab-src
mkdir build2 && cd build2
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build .
```

### Rebuild only the NFD plugin (after code changes)

**Option 1 - Use the build script:**

```cmd
NFD-HoleFill\build_nfd.bat
```

This script:
1. Sets up VS x64 developer environment (`vcvarsall.bat`)
2. Runs `cmake --build . --target filter_nfd_holefill`

**Option 2 - Manual (from Developer Command Prompt):**

```cmd
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
cd "C:\Users\ACE\Desktop\iu\Advanced Computer Graphics\meshlab-src\build2"
cmake --build . --target filter_nfd_holefill
```

Build output: `build2/src/distrib/plugins/filter_nfd_holefill.dll`

---

## Run Instructions

### Run MeshLab from build directory (recommended)

```cmd
"C:\Users\ACE\Desktop\iu\Advanced Computer Graphics\meshlab-src\build2\src\distrib\meshlab.exe"
```

The plugin DLL is already in the correct `plugins/` folder relative to `meshlab.exe`.

### Using the Plugin

1. **Import mesh:** `File > Import Mesh` -- load a mesh with holes (`.ply`, `.obj`, `.stl`)

2. **Open filter:** `Filters > Remeshing, Simplification and Reconstruction > NFD Hole Filling`

3. **Configure parameters:**

   | Parameter | Default | Description |
   |-----------|---------|-------------|
   | Max Hole Size | 100 | Maximum boundary edges per hole. Larger holes are skipped. |
   | Diffusion Iterations | 50 | Number of heat equation iterations for normal diffusion. Higher = smoother. |
   | Diffusion Lambda | 0.5 | Diffusion speed coefficient (recommended: 0.1 -- 1.0). |
   | Smoothing Iterations | 3 | Laplacian smoothing passes on the filled patch. |

4. **Click Apply.**

5. **Export result:** `File > Export Mesh As` -- save to `.ply` or `.obj`.

---

## Test Data

Test meshes with pre-created holes are in `NFD-HoleFill/data/input/`:

| File | Description | Vertices | Faces | Holes |
|------|-------------|----------|-------|-------|
| `sphere_small_hole.ply` | Icosphere, 1 small hole (top) | 642 | 1,274 | 1 |
| `sphere_large_hole.ply` | Icosphere, 1 large hole (top) | 642 | 1,256 | 1 |
| `sphere_two_holes.ply` | Icosphere, holes at top and bottom | 642 | 1,268 | 2 |
| `cylinder_side_hole.ply` | Cylinder, hole on the side | 82 | 155 | 1 |
| `torus_hole.ply` | Torus, 1 hole at outer edge | 640 | 1,274 | 1 |
| `bunny_hole.ply` | Stanford Bunny, hole at top | 34,834 | 69,427 | 6 |

To regenerate test meshes: `python data/generate_test_meshes.py` (requires `trimesh`, `numpy`)

Start with `sphere_small_hole.ply` for the simplest test case.

---

## Algorithm Pipeline (6 Steps)

```
Input mesh with hole(s)
        |
   [Step 1] Hole Detection
        |   Trace boundary edge loops (edges belonging to exactly 1 face)
        |
   [Step 2] Boundary Analysis
        |   Compute vertex normals (area-weighted) and mean curvature
        |   (cotangent Laplacian) at each boundary vertex
        |
   [Step 3] Initial Triangulation
        |   Ear clipping on the 2D-projected boundary polygon,
        |   then refine large triangles by centroid subdivision
        |
   [Step 4] Normal Field Diffusion   <-- CORE NOVELTY
        |   Solve heat equation (I + lambda * L_cot) * n_new = n_old
        |   using Eigen SimplicialLDLT solver with Dirichlet boundary
        |   conditions (boundary normals fixed)
        |
   [Step 5] Curvature-Guided Displacement
        |   v' = v + H_avg * avgEdge * g(t) * n_diffused
        |   t = geodesic distance to boundary (Dijkstra), g(t) = 4t(1-t)
        |
   [Step 6] Laplacian Smoothing
        |   Uniform Laplacian with boundary vertices held fixed
        |
   Output: filled mesh
```

---

## Dependencies (linked automatically via CMake)

- **VCG Library** -- mesh data structures, topology, normals
- **Eigen 3** -- sparse matrix assembly, SimplicialLDLT solver
- **Qt 5** -- plugin interface (QObject, QAction, RichParameterList)

---

## Important Notes

- **Ocf Components:** The plugin enables VCG Optional Component Framework (Ocf) for
  FF/VF adjacency before computing topology. This is required because CMeshO uses
  `FFAdjOcf` and `VFAdjOcf` (optional, not statically allocated).

- **Build vs Install:** Always run `meshlab.exe` from the build directory
  (`build2/src/distrib/`) to ensure ABI compatibility between the plugin DLL and MeshLab.
  Copying the DLL to a separately installed MeshLab may cause crashes due to version mismatch.
