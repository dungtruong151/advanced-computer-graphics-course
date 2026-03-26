"""
NFD-HoleFill: Main Demo Script

Usage:
    python main.py                     # Run with generated test mesh
    python main.py --input mesh.ply    # Run with custom mesh file
    python main.py --help              # Show all options
"""

import argparse
import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mesh_io import load_mesh, save_mesh, create_test_mesh_with_hole
from pipeline import NFDHoleFiller
from baseline import flat_fill_with_smoothing
from evaluate import evaluate
from visualize import (visualize_comparison, plot_metrics_comparison,
                       visualize_mesh)


def run_demo(args):
    """Run the full NFD-HoleFill demo."""

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # --- Load or create test mesh ---
    if args.input:
        print(f"\nLoading mesh from: {args.input}")
        mesh_with_hole = load_mesh(args.input)
        ground_truth = None
        print("NOTE: No ground truth available for custom meshes.")
        print("      Evaluation metrics will not be computed.\n")
    else:
        print("\nGenerating test mesh (icosphere with artificial hole)...")
        mesh_with_hole, ground_truth, removed_faces = create_test_mesh_with_hole(
            hole_size=args.hole_size, seed=args.seed
        )
        # Save test meshes
        save_mesh(ground_truth,
                  os.path.join(output_dir, "00_ground_truth.ply"))
        save_mesh(mesh_with_hole,
                  os.path.join(output_dir, "01_with_hole.ply"))

    # --- Run NFD-HoleFill (our method) ---
    print("\n" + "#" * 60)
    print("# Running NFD-HoleFill (Our Method)")
    print("#" * 60)

    filler = NFDHoleFiller(
        lambda_param=args.lambda_param,
        dt=args.dt,
        diffusion_iterations=args.diffusion_iter,
        displacement_scale=args.disp_scale,
        smooth_iterations=args.smooth_iter,
        smooth_alpha=args.smooth_alpha
    )
    filled_nfd, stats_nfd = filler.fill_holes(mesh_with_hole)
    save_mesh(filled_nfd, os.path.join(output_dir, "02_filled_nfd.ply"))

    # --- Run Baseline ---
    print("\n" + "#" * 60)
    print("# Running Baseline (Flat Fill + Laplacian Smoothing)")
    print("#" * 60)

    filled_baseline, stats_baseline = flat_fill_with_smoothing(
        mesh_with_hole,
        smooth_iterations=args.smooth_iter * 2,  # Give baseline more smoothing
        smooth_alpha=args.smooth_alpha
    )
    save_mesh(filled_baseline, os.path.join(output_dir, "03_filled_baseline.ply"))

    # --- Evaluate ---
    eval_results = None
    if ground_truth is not None:
        eval_results = evaluate(
            ground_truth, filled_nfd, filled_baseline,
            n_samples=args.eval_samples
        )

        # Save metrics chart
        plot_metrics_comparison(
            eval_results,
            save_path=os.path.join(output_dir, "metrics_comparison.png")
        )

    # --- Visualize ---
    if not args.no_viz:
        print("\nOpening 3D visualization...")
        visualize_comparison(
            mesh_original=ground_truth if ground_truth else mesh_with_hole,
            mesh_with_hole=mesh_with_hole,
            mesh_nfd=filled_nfd,
            mesh_baseline=filled_baseline,
            screenshot_path=os.path.join(output_dir, "comparison.png")
            if args.screenshot else None
        )

    print("\nAll outputs saved to:", output_dir)
    return eval_results


def main():
    parser = argparse.ArgumentParser(
        description="NFD-HoleFill: Normal Field Diffusion-Guided Hole Filling"
    )

    # Input/Output
    parser.add_argument('--input', '-i', type=str, default=None,
                        help='Input mesh file (PLY, OBJ, STL). If not given, uses test mesh.')
    parser.add_argument('--output-dir', '-o', type=str,
                        default='../results',
                        help='Output directory for results')

    # Test mesh parameters
    parser.add_argument('--hole-size', type=int, default=15,
                        help='Number of faces to remove for test hole (default: 15)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for test mesh generation')

    # Algorithm parameters
    parser.add_argument('--lambda-param', type=float, default=1.0,
                        help='Diffusion coefficient (default: 1.0)')
    parser.add_argument('--dt', type=float, default=0.1,
                        help='Diffusion time step (default: 0.1)')
    parser.add_argument('--diffusion-iter', type=int, default=50,
                        help='Max diffusion iterations (default: 50)')
    parser.add_argument('--disp-scale', type=float, default=1.0,
                        help='Displacement scale factor (default: 1.0)')
    parser.add_argument('--smooth-iter', type=int, default=3,
                        help='Laplacian smoothing iterations (default: 3)')
    parser.add_argument('--smooth-alpha', type=float, default=0.5,
                        help='Laplacian smoothing weight (default: 0.5)')

    # Evaluation
    parser.add_argument('--eval-samples', type=int, default=10000,
                        help='Number of samples for evaluation (default: 10000)')

    # Visualization
    parser.add_argument('--no-viz', action='store_true',
                        help='Disable 3D visualization')
    parser.add_argument('--screenshot', action='store_true',
                        help='Save screenshot instead of interactive view')

    args = parser.parse_args()
    run_demo(args)


if __name__ == '__main__':
    main()
