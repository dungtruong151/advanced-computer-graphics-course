"""
Generate test meshes with holes for NFD Hole Filling plugin testing.

For every test case we now write TWO files:
  <name>_gt.ply      the full mesh (ground truth, no hole)
  <name>_hole.ply    the same mesh with one or more faces removed to form a hole

Having both lets evaluate.py compare the NFD-filled output against ground truth.

Output: data/input/ as .ply files ready for MeshLab.
"""

import collections
import io
import os
import sys
import urllib.request
import zipfile

import numpy as np
import trimesh


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def remove_faces_around_vertex(mesh, vertex_index, radius_faces=1):
    """Remove faces touching a vertex and optionally its neighbors (BFS by face rings)."""
    vf = collections.defaultdict(set)
    for i, face in enumerate(mesh.faces):
        for v in face:
            vf[v].add(i)

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


def count_holes(mesh):
    """Count boundary loops (approximate hole count)."""
    edges = mesh.edges_sorted
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    boundary_edges = unique[counts == 1]
    if len(boundary_edges) == 0:
        return 0
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


def save_pair(full_mesh, holed_mesh, base_name):
    """Save both the ground-truth mesh and its holed version."""
    gt_path = os.path.join(OUTPUT_DIR, base_name + "_gt.ply")
    hole_path = os.path.join(OUTPUT_DIR, base_name + "_hole.ply")
    full_mesh.export(gt_path)
    holed_mesh.export(hole_path)
    nh = count_holes(holed_mesh)
    print(f"  Saved: {base_name}_gt.ply + {base_name}_hole.ply  "
          f"|  V={len(holed_mesh.vertices)} F={len(holed_mesh.faces)} holes~{nh}")


def _seal_pass(mesh):
    """One pass: find every closed boundary loop and fan-triangulate it.
    Returns (new_mesh, num_loops_closed).
    """
    edges = mesh.edges_sorted
    uniq, counts = np.unique(edges, axis=0, return_counts=True)
    border = uniq[counts == 1]
    if len(border) == 0:
        return mesh, 0

    # Unique border vertex adjacency (list; duplicates removed per neighbor)
    adj = collections.defaultdict(set)
    for a, b in border:
        adj[int(a)].add(int(b))
        adj[int(b)].add(int(a))

    # Walk boundary loops. For non-manifold junctions (>2 neighbors), pick any
    # unvisited neighbor and let a later pass catch the other branch.
    visited = set()
    loops = []
    all_bverts = list(adj.keys())
    for seed in all_bverts:
        if seed in visited:
            continue
        loop = [seed]
        visited.add(seed)
        prev = -1
        cur = seed
        ok = True
        for _step in range(len(all_bverts) + 2):
            cand = [n for n in adj[cur] if n != prev]
            if not cand:
                ok = False
                break
            # Prefer unvisited neighbors
            unv = [n for n in cand if n not in visited]
            if unv:
                nxt = unv[0]
            else:
                # Only option is an already-visited vertex; check if we closed
                nxt = cand[0]
            if nxt == seed:
                break  # loop closed
            if nxt in visited:
                ok = False
                break
            visited.add(nxt)
            loop.append(nxt)
            prev, cur = cur, nxt
        else:
            ok = False
        if ok and len(loop) >= 3:
            loops.append(loop)

    if not loops:
        return mesh, 0

    new_verts = list(mesh.vertices)
    new_faces = list(mesh.faces)
    for loop in loops:
        pts = np.array([new_verts[i] for i in loop])
        c = pts.mean(axis=0)
        c_idx = len(new_verts)
        new_verts.append(c)
        for k in range(len(loop)):
            a = loop[k]
            b = loop[(k + 1) % len(loop)]
            new_faces.append([a, b, c_idx])
    sealed = trimesh.Trimesh(vertices=np.array(new_verts),
                             faces=np.array(new_faces), process=False)
    return sealed, len(loops)


def seal_all_holes(mesh, max_passes=5):
    """Iteratively seal boundary loops with centroid fan triangulation.

    Not trying to produce a pretty patch — just a watertight GT so our
    artificial hole is the only opening evaluate.py has to account for.
    """
    for _ in range(max_passes):
        mesh, n = _seal_pass(mesh)
        if n == 0:
            break
    return mesh


