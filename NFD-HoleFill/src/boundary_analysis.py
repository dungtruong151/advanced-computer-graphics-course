"""
Step 3: Boundary Analysis
Compute normals and curvature at boundary vertices of each hole.
"""

import numpy as np
from collections import defaultdict


def compute_vertex_normals(vertices, faces):
    """Compute per-vertex normals as area-weighted average of adjacent face normals."""
    vertex_normals = np.zeros_like(vertices)

    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        edge1 = v1 - v0
        edge2 = v2 - v0
        face_normal = np.cross(edge1, edge2)
        # Area-weighted (face_normal magnitude = 2 * triangle area)
        for vi in face:
            vertex_normals[vi] += face_normal

    # Normalize
    norms = np.linalg.norm(vertex_normals, axis=1, keepdims=True)
    norms[norms < 1e-10] = 1.0
    vertex_normals /= norms

    return vertex_normals


def compute_vertex_adjacency(faces):
    """Build vertex-to-vertex adjacency from faces."""
    adj = defaultdict(set)
    for face in faces:
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[face[i]].add(face[j])
    return adj


def compute_cotangent_weights(vertices, faces):
    """
    Compute cotangent weights for the Laplacian.
    Returns dict: (vi, vj) -> weight
    """
    weights = defaultdict(float)

    for face in faces:
        for k in range(3):
            i = face[k]
            j = face[(k + 1) % 3]
            opp = face[(k + 2) % 3]

            # Compute cotangent of angle at opposite vertex
            ei = vertices[i] - vertices[opp]
            ej = vertices[j] - vertices[opp]

            cos_angle = np.dot(ei, ej) / (np.linalg.norm(ei) * np.linalg.norm(ej) + 1e-10)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            sin_angle = np.sqrt(1.0 - cos_angle ** 2) + 1e-10
            cot = cos_angle / sin_angle

            # Clamp to avoid numerical issues
            cot = np.clip(cot, -10.0, 10.0)

            weights[(i, j)] += 0.5 * cot
            weights[(j, i)] += 0.5 * cot

    return weights


def compute_mean_curvature(vertices, faces, vertex_indices=None):
    """
    Compute mean curvature at vertices using the cotangent Laplacian.
    H(v) = (1/2) * ||Laplacian(v)||

    Args:
        vertices: (N, 3) vertex positions
        faces: (M, 3) face indices
        vertex_indices: compute only for these vertices (None = all)

    Returns:
        curvatures: dict mapping vertex index -> mean curvature value
    """
    if vertex_indices is None:
        vertex_indices = range(len(vertices))

    weights = compute_cotangent_weights(vertices, faces)
    adj = compute_vertex_adjacency(faces)

    curvatures = {}

    for vi in vertex_indices:
        neighbors = adj.get(vi, set())
        if not neighbors:
            curvatures[vi] = 0.0
            continue

        # Compute cotangent Laplacian at vi
        laplacian = np.zeros(3)
        weight_sum = 0.0

        for vj in neighbors:
            w = weights.get((vi, vj), 0.0)
            laplacian += w * (vertices[vj] - vertices[vi])
            weight_sum += w

        if weight_sum > 1e-10:
            laplacian /= weight_sum

        # Mean curvature = 0.5 * ||Laplacian||
        H = 0.5 * np.linalg.norm(laplacian)
        curvatures[vi] = H

    return curvatures


def analyze_boundary(vertices, faces, loop):
    """
    Main function: compute normals and curvature at boundary vertices.

    Returns:
        boundary_normals: dict mapping vertex index -> normal vector (3,)
        boundary_curvatures: dict mapping vertex index -> mean curvature (float)
        avg_curvature: average mean curvature at boundary
    """
    # Compute vertex normals for all vertices (needed for diffusion boundary conditions)
    all_normals = compute_vertex_normals(vertices, faces)

    boundary_normals = {}
    for vi in loop:
        boundary_normals[vi] = all_normals[vi]

    # Compute mean curvature at boundary
    boundary_curvatures = compute_mean_curvature(vertices, faces, loop)

    avg_curvature = np.mean(list(boundary_curvatures.values()))

    print(f"  Boundary analysis:")
    print(f"    Boundary vertices: {len(loop)}")
    print(f"    Avg mean curvature: {avg_curvature:.6f}")
    print(f"    Min curvature: {min(boundary_curvatures.values()):.6f}")
    print(f"    Max curvature: {max(boundary_curvatures.values()):.6f}")

    return boundary_normals, boundary_curvatures, avg_curvature
