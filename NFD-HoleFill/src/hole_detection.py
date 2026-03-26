"""
Step 1: Hole Detection
Detect boundary loops (holes) in a triangle mesh.
A boundary edge belongs to exactly one triangle.
"""

import numpy as np
from collections import defaultdict


def find_boundary_edges(faces):
    """
    Find all boundary edges in a mesh.
    A boundary edge is shared by exactly one face.

    Returns: list of (v1, v2) tuples representing boundary edges
    """
    edge_count = defaultdict(int)
    edge_to_face = defaultdict(list)

    for fi, face in enumerate(faces):
        for i in range(3):
            v1, v2 = face[i], face[(i + 1) % 3]
            edge = (min(v1, v2), max(v1, v2))
            edge_count[edge] += 1
            edge_to_face[edge].append(fi)

    boundary_edges = []
    for edge, count in edge_count.items():
        if count == 1:
            # Keep original orientation from the face
            boundary_edges.append(edge)

    return boundary_edges


def extract_boundary_loops(boundary_edges):
    """
    Connect boundary edges into ordered loops.
    Each loop represents one hole in the mesh.

    Returns: list of loops, where each loop is a list of vertex indices
    """
    if not boundary_edges:
        return []

    # Build adjacency for boundary vertices
    adj = defaultdict(set)
    for v1, v2 in boundary_edges:
        adj[v1].add(v2)
        adj[v2].add(v1)

    visited_edges = set()
    loops = []

    for start_v1, start_v2 in boundary_edges:
        edge_key = (min(start_v1, start_v2), max(start_v1, start_v2))
        if edge_key in visited_edges:
            continue

        # Trace loop starting from this edge
        loop = [start_v1]
        current = start_v1
        prev = None

        while True:
            neighbors = adj[current]
            # Pick next vertex (not the one we came from)
            next_v = None
            for n in neighbors:
                ek = (min(current, n), max(current, n))
                if n != prev and ek not in visited_edges:
                    next_v = n
                    break

            if next_v is None:
                break

            edge_key = (min(current, next_v), max(current, next_v))
            visited_edges.add(edge_key)

            if next_v == loop[0]:
                # Loop closed
                break

            loop.append(next_v)
            prev = current
            current = next_v

        if len(loop) >= 3:
            loops.append(loop)

    # Sort loops by size (largest first)
    loops.sort(key=len, reverse=True)

    return loops


def detect_holes(mesh):
    """
    Main function: detect all holes in a trimesh mesh.

    Returns: list of boundary loops (each loop = list of vertex indices)
    """
    boundary_edges = find_boundary_edges(mesh.faces)

    if not boundary_edges:
        print("No holes detected in the mesh.")
        return []

    loops = extract_boundary_loops(boundary_edges)

    print(f"Detected {len(loops)} hole(s):")
    for i, loop in enumerate(loops):
        print(f"  Hole {i}: {len(loop)} boundary vertices")

    return loops
