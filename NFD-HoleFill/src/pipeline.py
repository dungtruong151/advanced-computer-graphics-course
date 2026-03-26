"""
NFD-HoleFill: Normal Field Diffusion-Guided Hole Filling

Main pipeline combining all steps:
1. Hole Detection
2. Initial Triangulation
3. Boundary Analysis
4. Normal Field Diffusion
5. Curvature-Guided Displacement
6. Local Smoothing
"""

import numpy as np
import trimesh
import time

from hole_detection import detect_holes
from triangulation import triangulate_hole
from boundary_analysis import analyze_boundary, compute_vertex_normals
from normal_diffusion import diffuse_normal_field
from displacement import displace_vertices, laplacian_smooth_patch


class NFDHoleFiller:
    """Normal Field Diffusion-Guided Hole Filling algorithm."""

    def __init__(self, lambda_param=1.0, dt=0.1, diffusion_iterations=50,
                 displacement_scale=1.0, smooth_iterations=3, smooth_alpha=0.5):
        """
        Args:
            lambda_param: diffusion coefficient for normal propagation
            dt: time step for diffusion
            diffusion_iterations: max iterations for normal diffusion
            displacement_scale: scale factor for vertex displacement
            smooth_iterations: Laplacian smoothing iterations
            smooth_alpha: Laplacian smoothing weight
        """
        self.lambda_param = lambda_param
        self.dt = dt
        self.diffusion_iterations = diffusion_iterations
        self.displacement_scale = displacement_scale
        self.smooth_iterations = smooth_iterations
        self.smooth_alpha = smooth_alpha

    def fill_holes(self, mesh, hole_indices=None):
        """
        Fill holes in a mesh using the NFD method.

        Args:
            mesh: trimesh.Trimesh object
            hole_indices: list of hole indices to fill (None = fill all)

        Returns:
            filled_mesh: new trimesh.Trimesh with holes filled
            stats: dict with statistics about the filling process
        """
        start_time = time.time()
        stats = {
            'holes_detected': 0,
            'holes_filled': 0,
            'vertices_added': 0,
            'faces_added': 0,
            'time_seconds': 0
        }

        print("=" * 60)
        print("NFD-HoleFill: Normal Field Diffusion-Guided Hole Filling")
        print("=" * 60)

        # Step 1: Hole Detection
        print("\n[Step 1] Hole Detection")
        loops = detect_holes(mesh)

        if not loops:
            print("No holes to fill.")
            return mesh.copy(), stats

        stats['holes_detected'] = len(loops)

        # Select which holes to fill
        if hole_indices is not None:
            loops = [loops[i] for i in hole_indices if i < len(loops)]

        # Work with copies
        vertices = mesh.vertices.copy()
        faces = list(map(tuple, mesh.faces))

        total_new_faces = []

        for hole_idx, loop in enumerate(loops):
            print(f"\n--- Filling Hole {hole_idx} ({len(loop)} boundary vertices) ---")

            # Step 2: Initial Triangulation
            print(f"\n[Step 2] Initial Triangulation")
            new_vertices, patch_faces, interior_indices, boundary_indices = \
                triangulate_hole(vertices, loop)

            if not patch_faces:
                print(f"  WARNING: Could not triangulate hole {hole_idx}, skipping.")
                continue

            # Update vertex array if new vertices were added
            if len(new_vertices) > len(vertices):
                vertices = new_vertices

            # Step 3: Boundary Analysis
            print(f"\n[Step 3] Boundary Analysis")
            boundary_normals, boundary_curvatures, avg_curvature = \
                analyze_boundary(vertices, faces, boundary_indices)

            # Step 4: Normal Field Diffusion
            print(f"\n[Step 4] Normal Field Diffusion")
            if interior_indices:
                diffused_normals = diffuse_normal_field(
                    vertices, patch_faces,
                    boundary_indices, boundary_normals,
                    interior_indices,
                    lambda_param=self.lambda_param,
                    dt=self.dt,
                    n_iterations=self.diffusion_iterations
                )
            else:
                # No interior vertices - use boundary normals for all patch vertices
                # Compute normals for non-boundary patch vertices from patch geometry
                diffused_normals = dict(boundary_normals)
                patch_vertex_set = set()
                for f in patch_faces:
                    patch_vertex_set.update(f)
                patch_interior = patch_vertex_set - set(boundary_indices)

                if patch_interior:
                    # For vertices that are in patch but not boundary and not interior
                    # (shouldn't happen normally, but handle gracefully)
                    all_normals = compute_vertex_normals(vertices, faces)
                    for vi in patch_interior:
                        if vi < len(all_normals):
                            diffused_normals[vi] = all_normals[vi]

            # Step 5: Curvature-Guided Displacement
            print(f"\n[Step 5] Curvature-Guided Displacement")
            if interior_indices:
                vertices = displace_vertices(
                    vertices, patch_faces,
                    boundary_indices, interior_indices,
                    diffused_normals, boundary_curvatures, avg_curvature,
                    displacement_scale=self.displacement_scale
                )
            else:
                print("  No interior vertices to displace (small hole).")

            # Step 6: Local Smoothing
            print(f"\n[Step 6] Local Smoothing")
            if interior_indices:
                vertices = laplacian_smooth_patch(
                    vertices, patch_faces,
                    boundary_indices, interior_indices,
                    n_iterations=self.smooth_iterations,
                    alpha=self.smooth_alpha
                )
            else:
                print("  No interior vertices to smooth (small hole).")

            # Collect new faces
            total_new_faces.extend(patch_faces)
            stats['holes_filled'] += 1

        # Build final mesh
        all_faces = faces + total_new_faces
        filled_mesh = trimesh.Trimesh(
            vertices=vertices,
            faces=np.array(all_faces),
            process=False
        )

        # Clean up
        mask = filled_mesh.nondegenerate_faces()
        filled_mesh.update_faces(mask)
        filled_mesh.remove_unreferenced_vertices()

        stats['vertices_added'] = len(vertices) - len(mesh.vertices)
        stats['faces_added'] = len(filled_mesh.faces) - len(mesh.faces)
        stats['time_seconds'] = time.time() - start_time

        print(f"\n{'=' * 60}")
        print(f"DONE!")
        print(f"  Holes filled: {stats['holes_filled']}/{stats['holes_detected']}")
        print(f"  Vertices added: {stats['vertices_added']}")
        print(f"  Faces added: {stats['faces_added']}")
        print(f"  Time: {stats['time_seconds']:.2f}s")
        print(f"{'=' * 60}")

        return filled_mesh, stats


def fill_mesh_holes(mesh, **kwargs):
    """Convenience function to fill holes in a mesh."""
    filler = NFDHoleFiller(**kwargs)
    return filler.fill_holes(mesh)
