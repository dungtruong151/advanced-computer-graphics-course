"""
Mesh I/O utilities using trimesh.
Load and save meshes in common formats (PLY, OBJ, STL).
"""

import trimesh
import numpy as np


def load_mesh(filepath):
    """Load a mesh from file. Returns trimesh.Trimesh object."""
    mesh = trimesh.load(filepath, process=False)
    if isinstance(mesh, trimesh.Scene):
        # If loaded as scene, combine all geometries
        mesh = mesh.dump(concatenate=True)
    print(f"Loaded mesh: {filepath}")
    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces: {len(mesh.faces)}")
    return mesh


def save_mesh(mesh, filepath):
    """Save a mesh to file."""
    mesh.export(filepath)
    print(f"Saved mesh: {filepath}")


def create_test_mesh_with_hole(hole_size=10, seed=42):
    """
    Create a test mesh (sphere) with an artificial hole for testing.
    Removes `hole_size` adjacent faces to create a hole.
    Returns: (mesh_with_hole, original_mesh, removed_face_indices)
    """
    rng = np.random.default_rng(seed)

    # Create a UV sphere
    mesh = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
    original = mesh.copy()

    # Pick a seed face and expand to create a hole
    seed_face = rng.integers(0, len(mesh.faces))
    adjacency = mesh.face_adjacency

    # BFS to find adjacent faces
    to_remove = {seed_face}
    frontier = {seed_face}
    while len(to_remove) < hole_size and frontier:
        new_frontier = set()
        for f in frontier:
            # Find adjacent faces
            mask = (adjacency[:, 0] == f) | (adjacency[:, 1] == f)
            neighbors = adjacency[mask].flatten()
            for n in neighbors:
                if n not in to_remove:
                    new_frontier.add(n)
                    to_remove.add(n)
                    if len(to_remove) >= hole_size:
                        break
            if len(to_remove) >= hole_size:
                break
        frontier = new_frontier

    remove_indices = sorted(to_remove)

    # Remove faces to create hole
    keep_mask = np.ones(len(mesh.faces), dtype=bool)
    keep_mask[remove_indices] = False
    mesh.update_faces(keep_mask)
    mesh.remove_unreferenced_vertices()

    print(f"Created test mesh with hole:")
    print(f"  Original faces: {len(original.faces)}")
    print(f"  Removed faces: {len(remove_indices)}")
    print(f"  Remaining faces: {len(mesh.faces)}")

    return mesh, original, remove_indices
