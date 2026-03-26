"""
Step 4: Normal Field Diffusion (CORE NOVELTY)

Propagate normal vectors from boundary into the hole interior
using heat diffusion on the patch mesh.

The heat equation on the mesh:
    dn/dt = lambda * L * n

where L is the cotangent Laplacian matrix of the patch,
and boundary conditions are fixed normals from the original mesh.

Solved using implicit Euler:
    (I - lambda * dt * L) * n^(t+1) = n^(t)
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve


def build_patch_laplacian(patch_vertices, patch_faces, n_total_verts):
    """
    Build the cotangent Laplacian matrix for the patch mesh.

    Args:
        patch_vertices: vertex positions (full array)
        patch_faces: triangles of the patch
        n_total_verts: total number of vertices

    Returns:
        L: sparse (n_total_verts x n_total_verts) cotangent Laplacian
    """
    rows = []
    cols = []
    vals = []

    for face in patch_faces:
        for k in range(3):
            i = face[k]
            j = face[(k + 1) % 3]
            opp = face[(k + 2) % 3]

            ei = patch_vertices[i] - patch_vertices[opp]
            ej = patch_vertices[j] - patch_vertices[opp]

            cos_a = np.dot(ei, ej) / (np.linalg.norm(ei) * np.linalg.norm(ej) + 1e-10)
            cos_a = np.clip(cos_a, -0.999, 0.999)
            sin_a = np.sqrt(1.0 - cos_a ** 2) + 1e-10
            cot = cos_a / sin_a
            cot = np.clip(cot, -10.0, 10.0)

            w = 0.5 * cot

            # Off-diagonal: L[i,j] += w, L[j,i] += w
            rows.extend([i, j])
            cols.extend([j, i])
            vals.extend([w, w])

            # Diagonal: L[i,i] -= w, L[j,j] -= w
            rows.extend([i, j])
            cols.extend([i, j])
            vals.extend([-w, -w])

    L = sparse.coo_matrix((vals, (rows, cols)),
                          shape=(n_total_verts, n_total_verts)).tocsr()
    return L


def diffuse_normal_field(patch_vertices, patch_faces, boundary_indices,
                         boundary_normals, interior_indices,
                         lambda_param=1.0, dt=0.1, n_iterations=50,
                         convergence_threshold=1e-6):
    """
    Diffuse normal vectors from boundary into interior vertices.

    Uses implicit Euler time stepping:
        (I - lambda * dt * L) * n^(t+1) = n^(t)

    Boundary conditions: normals at boundary vertices are fixed.

    Args:
        patch_vertices: all vertex positions
        patch_faces: triangles of the patch (list of tuples)
        boundary_indices: vertex indices on the boundary (fixed normals)
        boundary_normals: dict mapping boundary vertex -> normal vector
        interior_indices: vertex indices inside the patch (to be computed)
        lambda_param: diffusion coefficient (controls spread speed)
        dt: time step
        n_iterations: max number of diffusion iterations
        convergence_threshold: stop if change < threshold

    Returns:
        diffused_normals: dict mapping vertex index -> diffused normal vector
    """
    if not interior_indices:
        # No interior vertices, just return boundary normals
        return dict(boundary_normals)

    n_verts = len(patch_vertices)

    # All patch vertices (boundary + interior)
    all_patch_verts = set(boundary_indices) | set(interior_indices)

    # Build Laplacian for patch
    L = build_patch_laplacian(patch_vertices, patch_faces, n_verts)

    # Initialize normals: boundary = known, interior = average of boundary normals
    normals = np.zeros((n_verts, 3))

    # Set boundary normals
    boundary_set = set(boundary_indices)
    avg_normal = np.zeros(3)
    for vi, n in boundary_normals.items():
        normals[vi] = n
        avg_normal += n
    avg_normal /= len(boundary_normals)
    avg_normal /= np.linalg.norm(avg_normal) + 1e-10

    # Initialize interior normals to average of boundary
    for vi in interior_indices:
        normals[vi] = avg_normal

    # Build system matrix: (I - lambda * dt * L)
    I = sparse.eye(n_verts, format='csr')
    A = I - lambda_param * dt * L

    # Modify A to fix boundary conditions:
    # For boundary vertices, set row to identity (so n doesn't change)
    for vi in boundary_indices:
        # Zero out row
        start, end = A.indptr[vi], A.indptr[vi + 1]
        A.data[start:end] = 0.0
        # Set diagonal to 1
        for idx in range(start, end):
            if A.indices[idx] == vi:
                A.data[idx] = 1.0

    A.eliminate_zeros()

    # Iterative diffusion
    print(f"  Normal Field Diffusion:")
    print(f"    Interior vertices: {len(interior_indices)}")
    print(f"    Lambda: {lambda_param}, dt: {dt}, max_iter: {n_iterations}")

    interior_set = set(interior_indices)

    for iteration in range(n_iterations):
        old_normals = normals.copy()

        # Solve for each component (x, y, z) independently
        for dim in range(3):
            rhs = normals[:, dim].copy()

            # Fix boundary RHS
            for vi in boundary_indices:
                rhs[vi] = boundary_normals[vi][dim]

            # Solve
            normals[:, dim] = spsolve(A, rhs)

        # Re-normalize interior normals
        for vi in interior_indices:
            norm = np.linalg.norm(normals[vi])
            if norm > 1e-10:
                normals[vi] /= norm

        # Re-fix boundary (should already be correct, but just in case)
        for vi in boundary_indices:
            normals[vi] = boundary_normals[vi]

        # Check convergence on interior vertices
        max_change = 0.0
        for vi in interior_indices:
            change = np.linalg.norm(normals[vi] - old_normals[vi])
            max_change = max(max_change, change)

        if (iteration + 1) % 10 == 0 or iteration == 0:
            print(f"    Iteration {iteration + 1}: max change = {max_change:.8f}")

        if max_change < convergence_threshold:
            print(f"    Converged at iteration {iteration + 1}")
            break

    # Collect results
    diffused_normals = {}
    for vi in boundary_indices:
        diffused_normals[vi] = normals[vi].copy()
    for vi in interior_indices:
        diffused_normals[vi] = normals[vi].copy()

    return diffused_normals
