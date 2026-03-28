"""
Test NFD Hole Fill logic in Python to verify before running in Meshlab.
This mirrors the C++ plugin pipeline exactly.
"""
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from collections import Counter, defaultdict
import pymeshlab
import time

def load_mesh(path):
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(path)
    m = ms.current_mesh()
    verts = m.vertex_matrix().copy()
    faces = m.face_matrix().copy()
    normals = m.vertex_normal_matrix().copy()
    return verts, faces, normals

def find_boundary_edges(faces):
    edge_count = Counter()
    edge_to_face = defaultdict(list)
    for fi, f in enumerate(faces):
        for i in range(3):
            e = tuple(sorted([int(f[i]), int(f[(i+1)%3])]))
            edge_count[e] += 1
            edge_to_face[e].append((fi, i))
    boundary_edges = {e for e, c in edge_count.items() if c == 1}
    return boundary_edges, edge_to_face

def detect_holes(verts, faces, max_hole_size=100):
    boundary_edges, _ = find_boundary_edges(faces)

    # Build directed boundary edge map: v0 -> v1
    next_boundary = {}
    for e in boundary_edges:
        # Find which direction is the boundary half-edge
        # For boundary edge (a,b), we need to find the face and determine order
        next_boundary.setdefault(e[0], []).append(e[1])
        next_boundary.setdefault(e[1], []).append(e[0])

    # Trace loops
    visited = set()
    holes = []

    for start_e in boundary_edges:
        v0, v1 = start_e
        if (v0, v1) in visited:
            continue

        # Try tracing from v0
        loop = [v0]
        visited.add((v0, v1))
        current = v1
        prev = v0

        safety = 0
        while safety < max_hole_size * 2:
            safety += 1
            loop.append(current)

            # Find next vertex
            neighbors = next_boundary.get(current, [])
            next_v = None
            for n in neighbors:
                if n != prev and (tuple(sorted([current, n])) in boundary_edges):
                    if (current, n) not in visited:
                        next_v = n
                        break

            if next_v is None or next_v == v0:
                if next_v == v0:
                    visited.add((current, next_v))
                    # Complete loop
                    if 3 <= len(loop) <= max_hole_size:
                        holes.append(loop)
                break

            visited.add((current, next_v))
            prev = current
            current = next_v

    return holes

def compute_boundary_info(verts, faces, normals, hole_indices):
    """Compute normals and mean curvature at boundary vertices."""
    n = len(hole_indices)
    hole_normals = np.zeros((n, 3))
    hole_curvatures = np.zeros(n)

    # Build vertex adjacency
    adj = defaultdict(set)
    for f in faces:
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[int(f[i])].add(int(f[j]))

    for i, vi in enumerate(hole_indices):
        # Normal from mesh
        hole_normals[i] = normals[vi]
        norm = np.linalg.norm(hole_normals[i])
        if norm > 1e-10:
            hole_normals[i] /= norm

        # Mean curvature via Laplacian
        neighbors = list(adj[vi])
        if len(neighbors) > 0:
            laplacian = np.mean([verts[nj] - verts[vi] for nj in neighbors], axis=0)
            hole_curvatures[i] = np.linalg.norm(laplacian) / 2.0

    return hole_normals, hole_curvatures

def triangulate_patch(positions, hole_normals):
    """Create initial triangulation: boundary + interior ring + centroid."""
    n = len(positions)

    patch_verts = list(positions.copy())
    is_boundary = [True] * n

    centroid = np.mean(positions, axis=0)
    avg_normal = np.mean(hole_normals, axis=0)
    norm = np.linalg.norm(avg_normal)
    if norm > 1e-10:
        avg_normal /= norm

    if n <= 10:
        # Fan triangulation
        cent_idx = len(patch_verts)
        patch_verts.append(centroid)
        is_boundary.append(False)

        patch_faces = []
        for i in range(n):
            j = (i + 1) % n
            patch_faces.append([i, j, cent_idx])
    else:
        # Interior ring + centroid
        ring_start = len(patch_verts)
        for i in range(n):
            mid = positions[i] * 0.5 + centroid * 0.5
            patch_verts.append(mid)
            is_boundary.append(False)

        cent_idx = len(patch_verts)
        patch_verts.append(centroid)
        is_boundary.append(False)

        patch_faces = []
        for i in range(n):
            j = (i + 1) % n
            ri = ring_start + i
            rj = ring_start + j
            patch_faces.append([i, j, rj])
            patch_faces.append([i, rj, ri])
            patch_faces.append([ri, rj, cent_idx])

    patch_verts = np.array(patch_verts)
    patch_faces = np.array(patch_faces)

    # Init normals
    patch_normals = np.tile(avg_normal, (len(patch_verts), 1))
    patch_normals[:n] = hole_normals

    return patch_verts, patch_faces, patch_normals, n

