# NFD Hole Filling --- Source Code

**Course:** Advanced Computer Graphics
**Author:** Truong Tri Dung
**Student ID:** MITIU25208

This folder contains the full C++ source code for the NFD Hole Filling plugin,
together with the test dataset and the build helper scripts.

---

## Contents

```
demo/
├── README.md                      This file
├── plugin/
│   ├── filter_nfd_holefill.h      Class declaration (~70 lines)
│   ├── filter_nfd_holefill.cpp    Algorithm implementation (~1245 lines)
│   └── CMakeLists.txt             Plugin build configuration
├── data/
│   ├── generate_test_meshes.py    Script that produces the test set
│   └── input/                     Six test models (ground truth + hole pairs)
├── build_nfd.bat                  Incremental rebuild of just the plugin
└── build_meshlab.bat              Full rebuild of MeshLab + plugin
```

The plugin source is the `filter_nfd_holefill` MeshLab module. The two `.bat`
files automate common Windows build steps; the cross-platform CMake commands
they wrap are listed below if you prefer to build from a regular shell.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Visual Studio 2022 | 17.5+ | Install the **Desktop development with C++** workload |
| CMake | 3.18 or later | Bundled with Visual Studio is fine |
| Qt | 5.15.2 (`msvc2019_64`) | Default install path: `C:\Qt\5.15.2\msvc2019_64` |
| Ninja | bundled with VS | Used as the CMake generator |
| Python | 3.8+ | Optional, only needed to regenerate the test meshes |
| MeshLab source | latest | Cloned separately, see below |

The Python script in `data/` requires `numpy` and `trimesh`. These are not
needed to run the plugin --- the test data already in `data/input/` is enough
for evaluation.

---

## Setup

### 1. Clone the MeshLab source tree

This plugin is designed to be built as part of MeshLab's CMake project. Clone
MeshLab somewhere convenient:

```bash
git clone --recursive https://github.com/cnr-isti-vclab/meshlab.git meshlab-src
```

The `--recursive` flag pulls in VCGlib as a sub-module, which the plugin
depends on for mesh data structures and topology operations.

### 2. Drop the plugin into MeshLab's plugin tree

Copy `plugin/` into MeshLab's plugin directory under a new folder named
`filter_nfd_holefill`:

```
meshlab-src/
└── src/
    └── meshlabplugins/
        └── filter_nfd_holefill/        <-- create this folder
            ├── filter_nfd_holefill.h
            ├── filter_nfd_holefill.cpp
            └── CMakeLists.txt
```

### 3. Register the plugin with MeshLab's build system

Open `meshlab-src/src/meshlabplugins/CMakeLists.txt` and add a single line so
the plugin is picked up by the top-level build:

```cmake
add_subdirectory(filter_nfd_holefill)
```

### 4. Verify Qt is reachable

The plugin's `CMakeLists.txt` expects Qt 5.15.2 at the standard MSVC path. If
your install lives elsewhere, set the environment variable
`CMAKE_PREFIX_PATH=C:\path\to\Qt\5.15.2\msvc2019_64` before running CMake.

---

## Build

### Full build (one-time)

From a regular `cmd` or PowerShell with Visual Studio's developer environment
(`vcvarsall.bat x64`) loaded:

```bash
cd meshlab-src
mkdir build2
cd build2
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build .
```

The first build takes 15--30 minutes on a modern laptop because it compiles
all of MeshLab and its plugins.

### Incremental rebuild of just the plugin

After a full build, when you change only the plugin source:

```bash
cd meshlab-src/build2
cmake --build . --target filter_nfd_holefill
```

This finishes in a few seconds.

### Helper batch scripts

The two `.bat` files in this folder automate the above on Windows:

* `build_nfd.bat` --- runs `vcvarsall.bat x64` and then
  `cmake --build . --target filter_nfd_holefill` in the assumed `build2/`
  directory. Use this for incremental rebuilds.
* `build_meshlab.bat` --- runs the full build from scratch.

Both scripts assume the standard layout described above; edit the paths near
the top if your tree differs.

---

## Running the plugin in MeshLab

1. Launch MeshLab from the build tree:

   ```
   meshlab-src\build2\src\distrib\meshlab.exe
   ```

   Do **not** copy the compiled DLL into a separately installed MeshLab. The
   ABI between the development build and a release build will not match and
   the host process can crash at plugin load time.

2. Open one of the test meshes:

   ```
   File > Import Mesh
   ```

   Pick any `*_hole.ply` from `data/input/`. Recommended starting point:
   `sphere_small_hole.ply`.

3. Run the filter:

   ```
   Filters > Remeshing, Simplification and Reconstruction > NFD Hole Filling
   ```

