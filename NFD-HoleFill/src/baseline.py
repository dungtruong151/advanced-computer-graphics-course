"""
Baseline: Simple Flat Hole Filling + Laplacian Smoothing
Used for comparison with our NFD method.
"""

import numpy as np
import trimesh
import time

from hole_detection import detect_holes
from triangulation import triangulate_hole
from displacement import laplacian_smooth_patch


def flat_fill_with_smoothing(mesh, smooth_iterations=5, smooth_alpha=0.5):
    """
    Baseline method: fill holes with flat triangulation,
    then apply Laplacian smoothing.

    This is essentially what basic Meshlab hole filling does.
    """
    start_time = time.time()

    print("=" * 60)
    print("Baseline: Flat Fill + Laplacian Smoothing")
    print("=" * 60)

    # Detect holes
    loops = detect_holes(mesh)
    if not loops:
        return mesh.copy(), {}

    vertices = mesh.vertices.copy()
    faces = list(map(tuple, mesh.faces))
    total_new_faces = []

    for hole_idx, loop in enumerate(loops):
        print(f"\n--- Filling Hole {hole_idx} ({len(loop)} boundary vertices) ---")

        # Triangulate (same as NFD Step 2)
        new_vertices, patch_faces, interior_indices, boundary_indices = \
            triangulate_hole(vertices, loop)

        if not patch_faces:
            continue

        if len(new_vertices) > len(vertices):
            vertices = new_vertices

        # Only Laplacian smoothing (no normal diffusion, no curvature displacement)
        if interior_indices:
            vertices = laplacian_smooth_patch(
                vertices, patch_faces,
                boundary_indices, interior_indices,
                n_iterations=smooth_iterations,
                alpha=smooth_alpha
            )

        total_new_faces.extend(patch_faces)

    all_faces = faces + total_new_faces
    filled_mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=np.array(all_faces),
        process=False
    )
    mask = filled_mesh.nondegenerate_faces()
    filled_mesh.update_faces(mask)
    filled_mesh.remove_unreferenced_vertices()

    elapsed = time.time() - start_time
    print(f"\nBaseline done in {elapsed:.2f}s")

    return filled_mesh, {'time_seconds': elapsed}
