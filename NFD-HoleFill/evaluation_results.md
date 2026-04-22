# NFD Hole Filling — Evaluation Results

Measured with MeshLab's built-in **`Filters > Sampling > Hausdorff Distance`**
filter, run in both directions on each NFD-filled mesh against its ground truth.

- **Forward** = samples on *filled* mesh, closest point on *GT*
  → measures how far the filled patch deviates from the true surface
- **Reverse** = samples on *GT*, closest point on *filled*
  → measures how well the filled mesh covers the original surface
- **Symmetric Hausdorff** = `max(forward.max, reverse.max)` (the formal metric)

All `%` values are relative to the ground-truth bounding-box diagonal (as
reported by MeshLab in the *"Values w.r.t. BBox Diag"* block).

---

## Summary

| Model        | BBox diag | Hausdorff (sym.) | Hausdorff % | RMS (fwd) | RMS % | Notes |
|--------------|----------:|-----------------:|------------:|----------:|------:|-------|
| sphere_small | 3.464     | 4.260e-03        | 0.123 %     | 2.370e-04 | 0.007 % |  |
| sphere_large | 3.464     | 2.055e-02        | 0.592 %     | 2.095e-03 | 0.060 % |  |
| torus        | 7.141     | 2.447e-02        | 0.343 %     | 5.600e-05 | 0.001 % | reverse-direction dominated |
| cow          | 12.713    | 3.316e-01        | 2.609 %     | 1.443e-03 | 0.011 % | reverse direction dominates — see note |
| bunny        | 0.251     | 8.783e-03        | 3.498 %     | 4.550e-04 | 0.181 % | six separate holes, most patch error on the sharpest one |

RMS column uses the **forward** direction (filled → GT) because that is the
one that reports patch-surface accuracy. Reverse-direction RMS is shown in
the raw table below for completeness.

---

## Raw MeshLab numbers

All four rows per model are verbatim from the MeshLab log.

### sphere_small (BBox diag 3.464)

| Direction | min | max | mean | RMS |
|-----------|----:|----:|-----:|----:|
| filled → GT (644 samples) | 0.000000 | 0.004260 | 0.000013 | 0.000237 |
| &nbsp;&nbsp;% bbox        | 0.0000 % | 0.1230 % | 0.0004 % | 0.0069 % |
| GT → filled (642 samples) | 0.000000 | 0.000136 | 0.000000 | 0.000005 |
| &nbsp;&nbsp;% bbox        | 0.0000 % | 0.0039 % | 0.0000 % | 0.0002 % |

### sphere_large (BBox diag 3.464)

| Direction | min | max | mean | RMS |
|-----------|----:|----:|-----:|----:|
| filled → GT (652 samples) | 0.000000 | 0.020548 | 0.000255 | 0.002095 |
| &nbsp;&nbsp;% bbox        | 0.0000 % | 0.5915 % | 0.0073 % | 0.0603 % |
| GT → filled (642 samples) | 0.000000 | 0.017026 | 0.000073 | 0.001017 |
| &nbsp;&nbsp;% bbox        | 0.0000 % | 0.4915 % | 0.0021 % | 0.0293 % |

### torus (BBox diag 7.141)

| Direction | min | max | mean | RMS |
|-----------|----:|----:|-----:|----:|
| filled → GT (1920 samples) | 0.000000 | 0.002460 | 0.000001 | 0.000056 |
| &nbsp;&nbsp;% bbox         | 0.0000 % | 0.0345 % | 0.0000 % | 0.0008 % |
| GT → filled (1920 samples) | 0.000000 | 0.024472 | 0.000020 | 0.000630 |
| &nbsp;&nbsp;% bbox         | 0.0000 % | 0.3427 % | 0.0003 % | 0.0088 % |

### cow (BBox diag 12.713)

| Direction | min | max | mean | RMS |
|-----------|----:|----:|-----:|----:|
| filled → GT (2911 samples) | 0.000000 | 0.065758 | 0.000057 | 0.001443 |
| &nbsp;&nbsp;% bbox         | 0.0000 % | 0.5173 % | 0.0004 % | 0.0114 % |
| GT → filled (2903 samples) | 0.000000 | 0.331609 | 0.000337 | 0.007320 |
| &nbsp;&nbsp;% bbox         | 0.0000 % | 2.6088 % | 0.0027 % | 0.0576 % |

### bunny (BBox diag 0.251)

| Direction | min | max | mean | RMS |
|-----------|----:|----:|-----:|----:|
| filled → GT (35370 samples) | 0.000000 | 0.008783 | 0.000048 | 0.000455 |
| &nbsp;&nbsp;% bbox          | 0.0000 % | 3.498 %  | 0.0192 % | 0.1811 % |
| GT → filled (34834 samples) | 0.000000 | 0.000396 | 0.000000 | 0.000004 |
| &nbsp;&nbsp;% bbox          | 0.0000 % | 0.1584 % | 0.0000 % | 0.0014 % |

---

## Observations

**Sphere (small / large).** Forward and reverse magnitudes are similar, both
well under 1 % of the bounding-box diagonal. The large hole produces ~5× the
error of the small hole, which is the expected behavior — a larger hole leaves
the patch less constrained by boundary normals so the curvature-guided
displacement has more room to deviate from the true sphere.

**Bunny.** Forward Hausdorff max is the largest in the whole set at 3.5 % of
the bbox diagonal. That number is dominated by a single peak on one of the
six holes (likely the sharpest one, near the top of the ears). Mean and RMS
remain very low (0.02 % and 0.18 %), so the overall patch quality is fine;
the Hausdorff max captures a worst-case vertex rather than average behavior.

**Cow.** The *reverse*-direction Hausdorff dominates here (2.6 % bbox vs
0.5 % forward). That pattern means the NFD patch is slightly smaller than the
region the hole originally covered — some GT points near the hole boundary
don't have an equally close counterpart on the filled mesh. The forward RMS
is still very low (0.011 %), so the patch that was produced sits on the true
surface; it just doesn't fully span the removed region on the long axis.

**Torus.** Forward error is essentially zero (max 0.035 %, RMS 0.001 %) —
the NFD patch lies right on the true torus surface. The reverse direction
shows 0.343 % bbox because the hole was cut across a highly curved section
of the torus and a few GT points near the far side of the hole don't have
a patch vertex directly above them; those are resolvable by increasing
`RefinementFactor` so the patch carries more interior vertices.
