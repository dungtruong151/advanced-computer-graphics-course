"""
Step 2: Initial Triangulation
Fill a hole with an initial triangulation using ear clipping,
then refine by adding interior vertices for large holes.
"""

import numpy as np


def compute_loop_plane(vertices, loop):
    """Compute best-fit plane for a boundary loop using PCA."""
    points = vertices[loop]
    centroid = points.mean(axis=0)
    centered = points - centroid
    _, _, Vt = np.linalg.svd(centered)
    normal = Vt[-1]  # Smallest singular value direction = normal
    return centroid, normal


def project_to_2d(points_3d, centroid, normal):
    """Project 3D points onto the best-fit plane, returning 2D coordinates."""
    # Create local coordinate system on the plane
    up = np.array([0, 0, 1])
    if abs(np.dot(normal, up)) > 0.9:
        up = np.array([1, 0, 0])
    u = np.cross(normal, up)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)

    centered = points_3d - centroid
    coords_2d = np.column_stack([centered @ u, centered @ v])
    return coords_2d, u, v


def is_ear(polygon_2d, i, n_verts):
    """Check if vertex i forms an ear in the 2D polygon."""
    prev_i = (i - 1) % n_verts
    next_i = (i + 1) % n_verts

    a = polygon_2d[prev_i]
    b = polygon_2d[i]
    c = polygon_2d[next_i]

    # Check if triangle ABC is counter-clockwise (convex at B)
    cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if cross <= 0:
        return False

    # Check no other vertex is inside triangle ABC
    for j in range(n_verts):
        if j in (prev_i, i, next_i):
            continue
        if point_in_triangle(polygon_2d[j], a, b, c):
            return False

    return True


def point_in_triangle(p, a, b, c):
    """Check if point p is inside triangle abc using barycentric coordinates."""
    v0 = c - a
    v1 = b - a
    v2 = p - a

    dot00 = v0 @ v0
    dot01 = v0 @ v1
    dot02 = v0 @ v2
    dot11 = v1 @ v1
    dot12 = v1 @ v2

    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) < 1e-12:
        return False

    inv_denom = 1.0 / denom
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom

    return (u >= 0) and (v >= 0) and (u + v <= 1)


def ear_clipping(vertices, loop):
    """
    Triangulate a hole using ear clipping algorithm.

    Args:
        vertices: (N, 3) array of all mesh vertices
        loop: list of vertex indices forming the boundary loop

    Returns:
        new_faces: list of (v1, v2, v3) triangles filling the hole
    """
    if len(loop) < 3:
        return []

    if len(loop) == 3:
        return [tuple(loop)]

    # Project to 2D for ear detection
    centroid, normal = compute_loop_plane(vertices, loop)
    points_3d = vertices[loop]
    polygon_2d, _, _ = project_to_2d(points_3d, centroid, normal)

    # Ensure counter-clockwise orientation
    area = 0
    n = len(polygon_2d)
    for i in range(n):
        j = (i + 1) % n
        area += polygon_2d[i][0] * polygon_2d[j][1]
        area -= polygon_2d[j][0] * polygon_2d[i][1]
    if area < 0:
        polygon_2d = polygon_2d[::-1]
        loop = loop[::-1]

    # Ear clipping
    remaining = list(range(len(loop)))
    poly = polygon_2d.copy()
    faces = []

    max_iter = len(loop) * 3  # Safety limit
    iteration = 0

    while len(remaining) > 3 and iteration < max_iter:
        ear_found = False
        n_rem = len(remaining)

        for i in range(n_rem):
            if is_ear(poly, i, n_rem):
                prev_i = (i - 1) % n_rem
                next_i = (i + 1) % n_rem

                # Add triangle using original vertex indices
                faces.append((
                    loop[remaining[prev_i]],
                    loop[remaining[i]],
                    loop[remaining[next_i]]
                ))

                # Remove ear vertex
                remaining.pop(i)
                poly = np.delete(poly, i, axis=0)
                ear_found = True
                break

        if not ear_found:
            # Fallback: just take the first three vertices
            faces.append((
                loop[remaining[0]],
                loop[remaining[1]],
                loop[remaining[2]]
            ))
            remaining.pop(1)
            poly = np.delete(poly, 1, axis=0)

        iteration += 1

    # Add last triangle
    if len(remaining) == 3:
        faces.append((
            loop[remaining[0]],
            loop[remaining[1]],
            loop[remaining[2]]
        ))

    return faces


def refine_triangulation(vertices, faces, new_faces, loop, max_edge_length=None):
    """
    Refine the initial triangulation by splitting large triangles
    and adding interior vertices. For large holes.

    Args:
        vertices: current vertex array (will be extended)
        faces: existing mesh faces
        new_faces: triangles from ear clipping
        loop: boundary vertex indices
        max_edge_length: maximum allowed edge length (auto-computed if None)

    Returns:
        refined_vertices: updated vertex array with new interior vertices
        refined_faces: refined triangles for the patch
        interior_vertex_indices: indices of newly added interior vertices
    """
    if not new_faces:
        return vertices, [], []

    boundary_set = set(loop)

    # Compute max edge length from boundary if not given
    if max_edge_length is None:
        boundary_points = vertices[loop]
        edge_lengths = []
        for i in range(len(loop)):
            j = (i + 1) % len(loop)
            edge_lengths.append(np.linalg.norm(
                boundary_points[i] - boundary_points[j]
            ))
        max_edge_length = np.mean(edge_lengths) * 1.5

    # Simple refinement: split triangles with edges too long
    refined = list(new_faces)
    new_verts = list(vertices)
    interior_indices = []

    changed = True
    max_refine_iter = 3
    refine_iter = 0

    while changed and refine_iter < max_refine_iter:
        changed = False
        next_refined = []

        for tri in refined:
            v0, v1, v2 = tri
            p0, p1, p2 = np.array(new_verts[v0]), np.array(new_verts[v1]), np.array(new_verts[v2])

            e01 = np.linalg.norm(p1 - p0)
            e12 = np.linalg.norm(p2 - p1)
            e20 = np.linalg.norm(p0 - p2)

            max_e = max(e01, e12, e20)

            if max_e > max_edge_length:
                # Split at centroid
                centroid = (p0 + p1 + p2) / 3.0
                new_idx = len(new_verts)
                new_verts.append(centroid)
                interior_indices.append(new_idx)

                next_refined.append((v0, v1, new_idx))
                next_refined.append((v1, v2, new_idx))
                next_refined.append((v2, v0, new_idx))
                changed = True
            else:
                next_refined.append(tri)

        refined = next_refined
        refine_iter += 1

    return np.array(new_verts), refined, interior_indices


def triangulate_hole(vertices, loop):
    """
    Main function: triangulate a single hole.

    Returns:
        new_vertices: vertex array (may have new interior vertices)
        patch_faces: list of triangles filling the hole
        interior_indices: indices of interior vertices (new ones added)
        boundary_indices: the original loop indices
    """
    # Step 1: Ear clipping
    patch_faces = ear_clipping(vertices, loop)
    print(f"  Ear clipping produced {len(patch_faces)} triangles")

    # Step 2: Refine to add interior vertices (needed for normal diffusion)
    if len(loop) >= 5:
        new_vertices, patch_faces, interior_indices = refine_triangulation(
            vertices, None, patch_faces, loop
        )
        print(f"  Refinement: {len(interior_indices)} interior vertices added")
    else:
        new_vertices = vertices
        interior_indices = []

    return new_vertices, patch_faces, interior_indices, loop
