"""
Run NFD-HoleFill on real meshes (bunny, spot, etc.)
Creates artificial holes and compares NFD vs Baseline vs Ground Truth.
"""

import sys
import os
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mesh_io import save_mesh
from pipeline import NFDHoleFiller
from baseline import flat_fill_with_smoothing
from evaluate import evaluate
from visualize import visualize_comparison, plot_metrics_comparison


def create_hole_in_mesh(mesh, hole_size=50, seed=42):
    """Create an artificial hole in a mesh by removing adjacent faces."""
    rng = np.random.default_rng(seed)
    original = mesh.copy()
    adjacency = mesh.face_adjacency

    seed_face = rng.integers(0, len(mesh.faces))

    # BFS to find adjacent faces
    to_remove = {seed_face}
    frontier = {seed_face}
    while len(to_remove) < hole_size and frontier:
        new_frontier = set()
        for f in frontier:
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
    keep_mask = np.ones(len(mesh.faces), dtype=bool)
    keep_mask[remove_indices] = False
    mesh.update_faces(keep_mask)
    mesh.remove_unreferenced_vertices()

    print(f"Created hole: removed {len(remove_indices)} faces")
    print(f"  Before: {len(original.faces)} faces")
    print(f"  After:  {len(mesh.faces)} faces")

    return mesh, original


def run_on_mesh(mesh_path, hole_size=50, seed=42, output_name=None):
    """Run full pipeline on a single mesh."""

    if output_name is None:
        output_name = os.path.splitext(os.path.basename(mesh_path))[0]

    output_dir = os.path.join('..', 'results', output_name)
    os.makedirs(output_dir, exist_ok=True)

    # Load mesh
    print(f"\n{'#' * 60}")
    print(f"# Processing: {mesh_path}")
    print(f"{'#' * 60}")

    mesh = trimesh.load(mesh_path, force='mesh', process=False)
    print(f"Loaded: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

    # Create hole
    mesh_with_hole, ground_truth = create_hole_in_mesh(mesh, hole_size, seed)

    save_mesh(ground_truth, os.path.join(output_dir, '00_ground_truth.ply'))
    save_mesh(mesh_with_hole, os.path.join(output_dir, '01_with_hole.ply'))

    # Run NFD
    print(f"\n--- NFD-HoleFill ---")
    filler = NFDHoleFiller(
        lambda_param=1.0, dt=0.1, diffusion_iterations=100,
        displacement_scale=2.0, smooth_iterations=5, smooth_alpha=0.5
    )
    filled_nfd, stats_nfd = filler.fill_holes(mesh_with_hole)
    save_mesh(filled_nfd, os.path.join(output_dir, '02_filled_nfd.ply'))

    # Run Baseline
    print(f"\n--- Baseline ---")
    filled_baseline, stats_base = flat_fill_with_smoothing(
        mesh_with_hole, smooth_iterations=10, smooth_alpha=0.5
    )
    save_mesh(filled_baseline, os.path.join(output_dir, '03_filled_baseline.ply'))

    # Evaluate
    eval_results = evaluate(ground_truth, filled_nfd, filled_baseline, n_samples=10000)

    # Save charts
    plot_metrics_comparison(
        eval_results,
        save_path=os.path.join(output_dir, 'metrics_comparison.png')
    )

    # Save comparison image
    try:
        visualize_comparison(
            ground_truth, mesh_with_hole, filled_nfd, filled_baseline,
            screenshot_path=os.path.join(output_dir, 'comparison.png')
        )
    except Exception as e:
        print(f"Visualization error (non-critical): {e}")

    return eval_results


if __name__ == '__main__':
    data_dir = os.path.join('..', 'data', 'input')

    all_results = {}

    # Test on Spot (smaller, faster)
    spot_path = os.path.join(data_dir, 'spot.obj')
    if os.path.exists(spot_path):
        all_results['spot'] = run_on_mesh(spot_path, hole_size=30, seed=42)

    # Test on Bunny (larger, more detail)
    bunny_path = os.path.join(data_dir, 'bunny.obj')
    if os.path.exists(bunny_path):
        all_results['bunny'] = run_on_mesh(bunny_path, hole_size=100, seed=42)

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY OF ALL RESULTS")
    print(f"{'=' * 60}")
    for name, res in all_results.items():
        print(f"\n{name}:")
        for method in ['nfd', 'baseline']:
            if method in res:
                r = res[method]
                print(f"  {method:10s} | Hausdorff: {r['hausdorff_max']:.6f} | "
                      f"RMS: {r['rms_error']:.6f} | Normal: {r['normal_deviation_deg']:.2f} deg")