def diffuse_normal_field(patch_verts, patch_faces, patch_normals, n_boundary, iterations=50, lam=0.5):
    """Heat-equation-based normal field diffusion (core novelty)."""
    n_verts = len(patch_verts)
    n_interior = n_verts - n_boundary

    if n_interior == 0:
        return patch_normals

    # Build adjacency
    adj = defaultdict(set)
    for f in patch_faces:
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[int(f[i])].add(int(f[j]))

    # Interior vertex mapping
    interior_verts = list(range(n_boundary, n_verts))
    interior_map = {v: i for i, v in enumerate(interior_verts)}

    # Build sparse system: (I + lambda * L) * n_new = n_old + lambda * boundary_contrib
    A = lil_matrix((n_interior, n_interior))

    for ii, vi in enumerate(interior_verts):
        deg = len(adj[vi])
        A[ii, ii] = 1.0 + lam * deg
        for nj in adj[vi]:
            if nj in interior_map:
                A[ii, interior_map[nj]] = -lam

    A = A.tocsc()

    # Iterative diffusion
    normals = patch_normals.copy()
    for iteration in range(iterations):
        rhs = np.zeros((n_interior, 3))
        for ii, vi in enumerate(interior_verts):
            rhs[ii] = normals[vi]
            for nj in adj[vi]:
                if nj not in interior_map:  # boundary
                    rhs[ii] += lam * patch_normals[nj]

        for dim in range(3):
            normals[interior_verts, dim] = spsolve(A, rhs[:, dim])

    # Normalize
    for i in interior_verts:
        norm = np.linalg.norm(normals[i])
        if norm > 1e-10:
            normals[i] /= norm

    return normals

def displace_vertices(patch_verts, patch_normals, n_boundary, hole_curvatures, positions):
    """Curvature-guided displacement along diffused normals."""
    H_avg = np.mean(hole_curvatures)

    avg_edge_len = 0
    for i in range(n_boundary):
        j = (i + 1) % n_boundary
        avg_edge_len += np.linalg.norm(positions[i] - positions[j])
    avg_edge_len /= n_boundary

    scale = H_avg * avg_edge_len

    centroid = np.mean(patch_verts[:n_boundary], axis=0)
    max_dist = max(np.linalg.norm(patch_verts[i] - centroid) for i in range(n_boundary))

    if max_dist < 1e-10:
        return patch_verts

    result = patch_verts.copy()
    for i in range(n_boundary, len(patch_verts)):
        min_dist = min(np.linalg.norm(patch_verts[i] - patch_verts[bi]) for bi in range(n_boundary))
        dist_norm = min(min_dist / max_dist, 1.0)
        weight = dist_norm * (1.0 - dist_norm) * 4.0
        displacement = scale * weight
        result[i] += patch_normals[i] * displacement

    return result

def smooth_patch(patch_verts, patch_faces, n_boundary, iterations=3):
    """Laplacian smoothing with fixed boundary."""
    adj = defaultdict(set)
    for f in patch_faces:
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[int(f[i])].add(int(f[j]))

    result = patch_verts.copy()
    for _ in range(iterations):
        new_pos = result.copy()
        for i in range(n_boundary, len(result)):
            if len(adj[i]) > 0:
                new_pos[i] = np.mean([result[nj] for nj in adj[i]], axis=0)
        result = new_pos
    return result

