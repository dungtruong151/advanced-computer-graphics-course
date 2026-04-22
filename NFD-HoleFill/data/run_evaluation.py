"""
Batch evaluation runner.

Looks for every pair  <name>_gt.ply  /  <name>_filled.ply  under data/input/,
runs evaluate.evaluate(), prints a summary table, and writes it to
data/evaluation_results.md so the numbers can be pasted into the report.

Workflow:
  1. python generate_test_meshes.py              # creates *_gt.ply and *_hole.ply
  2. (in MeshLab) apply NFD filter to each *_hole.ply, save as *_filled.ply
  3. python run_evaluation.py                    # reads the pairs, prints a table
"""

import glob
import os
import sys

from evaluate import evaluate


INPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
REPORT    = os.path.join(os.path.dirname(__file__), "evaluation_results.md")


def find_pairs():
    pairs = []
    for gt in sorted(glob.glob(os.path.join(INPUT_DIR, "*_gt.ply"))):
        base = os.path.basename(gt)[:-len("_gt.ply")]
        filled = os.path.join(INPUT_DIR, base + "_filled.ply")
        if os.path.exists(filled):
            pairs.append((base, gt, filled))
    return pairs


def main():
    pairs = find_pairs()
    if not pairs:
        print("No <name>_filled.ply files found in data/input/.")
        print("Apply NFD filter in MeshLab on each *_hole.ply and export as *_filled.ply.")
        return 1

    rows = []
    for name, gt, filled in pairs:
        print(f"\n=== {name} ===")
        r = evaluate(gt, filled, sample_count=50000)
        print(f"  Hausdorff     : {r['hausdorff']:.6e}   ({r['hausdorff_pct']:.4f}%)")
        print(f"  RMS (global)  : {r['rms']:.6e}   ({r['rms_pct']:.4f}%)")
        print(f"  RMS (patch)   : {r['patch_rms']:.6e}   ({r['patch_rms_pct']:.4f}%)")
        print(f"  Normal dev    : {r['normal_dev_mean_deg']:.3f}° mean, "
              f"{r['normal_dev_max_deg']:.3f}° max")
        print(f"  Back-facing   : {r['flipped_face_pct']:.2f}% (>90°)")
        rows.append((name, r))

    # Write a markdown table for the report.
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("# NFD Hole Filling - Evaluation Results\n\n")
        f.write("All distances reported as % of the ground-truth bounding-box diagonal.\n\n")
        f.write("| Model | Hausdorff % | RMS (global) % | RMS (patch) % | "
                "Normal dev (mean) | Back-facing % |\n")
        f.write("|-------|------------:|---------------:|--------------:|"
                "------------------:|--------------:|\n")
        for name, r in rows:
            f.write(f"| {name} | {r['hausdorff_pct']:.4f} | {r['rms_pct']:.4f} | "
                    f"{r['patch_rms_pct']:.4f} | {r['normal_dev_mean_deg']:.2f}° | "
                    f"{r['flipped_face_pct']:.2f} |\n")
        f.write("\nRaw absolute distances (BBox diagonal in parentheses):\n\n")
        f.write("| Model | BBox diag | Hausdorff | RMS | Normal dev max |\n")
        f.write("|-------|----------:|----------:|----:|---------------:|\n")
        for name, r in rows:
            f.write(f"| {name} | {r['bbox_diag']:.4f} | {r['hausdorff']:.4e} | "
                    f"{r['rms']:.4e} | {r['normal_dev_max_deg']:.2f}° |\n")

    print(f"\nReport written to: {REPORT}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
