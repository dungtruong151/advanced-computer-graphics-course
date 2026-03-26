"""
Step 5: Curvature-Guided Vertex Displacement
Step 6: Local Smoothing

Displace interior patch vertices along diffused normals,
guided by boundary curvature information.
Then apply constrained Laplacian smoothing.
"""

import numpy as np
from collections import defaultdict


def compute_geodesic_distance_to_boundary(patch_vertices, patch_faces,
                                          boundary_indices, interior_indices):
    """
    Compute approximate geodesic distance from each interior vertex
    to the nearest boundary vertex using Dijkstra on the mesh graph.

    Returns: dict mapping vertex index -> normalized distance [0, 1]
    """
    # Build adjacency with edge lengths
    adj = defaultdict(list)
    for face in patch_faces:
        for i in range(3):
            vi = face[i]
            vj = face[(i + 1) % 3]
            dist = np.linalg.norm(patch_vertices[vi] - patch_vertices[vj])
            adj[vi].append((vj, dist))
            adj[vj].append((vi, dist))

    boundary_set = set(boundary_indices)

    # Dijkstra from all boundary vertices simultaneously
    import heapq
    dist = {}
    for vi in boundary_indices:
        dist[vi] = 0.0

    heap = [(0.0, vi) for vi in boundary_indices]
    heapq.heapify(heap)

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float('inf')):
            continue
        for v, w in adj[u]:
            new_dist = d + w
            if new_dist < dist.get(v, float('inf')):
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    # Normalize distances for interior vertices
    if not interior_indices:
        return {}

    interior_dists = {vi: dist.get(vi, 0.0) for vi in interior_indices}
    max_dist = max(interior_dists.values()) if interior_dists else 1.0
    if max_dist < 1e-10:
        max_dist = 1.0

    normalized = {vi: d / max_dist for vi, d in interior_dists.items()}
    return normalized


def displacement_weight(t):
    """
    Weighting function for displacement based on normalized distance.
    g(t) = t * (1 - t) * 4  (peaks at t=0.5, zero at boundary and center)

    The factor 4 ensures max value = 1.0 at t = 0.5
    """
    return 4.0 * t * (1.0 - t)


def estimate_displacement_magnitude(vertices, boundary_indices, patch_faces):
    """
    Estimate how much interior vertices should be displaced by analyzing
    the boundary geometry. Uses the deviation of the hole centroid from
    the average boundary plane to guess the surface curvature depth.

    Returns: estimated displacement scale factor
    """
    boundary_points = vertices[boundary_indices]
    centroid = boundary_points.mean(axis=0)

    # Compute average edge length at boundary for scale reference
    edge_lengths = []
    for i in range(len(boundary_indices)):
        j = (i + 1) % len(boundary_indices)
        el = np.linalg.norm(boundary_points[i] - boundary_points[j])
        edge_lengths.append(el)
    avg_edge = np.mean(edge_lengths)

    # Compute hole "diameter" (max distance between boundary vertices)
    from scipy.spatial.distance import pdist
    if len(boundary_points) > 1:
        hole_diameter = np.max(pdist(boundary_points))
    else:
        hole_diameter = avg_edge

    return avg_edge, hole_diameter


def displace_vertices(patch_vertices, patch_faces, boundary_indices,
                      interior_indices, diffused_normals,
                      boundary_curvatures, avg_curvature,
                      displacement_scale=1.0):
    """
    Displace interior vertices along their diffused normals.

    Uses adaptive displacement: combines curvature information with
    hole geometry to determine appropriate displacement magnitude.

    v_i' = v_i + d_i * n_diffused(i)

    Args:
        patch_vertices: vertex positions
        patch_faces: patch triangles
        boundary_indices: boundary vertex indices (not moved)
        interior_indices: interior vertex indices (to be displaced)
        diffused_normals: dict vi -> normal vector
        boundary_curvatures: dict vi -> curvature at boundary
        avg_curvature: average curvature at boundary
        displacement_scale: user scaling factor

    Returns:
        displaced_vertices: updated vertex positions
    """
    vertices = patch_vertices.copy()

    if not interior_indices:
        return vertices

    # Compute geodesic distances
    geo_dist = compute_geodesic_distance_to_boundary(
        vertices, patch_faces, boundary_indices, interior_indices
    )

    # Estimate adaptive displacement from hole geometry
    avg_edge, hole_diameter = estimate_displacement_magnitude(
        vertices, boundary_indices, patch_faces
    )

    # Adaptive scale: curvature * hole_diameter gives natural depth estimate
    # For a sphere of radius R: curvature ~ 1/R, hole_diameter ~ d
    # Sagitta (depth) of spherical cap ~ d^2 / (8*R) = d^2 * curvature / 8
    adaptive_depth = (hole_diameter ** 2) * avg_curvature / 8.0

    # Compute displacement for each interior vertex
    n_displaced = 0
    max_displacement = 0.0

    for vi in interior_indices:
        if vi not in diffused_normals:
            continue

        normal = diffused_normals[vi]
        t = geo_dist.get(vi, 0.0)
        weight = displacement_weight(t)

        # Displacement magnitude: adaptive depth * weight * user scale
        d = adaptive_depth * displacement_scale * weight

        # Apply displacement
        vertices[vi] = vertices[vi] + d * normal
        n_displaced += 1
        max_displacement = max(max_displacement, abs(d))

    print(f"  Vertex Displacement:")
    print(f"    Displaced vertices: {n_displaced}")
    print(f"    Avg curvature: {avg_curvature:.6f}")
    print(f"    Hole diameter: {hole_diameter:.6f}")
    print(f"    Adaptive depth: {adaptive_depth:.6f}")
    print(f"    Max displacement: {max_displacement:.6f}")

    return vertices


def laplacian_smooth_patch(vertices, patch_faces, boundary_indices,
                           interior_indices, n_iterations=3, alpha=0.5):
    """
    Apply Laplacian smoothing ONLY to interior patch vertices.
    Boundary vertices are kept fixed.

    Args:
        vertices: vertex positions (modified in-place)
        patch_faces: patch triangles
        boundary_indices: fixed vertices
        interior_indices: vertices to smooth
        n_iterations: number of smoothing passes
        alpha: smoothing factor (0 = no smooth, 1 = full Laplacian)

    Returns:
        smoothed_vertices: updated vertex positions
    """
    result = vertices.copy()
    boundary_set = set(boundary_indices)
    interior_set = set(interior_indices)

    # Build adjacency from patch faces only
    adj = defaultdict(set)
    for face in patch_faces:
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[face[i]].add(face[j])

    for iteration in range(n_iterations):
        new_positions = result.copy()

        for vi in interior_indices:
            neighbors = adj.get(vi, set())
            if not neighbors:
                continue

            # Compute centroid of neighbors
            centroid = np.zeros(3)
            for vj in neighbors:
                centroid += result[vj]
            centroid /= len(neighbors)

            # Move toward centroid
            new_positions[vi] = (1.0 - alpha) * result[vi] + alpha * centroid

        result = new_positions

    n_smoothed = len(interior_indices)
    print(f"  Laplacian Smoothing:")
    print(f"    Iterations: {n_iterations}, alpha: {alpha}")
    print(f"    Smoothed vertices: {n_smoothed}")

    return result
