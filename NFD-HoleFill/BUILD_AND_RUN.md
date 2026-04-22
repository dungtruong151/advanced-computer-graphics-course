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

Every test case in `NFD-HoleFill/data/input/` comes as a **pair**:

- `<name>_gt.ply` — the ground-truth mesh (no hole), used for evaluation
- `<name>_hole.ply` — the same mesh with faces removed to form a hole

| Pair | Description | Vertices | Faces | Holes |
|------|-------------|---------:|------:|------:|
| `sphere_small` | Icosphere, 1 small hole (top) | 642 | 1,274 | 1 |
| `sphere_large` | Icosphere, 1 large hole (top) | 642 | 1,256 | 1 |
| `sphere_two`   | Icosphere, holes at top and bottom | 642 | 1,268 | 2 |
| `cylinder_side`| Cylinder, hole on the side | 82 | 155 | 1 |
| `torus`        | Torus, 1 hole at outer edge | 640 | 1,274 | 1 |
| `bunny`        | Stanford Bunny, hole at top | 34,834 | 69,427 | 6 |
| `spot`         | Cow (watertight Spot substitute) | 2,903 | 5,774 | 1 |

To regenerate: `python data/generate_test_meshes.py`
(requires `trimesh`, `numpy`; also auto-downloads `stanford-bunny.obj` and
`cow.obj` from the `alecjacobson/common-3d-test-models` GitHub mirror.)

Start with `sphere_small_hole.ply` for the simplest test case.

---

## Evaluation

The proposal asks for three quantitative metrics: **Hausdorff Distance**,
**RMS Error**, and **Normal Deviation**. MeshLab ships a ready-made
`Hausdorff Distance` sampling filter that reports the first two directly,
so evaluation is done inside MeshLab — no extra scripts needed.

Workflow:

1. **Prepare GT/hole pairs** (only once):
   ```bash
   cd NFD-HoleFill/data
   python generate_test_meshes.py
   ```
   This writes `<name>_gt.ply` and `<name>_hole.ply` pairs to `data/input/`.

2. **Fill the hole with NFD** (per test case):
   - `File > Import Mesh` → `<name>_hole.ply`
   - `Filters > Remeshing, Simplification and Reconstruction > NFD Hole Filling`
   - `File > Export Mesh As...` → save as `<name>_filled.ply`

3. **Measure against ground truth** (per test case):
   - `File > Import Mesh` → `<name>_gt.ply` (add as a second layer)
   - `Filters > Sampling > Hausdorff Distance`
     - *Sampled Mesh*: the filled mesh (layer 0)
     - *Target Mesh*: the GT mesh (layer 1)
     - Enable *Sample Vertexes*, *Sample Edges*, *Sample Faces*
   - Read the reported **Max / Mean / RMS** distance from the log panel.
   - Repeat with Sampled and Target swapped and take the larger of the two
     max distances for the symmetric **Hausdorff** value.

4. **Normal deviation** (optional third metric):
   - After the Hausdorff filter, MeshLab attaches a per-vertex *quality*
     value (distance). For normal deviation, use
     `Filters > Quality Measures and Computations > Per Vertex Quality Function`
     with an expression comparing vertex normals against the closest-point
     normals, or just report the **max angle** between any patch face
     normal and the GT face normal at its projected point (can be read
     off via `Render > Show Normal` on both layers overlaid).

Record the numbers in a results table of your report:

| Model | Hausdorff (max) | RMS | Normal dev (max) |
|-------|-----------------|-----|------------------|
| sphere_small | ... | ... | ... |
| ... | ... | ... | ... |

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