4. Adjust parameters (see below) and click **Apply**.

5. (Optional) Export the filled mesh:

   ```
   File > Export Mesh As...   ->   *.ply
   ```

---

## Filter parameters

| Parameter | Default | Effect |
|---|---:|---|
| `MaxHoleSize` | 100 | Skip boundary loops longer than this many edges |
| `DiffusionIterations` | 50 | Implicit-Euler iterations in Stage 4 |
| `DiffusionLambda` | 0.5 | Time step of the heat equation |
| `SmoothingIterations` | 3 | Stage 5 uniform Laplacian iterations |
| `RefinementFactor` | 1.0 | Triangle size relative to boundary edge length |
| `CurvatureStrength` | 1.0 | Multiplier on the spherical-cap dome height |
| `UseDelaunayFlipping` | on | Toggle the Delaunay flip pass (off for demos) |

For most meshes the default values produce a usable result. The two
parameters that most often need adjustment are `CurvatureStrength` (lower if
the patch overshoots, higher if it looks too flat) and `RefinementFactor`
(smaller for denser patches on large holes).

---

## Test data

The folder `data/input/` contains six test models in PLY format. Each model
appears as a pair: `*_gt.ply` is the watertight ground truth, and
`*_hole.ply` is the same mesh with one or more holes cut out. The pairs are:

| Model | Description |
|---|---|
| `sphere_small` | Icosphere with a small hole |
| `sphere_large` | Icosphere with a larger hole |
| `sphere_two`   | Icosphere with two separate holes |
| `cylinder_side`| Hole on the side of a cylinder |
| `torus`        | Hole on a curved section of a torus |
| `cow`          | Watertight cow with a large cut-out |
| `bunny`        | Stanford Bunny with six holes |

To regenerate the test set from scratch:

```bash
cd data
python generate_test_meshes.py
```

The script uses fixed random seeds, so the output is reproducible.

---

## Evaluating against the ground truth

To reproduce the Hausdorff measurements reported in Chapter 6:

1. Open both the filled mesh and the ground-truth mesh in the same MeshLab
   session.
2. Run `Filters > Sampling > Hausdorff Distance` twice, once with the filled
   mesh as the sampled mesh, once with the ground truth as the sampled mesh.
3. Read the per-direction `min`, `max`, `mean`, and `RMS` values from the
   filter dialog or the MeshLab log.

The symmetric Hausdorff distance is `max(forward.max, reverse.max)`; the
percentages reported in the table are relative to the ground-truth bounding-box
diagonal that MeshLab prints in the same log.

---

## Code layout

The full pipeline lives in a single `.cpp` file, organised in pipeline order:

| Lines | Section |
|---:|---|
| 1--170 | Plugin registration boilerplate (Qt macros, filter metadata, parameter list) |
| 170--320 | `applyFilter` driver |
| 320--395 | Stage 1: `detectHoles` |
| 395--460 | Stage 2: `computeBoundaryInfo` |
| 460--850 | Stage 3: `triangulatePatch` (longest function: ear clipping + Delaunay + refine) |
| 850--990 | Stage 4: `diffuseNormalField` |
| 990--1145 | Stage 6: `displaceVertices` (includes the Taubin pass) |
| 1145--1175 | Stage 5: `smoothPatch` |
| 1175--end | Stage 7: `mergePatchIntoMesh` |

Reading top to bottom matches the order of operations described in Chapter 4
of the report. There is no global state, so the plugin is thread-safe per
mesh, although MeshLab itself does not parallelise filter execution across
meshes.

---

## Troubleshooting

**The plugin does not appear in the Filters menu.** Check that the DLL was
built into `build2/src/distrib/plugins/filter_nfd_holefill.dll` and that
MeshLab was launched from the same build tree. Plugins from a different build
or install will be skipped at startup.

**MeshLab crashes when the filter is invoked.** Most likely a non-manifold
input. Run `Filters > Cleaning and Repairing > Repair non-manifold edges`
before NFD.

**The patch overshoots and looks like a raised bump.** Lower
`CurvatureStrength` to 0.7 or 0.6. This is the "overshoot" failure mode
described in the report.

**The patch does not fully cover the hole.** Decrease `RefinementFactor` (try
0.7, then 0.5) and/or increase `DiffusionIterations` (try 100). This usually
trades runtime for coverage on large holes.

**CMake cannot find Qt.** Set `CMAKE_PREFIX_PATH` to the Qt install root
before re-running `cmake ..`.

---

## Contact

Truong Tri Dung --- MITIU25208 --- School of Computer Science and Engineering,
International University, VNU-HCM.
