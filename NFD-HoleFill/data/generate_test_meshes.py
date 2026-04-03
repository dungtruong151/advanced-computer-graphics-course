"""
Generate test meshes with holes for NFD Hole Filling plugin testing.
Output: data/input/ as .ply files ready for MeshLab.
"""

import numpy as np
import trimesh
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def remove_faces_around_vertex(mesh, vertex_index, radius_faces=1):
    """Remove faces touching a vertex and optionally its neighbors (BFS by face rings)."""
    import collections
    # Build vertex -> faces map
    vf = collections.defaultdict(set)
    for i, face in enumerate(mesh.faces):
        for v in face:
            vf[v].add(i)

    # BFS over face rings
    frontier_verts = {vertex_index}
    removed_faces = set()
    for _ in range(radius_faces):
        next_verts = set()
        for v in frontier_verts:
            for fi in vf[v]:
                if fi not in removed_faces:
                    removed_faces.add(fi)
                    for nv in mesh.faces[fi]:
                        if nv not in frontier_verts:
                            next_verts.add(nv)
        frontier_verts = next_verts

    keep = [i for i in range(len(mesh.faces)) if i not in removed_faces]
    new_mesh = trimesh.Trimesh(
        vertices=mesh.vertices.copy(),
        faces=mesh.faces[keep],
        process=False
    )
    return new_mesh


def save(mesh, name):
    path = os.path.join(OUTPUT_DIR, name)
    mesh.export(path)
    n_holes = count_holes(mesh)
    print(f"  Saved: {name}  |  vertices={len(mesh.vertices)}  faces={len(mesh.faces)}  holes~{n_holes}")


def count_holes(mesh):
    """Count boundary loops (approximate hole count)."""
    edges = mesh.edges_sorted
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    boundary_edges = unique[counts == 1]
    if len(boundary_edges) == 0:
        return 0
    # Build adjacency among boundary edges
    adj = {}
    for e in boundary_edges:
        for v in e:
            adj.setdefault(v, []).append(tuple(e))
    visited = set()
    loops = 0
    for start in adj:
        if start in visited:
            continue
        stack = [start]
        while stack:
            v = stack.pop()
            if v in visited:
                continue
            visited.add(v)
            for e in adj.get(v, []):
                for nv in e:
                    if nv not in visited:
                        stack.append(nv)
        loops += 1
    return loops


# ── 1. Sphere with 1 small hole ────────────────────────────────────────────
print("1. Sphere - small hole")
sphere = trimesh.creation.icosphere(subdivisions=3)  # ~642 verts
top_vertex = np.argmax(sphere.vertices[:, 2])
m = remove_faces_around_vertex(sphere, top_vertex, radius_faces=1)
save(m, "sphere_small_hole.ply")

# ── 2. Sphere with 1 large hole ────────────────────────────────────────────
print("2. Sphere - large hole")
m = remove_faces_around_vertex(sphere, top_vertex, radius_faces=2)
save(m, "sphere_large_hole.ply")

# ── 3. Sphere with 2 holes ──────────────────────────────────────────────────
print("3. Sphere - 2 holes")
top = np.argmax(sphere.vertices[:, 2])
bottom = np.argmin(sphere.vertices[:, 2])
m = remove_faces_around_vertex(sphere, top, radius_faces=1)
m = remove_faces_around_vertex(m, bottom, radius_faces=1)
save(m, "sphere_two_holes.ply")

# ── 4. Cylinder with hole on the side ──────────────────────────────────────
print("4. Cylinder - side hole")
cyl = trimesh.creation.cylinder(radius=1.0, height=3.0, sections=40)
# Find vertex on the side near the middle
radii = np.sqrt(cyl.vertices[:, 0]**2 + cyl.vertices[:, 1]**2)
side_verts = np.where(radii > radii.max() * 0.9)[0]
m = remove_faces_around_vertex(cyl, side_verts[0], radius_faces=1)
save(m, "cylinder_side_hole.ply")

# ── 5. Torus with 1 hole ────────────────────────────────────────────────────
print("5. Torus - hole")
torus = trimesh.creation.torus(major_radius=2.0, minor_radius=0.5, minor_sections=20)
outer_verts = np.argsort(torus.vertices[:, 0])[-1:]
m = remove_faces_around_vertex(torus, outer_verts[0], radius_faces=1)
save(m, "torus_hole.ply")

# ── 6. Bunny with hole (if bunny.obj exists) ────────────────────────────────
bunny_path = os.path.join(OUTPUT_DIR, "bunny.obj")
if os.path.exists(bunny_path):
    print("6. Bunny - hole")
    bunny = trimesh.load(bunny_path, process=False)
    top = np.argmax(bunny.vertices[:, 1])
    m = remove_faces_around_vertex(bunny, top, radius_faces=2)
    save(m, "bunny_hole.ply")
else:
    print("6. Bunny skipped (bunny.obj not found)")

print("\nDone. Files saved to:", OUTPUT_DIR)
