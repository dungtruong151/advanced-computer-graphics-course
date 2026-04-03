# Advancing Front Hole Filling - MeshLab Plugin

## Prerequisites

- Visual Studio 2022+ with C++ Desktop workload
- CMake 3.18+
- Qt 5.15.2 (`C:\Qt\5.15.2\msvc2019_64`)
- MeshLab source tree (with VCG Library)

## Files

```
plugin/
  filter_advancing_front.h      # Class declaration
  filter_advancing_front.cpp    # Algorithm (~350 lines)
  CMakeLists.txt                # Build config
```

## Build

### 1. Copy plugin into MeshLab source tree

```cmd
xcopy /E /I "Assignment 2\plugin" "meshlab-src\src\meshlabplugins\filter_advancing_front"
```

### 2. Register in CMakeLists

Add to `meshlab-src/src/CMakeLists.txt` under `MESHLAB_PLUGINS`:

```cmake
meshlabplugins/filter_advancing_front
```

### 3. First-time full build

```cmd
cd meshlab-src
mkdir build2 && cd build2
cmake "..\src" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="C:\Qt\5.15.2\msvc2019_64"
cmake --build .
```

### 4. Rebuild plugin only

```cmd
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
cd /d "meshlab-src\build2"
cmake --build . --target filter_advancing_front
```

## Run

```cmd
meshlab-src\build2\src\distrib\meshlab.exe
```

1. `File > Import Mesh` -- load a `.ply` or `.obj` with holes
2. `Filters > Remeshing, Simplification and Reconstruction > Advancing Front Hole Filling`
3. Set parameters and click **Apply**
4. `File > Export Mesh As` to save result

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Max Hole Size | 100 | Max boundary edges per hole |
| Smoothing Iterations | 3 | Laplacian smoothing passes |

### Test meshes

Located in `NFD-HoleFill/data/input/`:
`sphere_small_hole.ply`, `sphere_large_hole.ply`, `sphere_two_holes.ply`,
`cylinder_side_hole.ply`, `torus_hole.ply`, `bunny_hole.ply`

## Note

Always run `meshlab.exe` from the build directory (`build2/src/distrib/`).
The plugin requires Ocf components enabled -- this is handled automatically.