def _try_download(urls, cache_path, label):
    """Try each URL in order; cache bytes on success; return loaded trimesh or None."""
    if os.path.exists(cache_path):
        return trimesh.load(cache_path, process=False, force='mesh')
    for url in urls:
        try:
            print(f"  Fetching {label} from {url} ...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if url.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    target = None
                    for name in z.namelist():
                        low = name.lower()
                        if low.endswith('.obj') and 'triangulated' in low:
                            target = name; break
                    if target is None:
                        for name in z.namelist():
                            if name.lower().endswith('.obj'):
                                target = name; break
                    if target is None:
                        print(f"  {label}: no .obj inside zip."); continue
                    with z.open(target) as f:
                        data = f.read()
            with open(cache_path, 'wb') as f:
                f.write(data)
            return trimesh.load(cache_path, process=False, force='mesh')
        except Exception as e:
            print(f"  {label}: {url} failed ({e})")
    return None


def try_fetch_spot():
    """Stanford/Keenan-Crane Spot. The distributed Spot has intentional
    openings (eyes, nostrils, mouth, hooves) that are hard to seal cleanly,
    so we fall back to the watertight `cow.obj` from the same repository —
    a simpler cow model that plays the same role as a non-sphere test case.
    """
    return _try_download(
        [
            "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/cow.obj",
        ],
        os.path.join(OUTPUT_DIR, "_cow.obj"),
        "cow (Spot substitute)")


def try_fetch_bunny():
    return _try_download(
        [
            "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/stanford-bunny.obj",
        ],
        os.path.join(OUTPUT_DIR, "_bunny.obj"),
        "Bunny")


# ── 1-3. Sphere cases ──────────────────────────────────────────────────────
print("1. Sphere - small hole")
sphere = trimesh.creation.icosphere(subdivisions=3)
top = int(np.argmax(sphere.vertices[:, 2]))
bottom = int(np.argmin(sphere.vertices[:, 2]))
save_pair(sphere,
          remove_faces_around_vertex(sphere, top, radius_faces=1),
          "sphere_small")

print("2. Sphere - large hole")
save_pair(sphere,
          remove_faces_around_vertex(sphere, top, radius_faces=2),
          "sphere_large")

print("3. Sphere - 2 holes")
m = remove_faces_around_vertex(sphere, top, radius_faces=1)
m = remove_faces_around_vertex(m, bottom, radius_faces=1)
save_pair(sphere, m, "sphere_two")

# ── 4. Cylinder ────────────────────────────────────────────────────────────
print("4. Cylinder - side hole")
cyl = trimesh.creation.cylinder(radius=1.0, height=3.0, sections=40)
radii = np.sqrt(cyl.vertices[:, 0]**2 + cyl.vertices[:, 1]**2)
side_verts = np.where(radii > radii.max() * 0.9)[0]
save_pair(cyl,
          remove_faces_around_vertex(cyl, int(side_verts[0]), radius_faces=1),
          "cylinder_side")

# ── 5. Torus ───────────────────────────────────────────────────────────────
print("5. Torus - hole")
torus = trimesh.creation.torus(major_radius=2.0, minor_radius=0.5, minor_sections=20)
outer_verts = np.argsort(torus.vertices[:, 0])[-1:]
save_pair(torus,
          remove_faces_around_vertex(torus, int(outer_verts[0]), radius_faces=1),
          "torus")

# ── 6. Stanford Bunny ─────────────────────────────────────────────────────
print("6. Bunny - hole")
bunny = try_fetch_bunny()
if bunny is None:
    # Legacy fallback: user-placed bunny.obj
    legacy = os.path.join(OUTPUT_DIR, "bunny.obj")
    if os.path.exists(legacy):
        bunny = trimesh.load(legacy, process=False, force='mesh')
if bunny is not None:
    top_bunny = int(np.argmax(bunny.vertices[:, 1]))
    save_pair(bunny,
              remove_faces_around_vertex(bunny, top_bunny, radius_faces=2),
              "bunny")
else:
    print("  Bunny skipped (download failed and no local bunny.obj).")

# ── 7. Stanford-style second test model (cow.obj as Spot substitute) ─────
print("7. Cow (Spot substitute) - hole")
spot = try_fetch_spot()
if spot is not None:
    bcount = int((np.unique(spot.edges_sorted, axis=0, return_counts=True)[1] == 1).sum())
    print(f"  pre-existing boundary edges: {bcount}")
    if bcount > 0:
        spot = seal_all_holes(spot)
        bcount = int((np.unique(spot.edges_sorted, axis=0, return_counts=True)[1] == 1).sum())
        print(f"  after sealing: {bcount}")
    top_spot = int(np.argmax(spot.vertices[:, 1]))
    save_pair(spot,
              remove_faces_around_vertex(spot, top_spot, radius_faces=2),
              "spot")

print("\nDone. Files saved to:", OUTPUT_DIR)