def save_result(original_verts, original_faces, patches, output_path):
    """Merge patches into original mesh and save."""
    all_verts = list(original_verts)
    all_faces = list(original_faces)

    for patch_verts, patch_faces, hole_indices, n_boundary in patches:
        vert_map = {}
        # Boundary verts map to original
        for i in range(n_boundary):
            vert_map[i] = hole_indices[i]
        # Interior verts are new
        for i in range(n_boundary, len(patch_verts)):
            vert_map[i] = len(all_verts)
            all_verts.append(patch_verts[i])
        # Add faces
        for f in patch_faces:
            all_faces.append([vert_map[int(f[0])], vert_map[int(f[1])], vert_map[int(f[2])]])

    all_verts = np.array(all_verts)
    all_faces = np.array(all_faces, dtype=np.int32)

    ms = pymeshlab.MeshSet()
    mesh = pymeshlab.Mesh(all_verts, all_faces)
    ms.add_mesh(mesh)
    ms.save_current_mesh(output_path)
    print("Saved:", output_path)

# =====================================================
# MAIN TEST
# =====================================================
if __name__ == "__main__":
    input_path = "C:/Users/ACE/Desktop/iu/Advanced Computer Graphics/NFD-HoleFill/data/input/bunny.obj"
    output_path = "C:/Users/ACE/Desktop/iu/Advanced Computer Graphics/NFD-HoleFill/data/output/bunny_nfd_filled.ply"

    print("Loading mesh...")
    verts, faces, normals = load_mesh(input_path)
    print("  Vertices:", len(verts), "Faces:", len(faces))

    print("\nDetecting holes...")
    t0 = time.time()
    holes = detect_holes(verts, faces, max_hole_size=100)
    print("  Found", len(holes), "holes in {:.2f}s".format(time.time() - t0))
    for i, h in enumerate(holes[:5]):
        print("    Hole {}: {} edges".format(i, len(h)))
    if len(holes) > 5:
        print("    ... and {} more".format(len(holes) - 5))

    if len(holes) == 0:
        print("No holes found!")
        exit()

    patches = []
    total = len(holes)
    for hi, hole_indices in enumerate(holes):
        print("\nProcessing hole {}/{}  ({} edges)...".format(hi+1, total, len(hole_indices)))

        positions = verts[hole_indices]

        # Step 2: Boundary info
        hole_normals, hole_curvatures = compute_boundary_info(verts, faces, normals, hole_indices)
        print("  Avg curvature: {:.6f}".format(np.mean(hole_curvatures)))

        # Step 3: Triangulate
        patch_verts, patch_faces, patch_normals, n_boundary = triangulate_patch(positions, hole_normals)
        print("  Patch: {} verts ({} interior), {} faces".format(
            len(patch_verts), len(patch_verts) - n_boundary, len(patch_faces)))

        # Step 4: Normal diffusion
        t0 = time.time()
        patch_normals = diffuse_normal_field(patch_verts, patch_faces, patch_normals, n_boundary, iterations=50, lam=0.5)
        print("  Normal diffusion: {:.2f}s".format(time.time() - t0))

        # Step 5: Displacement
        patch_verts = displace_vertices(patch_verts, patch_normals, n_boundary, hole_curvatures, positions)

        # Step 6: Smoothing
        patch_verts = smooth_patch(patch_verts, patch_faces, n_boundary, iterations=3)

        patches.append((patch_verts, patch_faces, hole_indices, n_boundary))
        print("  Done.")

    # Save result
    print("\nSaving result...")
    save_result(verts, faces, patches, output_path)

    # Verify
    ms2 = pymeshlab.MeshSet()
    ms2.load_new_mesh(output_path)
    m2 = ms2.current_mesh()
    print("\nResult: {} verts, {} faces".format(m2.vertex_number(), m2.face_number()))

    # Count remaining holes
    fm = m2.face_matrix()
    edge_count = Counter()
    for f in fm:
        for i in range(3):
            e = tuple(sorted([int(f[i]), int(f[(i+1)%3])]))
            edge_count[e] += 1
    remaining = sum(1 for c in edge_count.values() if c == 1)
    print("Remaining boundary edges:", remaining)
    print("\nTEST COMPLETE")
