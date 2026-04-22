"""
Evaluate NFD hole filling output against ground truth.

Three metrics (as listed in the proposal):
  - Hausdorff Distance   (symmetric, max closest-point distance in either direction)
  - RMS Error            (root-mean-square of closest-point distances)
  - Normal Deviation     (mean angular difference between filled and GT face normals)

All distances are also reported as a % of the GT bounding-box diagonal so they are
comparable across models of different scale.

Usage:
    python evaluate.py <ground_truth.ply> <filled.ply> [--samples N]
"""

import argparse
import numpy as np
import trimesh


def _load(path):
    m = trimesh.load(path, process=False, force='mesh')
    if not isinstance(m, trimesh.Trimesh):
        raise ValueError(f"{path} did not load as a triangle mesh")
    return m


def evaluate(gt_path, filled_path, sample_count=50000):
    gt = _load(gt_path)
    filled = _load(filled_path)

    bbox_diag = float(np.linalg.norm(gt.bounding_box.extents))
    if bbox_diag < 1e-12:
        bbox_diag = 1.0

    # Sample points uniformly on both surfaces (area-weighted).
    rng = np.random.default_rng(0)
    n = min(sample_count, max(5000, len(filled.faces) * 3))

    samples_f, face_ids_f = filled.sample(n, return_index=True)
    samples_g, face_ids_g = gt.sample(n, return_index=True)

    # Closest-point queries both directions.
    _, dist_f_to_g, tri_g_for_f = gt.nearest.on_surface(samples_f)
    _, dist_g_to_f, _          = filled.nearest.on_surface(samples_g)

    # Hausdorff = max over both directions (symmetric).
    hausdorff = float(max(dist_f_to_g.max(), dist_g_to_f.max()))

    # RMS of filled-surface samples to GT surface (focuses on patch quality).
    rms = float(np.sqrt((dist_f_to_g ** 2).mean()))

    # Normal deviation: angle between filled sample's face normal and GT face normal
    # at the closest point.
    n_f = filled.face_normals[face_ids_f]
    n_g = gt.face_normals[tri_g_for_f]
    n_f = n_f / (np.linalg.norm(n_f, axis=1, keepdims=True) + 1e-12)
    n_g = n_g / (np.linalg.norm(n_g, axis=1, keepdims=True) + 1e-12)
    dots = np.clip((n_f * n_g).sum(axis=1), -1.0, 1.0)
    angles_deg = np.degrees(np.arccos(dots))
    normal_dev_mean = float(angles_deg.mean())
    normal_dev_max = float(angles_deg.max())
    flipped_pct = float((angles_deg > 90.0).mean() * 100.0)

    # Patch-focused metrics: restrict to samples that are far from GT surface.
    # Untouched regions of the filled mesh match GT exactly (distance ~ 0),
    # so the tail of the distance distribution is the newly-filled region.
    patch_mask = dist_f_to_g > (1e-4 * bbox_diag)
    if patch_mask.any():
        patch_rms = float(np.sqrt((dist_f_to_g[patch_mask] ** 2).mean()))
        patch_nd  = float(angles_deg[patch_mask].mean())
    else:
        patch_rms = rms
        patch_nd  = normal_dev_mean

    return {
        'gt_path': gt_path,
        'filled_path': filled_path,
        'gt_faces': int(len(gt.faces)),
        'filled_faces': int(len(filled.faces)),
        'bbox_diag': bbox_diag,
        'samples': int(n),

        'hausdorff': hausdorff,
        'hausdorff_pct': 100.0 * hausdorff / bbox_diag,

        'rms': rms,
        'rms_pct': 100.0 * rms / bbox_diag,

        'normal_dev_mean_deg': normal_dev_mean,
        'normal_dev_max_deg': normal_dev_max,
        'flipped_face_pct': flipped_pct,

        'patch_rms': patch_rms,
        'patch_rms_pct': 100.0 * patch_rms / bbox_diag,
        'patch_normal_dev_mean_deg': patch_nd,
    }


def print_report(r):
    print(f"Ground truth:        {r['gt_path']}   ({r['gt_faces']} faces)")
    print(f"Filled:              {r['filled_path']}   ({r['filled_faces']} faces)")
    print(f"BBox diagonal:       {r['bbox_diag']:.6f}")
    print(f"Samples per surface: {r['samples']}")
    print("-" * 70)
    print(f"Hausdorff distance:  {r['hausdorff']:.6e}   ({r['hausdorff_pct']:.4f}% of bbox)")
    print(f"RMS error (global):  {r['rms']:.6e}   ({r['rms_pct']:.4f}% of bbox)")
    print(f"RMS error (patch):   {r['patch_rms']:.6e}   ({r['patch_rms_pct']:.4f}% of bbox)")
    print(f"Normal dev (global): {r['normal_dev_mean_deg']:.3f}° mean,  "
          f"{r['normal_dev_max_deg']:.3f}° max")
    print(f"Normal dev (patch):  {r['patch_normal_dev_mean_deg']:.3f}° mean")
    print(f"Back-facing samples: {r['flipped_face_pct']:.2f}%   (>90° deviation)")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('gt', help='Ground truth mesh (no hole)')
    ap.add_argument('filled', help='Filled mesh (NFD output)')
    ap.add_argument('--samples', type=int, default=50000,
                    help='Number of surface samples per mesh (default 50000)')
    args = ap.parse_args()
    print_report(evaluate(args.gt, args.filled, args.samples))
