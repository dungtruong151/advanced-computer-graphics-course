"""
Evaluation: Compare NFD-HoleFill vs Baseline vs Ground Truth.

Metrics:
1. Hausdorff Distance (max surface deviation)
2. RMS Error (average vertex deviation)
3. Normal Deviation (average angle difference in normals)
"""

import numpy as np
import trimesh


def hausdorff_distance(mesh_a, mesh_b, n_samples=10000):
    """
    Compute one-sided Hausdorff distance from mesh_a to mesh_b.
    Sample points on mesh_a, find closest point on mesh_b.

    Returns: (max_dist, mean_dist)
    """
    # Sample points on mesh_a
    points_a, _ = trimesh.sample.sample_surface(mesh_a, n_samples)

    # Find closest points on mesh_b
    closest, distances, _ = mesh_b.nearest.on_surface(points_a)

    return float(np.max(distances)), float(np.mean(distances))


def symmetric_hausdorff(mesh_a, mesh_b, n_samples=10000):
    """Symmetric Hausdorff distance = max of both one-sided distances."""
    max_ab, mean_ab = hausdorff_distance(mesh_a, mesh_b, n_samples)
    max_ba, mean_ba = hausdorff_distance(mesh_b, mesh_a, n_samples)

    return max(max_ab, max_ba), (mean_ab + mean_ba) / 2.0


def rms_error(mesh_a, mesh_b, n_samples=10000):
    """
    Root Mean Square error between two meshes.
    Sample points on mesh_a, find distances to mesh_b.
    """
    points_a, _ = trimesh.sample.sample_surface(mesh_a, n_samples)
    _, distances, _ = mesh_b.nearest.on_surface(points_a)
    return float(np.sqrt(np.mean(distances ** 2)))


def normal_deviation(mesh_filled, mesh_ground_truth, n_samples=5000):
    """
    Average angular deviation of normals between filled mesh and ground truth.
    Sample points on filled mesh, find corresponding normals on ground truth.

    Returns: mean angle deviation in degrees
    """
    # Sample points and face indices on filled mesh
    points, face_indices = trimesh.sample.sample_surface(mesh_filled, n_samples)

    # Get normals at sampled points from filled mesh
    normals_filled = mesh_filled.face_normals[face_indices]

    # Find closest points on ground truth and their normals
    closest, distances, triangle_ids = mesh_ground_truth.nearest.on_surface(points)
    normals_gt = mesh_ground_truth.face_normals[triangle_ids]

    # Compute angle between normals
    dots = np.sum(normals_filled * normals_gt, axis=1)
    dots = np.clip(dots, -1.0, 1.0)
    angles = np.degrees(np.arccos(np.abs(dots)))  # abs because normal could be flipped

    return float(np.mean(angles))


def evaluate(ground_truth, filled_nfd, filled_baseline=None, n_samples=10000):
    """
    Full evaluation comparing NFD result (and optionally baseline) against ground truth.

    Returns: dict with all metrics
    """
    results = {}

    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)

    # Evaluate NFD method
    print("\n--- NFD-HoleFill ---")
    h_max, h_mean = symmetric_hausdorff(filled_nfd, ground_truth, n_samples)
    rms = rms_error(filled_nfd, ground_truth, n_samples)
    normal_dev = normal_deviation(filled_nfd, ground_truth, n_samples // 2)

    results['nfd'] = {
        'hausdorff_max': h_max,
        'hausdorff_mean': h_mean,
        'rms_error': rms,
        'normal_deviation_deg': normal_dev
    }

    print(f"  Hausdorff (max):   {h_max:.6f}")
    print(f"  Hausdorff (mean):  {h_mean:.6f}")
    print(f"  RMS Error:         {rms:.6f}")
    print(f"  Normal Deviation:  {normal_dev:.2f} deg")

    # Evaluate baseline if provided
    if filled_baseline is not None:
        print("\n--- Baseline (Flat + Smooth) ---")
        h_max_b, h_mean_b = symmetric_hausdorff(filled_baseline, ground_truth, n_samples)
        rms_b = rms_error(filled_baseline, ground_truth, n_samples)
        normal_dev_b = normal_deviation(filled_baseline, ground_truth, n_samples // 2)

        results['baseline'] = {
            'hausdorff_max': h_max_b,
            'hausdorff_mean': h_mean_b,
            'rms_error': rms_b,
            'normal_deviation_deg': normal_dev_b
        }

        print(f"  Hausdorff (max):   {h_max_b:.6f}")
        print(f"  Hausdorff (mean):  {h_mean_b:.6f}")
        print(f"  RMS Error:         {rms_b:.6f}")
        print(f"  Normal Deviation:  {normal_dev_b:.2f} deg")

        # Improvement
        print("\n--- Improvement (NFD vs Baseline) ---")
        if h_max_b > 0:
            print(f"  Hausdorff (max):  {(1 - h_max/h_max_b)*100:+.1f}%")
        if rms_b > 0:
            print(f"  RMS Error:        {(1 - rms/rms_b)*100:+.1f}%")
        if normal_dev_b > 0:
            print(f"  Normal Deviation: {(1 - normal_dev/normal_dev_b)*100:+.1f}%")

    print("=" * 60)
    return results
