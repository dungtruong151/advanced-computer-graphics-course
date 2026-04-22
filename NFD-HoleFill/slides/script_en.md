# Presentation Script (English) — ~10 minutes

Target pace: ~140 words per minute. Keep eye contact; don't read the slides
— use them as anchors. Timing hints in brackets at the top of each block.

---

## Title slide  [≈ 20 s]

Good morning everyone, my name is Truong Tri Dung, student ID MITIU25208,
and today I'll walk you through my project for IT516 — **Normal Field
Diffusion-Guided Hole Filling on 3D Meshes**. The talk is about 10 minutes,
and I'll leave time for questions at the end.

---

## Slide 1 — The Problem  [≈ 45 s]

Hole filling is a fundamental operation in 3D mesh processing. Whenever we
scan a real object, holes appear — from occlusion, from sensor noise, or
from reflective materials the scanner simply cannot see. Classical methods
like Liepa's 2003 algorithm, advancing-front triangulation, or volumetric
diffusion can close these holes, but the result often looks flat, or
over-smoothed, and it doesn't really conform to the curvature around the
hole. So the challenge is: can we close the hole in a way that
**respects the geometry** of its neighbourhood?

---

## Slide 2 — Our Idea  [≈ 45 s]

Our answer is: yes, if we propagate the right information. Instead of
diffusing only positions — which is what Laplacian-based methods do — we
propagate **normal vectors** from the boundary into the hole. The intuition
is that normals carry the local surface orientation; if we blend boundary
normals smoothly across the patch, we recover a good approximation of how
the missing surface was tilting. Then we displace the patch vertices along
those diffused normals to actually *build* the surface. So the approach
uses differential geometry — normals plus curvature — rather than pure
positional smoothing.

---

## Slide 3 — Six-Step Pipeline  [≈ 40 s]

Here is the full pipeline. Given a mesh with a hole, we first trace the
boundary edge loops — step 1. Step 2 builds an initial triangulation of
the hole with ear clipping plus centroid subdivision. Step 3 computes
per-vertex normals and mean curvature on the boundary. Step 4 — the
highlighted one, the core of the method — diffuses those normals into the
interior using the heat equation. Step 5 displaces the interior vertices
along the diffused normals. And step 6 runs a light smoothing pass. I'll
now go through the steps that matter the most.

---

## Slide 4 — Boundary Analysis  [≈ 40 s]

At every boundary vertex we extract two quantities. First, the **vertex
normal**, computed as an area-weighted average of adjacent face normals.
Second, the **mean curvature**, via the cotangent Laplacian — that's the
classical formula with weights equal to `cot α + cot β` on each edge.
These two quantities tell us where the surface is heading at the
boundary, and how fast it's bending. They become the **Dirichlet boundary
conditions** for the diffusion equation we'll solve next.

---

## Slide 5 — Normal Field Diffusion (Core)  [≈ 70 s]

This is the core of the method. We treat the patch as a small mesh and
solve the **heat equation** on it: the partial derivative of the normal
with respect to time equals lambda times the Laplacian of the normal. We
hold the boundary normals fixed — Dirichlet conditions — and we discretise
with **implicit Euler**. That gives a linear system: identity plus lambda
times the cotangent Laplacian, times the new normal field, equals the old
field plus a boundary-contribution term. The matrix is sparse and
symmetric positive definite, so we assemble it once and factor it with
**Eigen's SimplicialLDLT**, then we reuse the factor for every iteration.
The result is a smooth normal field that blends the boundary orientations
across the entire patch.

---

## Slide 6 — Curvature-Guided Displacement  [≈ 55 s]

Once each interior vertex has a normal, we move it along that normal by
an amount `d`. We use a **spherical-cap profile** — this is the analytic
height of a small circle sitting on a sphere. The scale factor uses the
mean boundary radius and the spread of the boundary normals, so it's
self-calibrating. The profile uses `t`, the **geodesic distance** to the
boundary normalised to the range zero to one — we compute it with
Dijkstra. The effect is that the patch domes out smoothly from the
boundary and peaks at the centre, just like a spherical cap that
continues the surrounding curvature.

---

## Slide 7 — Delaunay Edge Flipping  [≈ 50 s]

Ear clipping and centroid subdivision give us a *valid* triangulation,
but not an *optimal* one — we get sliver triangles around junction
vertices. The classic fix, taught in class, is the **max-min-angle edge
flip**: for every interior edge shared by two triangles, flip the
diagonal whenever it increases the minimum interior angle. We run it
twice — once after ear clipping, once after centroid subdivision. It
matters for us because cotangent weights blow up on slivers; removing
them keeps our Laplacian well-conditioned. On the left you can see the
raw triangulation with slivers; on the right, the cleaned-up version
after the two passes.

---

## Slide 8 — Post-Processing  [≈ 30 s]

After displacement we run two short smoothing passes, both keeping the
boundary vertices fixed. First, a **constrained Laplacian** that
redistributes interior vertices evenly. Second, **Taubin's
lambda-mu smoothing** — alternating shrink and inflate — which removes
per-vertex spikes without shrinking the overall dome. This gives us a
clean, well-triangulated patch.

---

## Slide 9 — Implementation and Parameters  [≈ 55 s]

The plugin is written in C++14, using the VCG Library for mesh
operations and Eigen 3 for the sparse solver. It integrates into the
MeshLab build via CMake, and appears under `Filters > Remeshing > NFD
Hole Filling`. The table lists the seven user parameters. The ones
people most often adjust are **CurvatureStrength** — lower it if the
patch bulges too much — and **RefinementFactor** — lower that if you
want a denser patch or if slivers survive. Everything else is safe at
defaults.

---

## Slide 10 — Visual Results  [≈ 35 s]

Here's a typical before-and-after. On the left, the input mesh with a
hole on its surface. On the right, the same mesh after running the NFD
filter with default parameters. Notice how the patch doesn't just
flatten the hole — it follows the surrounding curvature and blends
smoothly with the boundary.

---

## Slide 11 — Quantitative Evaluation  [≈ 60 s]

For numerical evaluation we used MeshLab's built-in **Hausdorff Distance
filter** in both directions — filled against ground truth, and ground
truth against filled. The main takeaway is in the RMS column: on
every tested model the forward RMS is well below two tenths of a
percent of the bounding-box diagonal. That means the patch vertices sit
essentially on the true surface. The Hausdorff maxes are dominated by
single-point peaks — on the bunny it's a corner of an ear, on the cow
it's a density-limited region — but the mean and RMS remain very small.

---

## Slide 12 — Conclusion  [≈ 40 s]

To summarise: NFD produces geometrically consistent patches with
sub-one-percent forward RMS on every model we tested, and it integrates
cleanly into MeshLab. Beyond the proposal we added Delaunay edge-flipping
for triangulation quality, a spherical-cap displacement profile with
self-calibrating scale, and Taubin smoothing to remove spikes. For
future work, a per-vertex scale driven by local mean curvature would
let the patch adapt to non-spherical regions, and sharp-feature
preservation would make the method useful for CAD-like inputs.

---

## Thank-You slide  [≈ 10 s]

That's all from me. Thank you for listening, and I'm happy to take any
questions.
