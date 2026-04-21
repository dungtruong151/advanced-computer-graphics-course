#include "filter_nfd_holefill.h"

#include <vcg/complex/algorithms/update/topology.h>
#include <vcg/complex/algorithms/update/normal.h>
#include <vcg/complex/algorithms/update/bounding.h>
#include <vcg/complex/algorithms/update/flag.h>
#include <vcg/complex/algorithms/update/curvature.h>
#include <vcg/complex/algorithms/hole.h>
#include <vcg/complex/algorithms/smooth.h>
#include <vcg/complex/allocate.h>
#include <Eigen/Sparse>
#include <Eigen/Dense>
#include <cmath>
#include <set>
#include <map>
#include <queue>
#include <vector>
#include <algorithm>
#include <limits>
// ===================================================================
// Static helpers
// ===================================================================

// Cotangent of the angle at vertex A in triangle (A, B, C)
static double cotAngle(const Point3m& A, const Point3m& B, const Point3m& C)
{
	Point3m AB = B - A, AC = C - A;
	double d = (double)(AB * AC);
	double c = (double)(AB ^ AC).Norm();
	if (c < 1e-12) return 0.0;
	return d / c;
}

// Build a local 2D orthonormal frame from a normal vector
static void buildLocalFrame(const Point3m& normal, Point3m& uAxis, Point3m& vAxis)
{
	Point3m n = normal;
	double nlen = (double)n.Norm();
	if (nlen < 1e-10) { uAxis = Point3m(1,0,0); vAxis = Point3m(0,1,0); return; }
	n /= (Scalarm)nlen;
	Point3m ref(1,0,0);
	if (std::fabs((double)(n * ref)) > 0.9)
		ref = Point3m(0,1,0);
	uAxis = n ^ ref;
	double ulen = (double)uAxis.Norm();
	if (ulen < 1e-10) { uAxis = Point3m(1,0,0); vAxis = Point3m(0,1,0); return; }
	uAxis /= (Scalarm)ulen;
	vAxis = n ^ uAxis;
	double vlen = (double)vAxis.Norm();
	if (vlen > 1e-10) vAxis /= (Scalarm)vlen;
}

// 2D cross product: (ax, ay) x (bx, by)
static double cross2D(double ax, double ay, double bx, double by)
{
	return ax * by - ay * bx;
}

// Is point P inside (or on) CCW triangle (A, B, C) in 2D?
static bool pointInTriangle2D(
	double px, double py,
	double ax, double ay,
	double bx, double by,
	double cx, double cy)
{
	double d1 = cross2D(bx - ax, by - ay, px - ax, py - ay);
	double d2 = cross2D(cx - bx, cy - by, px - bx, py - by);
	double d3 = cross2D(ax - cx, ay - cy, px - cx, py - cy);
	return (d1 >= -1e-10) && (d2 >= -1e-10) && (d3 >= -1e-10);
}

// ===================================================================
// Plugin boilerplate
// ===================================================================

FilterNFDHoleFillPlugin::FilterNFDHoleFillPlugin()
{
	typeList = {FP_NFD_HOLEFILL};
	for (ActionIDType tt : types())
		actionList.push_back(new QAction(filterName(tt), this));
}

FilterNFDHoleFillPlugin::~FilterNFDHoleFillPlugin() {}

QString FilterNFDHoleFillPlugin::pluginName() const
{
	return "FilterNFDHoleFill";
}

QString FilterNFDHoleFillPlugin::filterName(ActionIDType filterId) const
{
	switch (filterId) {
	case FP_NFD_HOLEFILL: return "NFD Hole Filling";
	default: assert(0); return QString();
	}
}

QString FilterNFDHoleFillPlugin::pythonFilterName(ActionIDType f) const
{
	switch (f) {
	case FP_NFD_HOLEFILL: return "apply_nfd_hole_filling";
	default: assert(0); return QString();
	}
}

QString FilterNFDHoleFillPlugin::filterInfo(ActionIDType filterId) const
{
	switch (filterId) {
	case FP_NFD_HOLEFILL:
		return "Fill holes using Normal Field Diffusion (NFD). "
		       "This method creates an initial triangulation of each hole, "
		       "then diffuses boundary normal vectors into the patch using "
		       "heat-equation-based diffusion, and finally displaces interior "
		       "vertices along the diffused normals guided by local curvature. "
		       "This produces geometrically consistent hole filling that "
		       "respects the surrounding surface shape.";
	default: assert(0); return "Unknown Filter";
	}
}

FilterNFDHoleFillPlugin::FilterClass FilterNFDHoleFillPlugin::getClass(const QAction* a) const
{
	switch (ID(a)) {
	case FP_NFD_HOLEFILL: return FilterPlugin::Remeshing;
	default: assert(0); return FilterPlugin::Generic;
	}
}

FilterPlugin::FilterArity FilterNFDHoleFillPlugin::filterArity(const QAction*) const
{
	return SINGLE_MESH;
}

int FilterNFDHoleFillPlugin::getPreConditions(const QAction*) const
{
	return MeshModel::MM_FACENUMBER;
}

int FilterNFDHoleFillPlugin::postCondition(const QAction*) const
{
	return MeshModel::MM_VERTCOORD | MeshModel::MM_FACENORMAL | MeshModel::MM_VERTNORMAL;
}

RichParameterList FilterNFDHoleFillPlugin::initParameterList(const QAction* action, const MeshModel& m)
{
	RichParameterList parlst;
	switch (ID(action)) {
	case FP_NFD_HOLEFILL:
		parlst.addParam(RichInt("MaxHoleSize", 100,
			"Max Hole Size (edges)",
			"Maximum number of boundary edges for a hole to be filled. "
			"Holes larger than this will be skipped."));
		parlst.addParam(RichInt("DiffusionIterations", 50,
			"Diffusion Iterations",
			"Number of iterations for the normal field diffusion. "
			"Higher values produce smoother normal fields but are slower."));
		parlst.addParam(RichFloat("DiffusionLambda", 0.5f,
			"Diffusion Lambda",
			"Diffusion coefficient controlling the speed of normal propagation. "
			"Values between 0.1 and 1.0 are recommended."));
		parlst.addParam(RichInt("SmoothingIterations", 3,
			"Smoothing Iterations",
			"Number of Laplacian smoothing iterations applied to the filled patch."));
		parlst.addParam(RichFloat("RefinementFactor", 1.0f,
			"Refinement Factor",
			"Target triangle edge length as a multiple of the average boundary edge. "
			"Smaller = finer (more detail), larger = coarser. "
			"1.0 = match boundary density, 0.5 = ~4x finer, 2.0 = coarser."));
		parlst.addParam(RichFloat("CurvatureStrength", 1.0f,
			"Curvature Strength",
			"Multiplier on the dome height. "
			"0.0 = flat patch (no bending), 1.0 = full spherical-cap fit, "
			"2.0 = exaggerated. Lower this if the patch overshoots on non-spherical "
			"objects (e.g. bunny, torus)."));
		break;
	default: assert(0);
	}
	return parlst;
}

// ===================================================================
// Main apply function
// ===================================================================

std::map<std::string, QVariant> FilterNFDHoleFillPlugin::applyFilter(
	const QAction* action,
	const RichParameterList& parameters,
	MeshDocument& md,
	unsigned int& /*postConditionMask*/,
	vcg::CallBackPos* cb)
{
	switch (ID(action)) {
	case FP_NFD_HOLEFILL: {
		CMeshO& m = md.mm()->cm;

		int maxHoleSize      = parameters.getInt("MaxHoleSize");
		int diffIterations   = parameters.getInt("DiffusionIterations");
		Scalarm diffLambda   = parameters.getFloat("DiffusionLambda");
		int smoothIterations = parameters.getInt("SmoothingIterations");
		Scalarm refinementFactor = parameters.getFloat("RefinementFactor");
		if (refinementFactor < (Scalarm)0.1) refinementFactor = (Scalarm)0.1;
		Scalarm curvatureStrength = parameters.getFloat("CurvatureStrength");
		if (curvatureStrength < (Scalarm)0) curvatureStrength = (Scalarm)0;

		// Step 0: Enable Ocf optional components and update topology
		cb(0, "Updating topology...");
		m.face.EnableFFAdjacency();
		m.face.EnableVFAdjacency();
		m.vert.EnableVFAdjacency();
		vcg::tri::UpdateTopology<CMeshO>::FaceFace(m);
		vcg::tri::UpdateTopology<CMeshO>::VertexFace(m);
		vcg::tri::UpdateFlags<CMeshO>::FaceBorderFromFF(m);
		vcg::tri::UpdateFlags<CMeshO>::VertexBorderFromFaceBorder(m);
		vcg::tri::UpdateNormal<CMeshO>::PerVertexNormalizedPerFace(m);

		// Step 1: Detect holes
		cb(5, "Detecting holes...");
		log("NFD: Detecting holes (maxSize=%d)...", maxHoleSize);
		std::vector<HoleBoundary> holes = detectHoles(m, maxHoleSize);

		if (holes.empty()) {
			log("No holes found (or all holes exceed max size).");
			break;
		}
		log("Found %d hole(s) to fill.", (int)holes.size());

		int totalHoles = (int)holes.size();
		for (int hi = 0; hi < totalHoles; hi++) {
			int baseProgress = 10 + (80 * hi / totalHoles);
			cb(baseProgress, ("Processing hole " + std::to_string(hi + 1) + "/" + std::to_string(totalHoles) + "...").c_str());

			log("NFD: Hole %d/%d: %d boundary vertices.", hi+1, totalHoles, (int)holes[hi].vertexIndices.size());

			// Step 2: Compute boundary normals and curvature (cotangent Laplacian)
			computeBoundaryInfo(m, holes[hi]);

			// Step 3: Initial triangulation (ear clipping + interior vertex refinement)
			PatchMesh patch = triangulatePatch(holes[hi], refinementFactor);

			if (patch.faces.empty()) {
				log("NFD:   WARNING: empty patch, skipping hole %d.", hi+1);
				continue;
			}

			// Validate patch face indices before proceeding
			bool patchValid = true;
			for (size_t fi = 0; fi < patch.faces.size(); fi++) {
				for (int k = 0; k < 3; k++) {
					if (patch.faces[fi][k] < 0 || patch.faces[fi][k] >= (int)patch.vertices.size()) {
						log("NFD:   ERROR: face %d has invalid vertex index %d (max=%d)",
						    (int)fi, patch.faces[fi][k], (int)patch.vertices.size()-1);
						patchValid = false;
					}
				}
			}
			if (!patchValid) {
				log("NFD:   Skipping hole %d due to invalid patch.", hi+1);
				continue;
			}

			// Step 4: Normal field diffusion via cotangent heat equation (CORE)
			diffuseNormalField(patch, diffIterations, diffLambda);

			// Check for NaN in normals after diffusion
			bool hasNaN = false;
			for (size_t vi = 0; vi < patch.normals.size(); vi++) {
				if (std::isnan(patch.normals[vi][0]) || std::isnan(patch.normals[vi][1]) || std::isnan(patch.normals[vi][2])) {
					hasNaN = true;
					break;
				}
			}
			if (hasNaN) {
				log("NFD:   WARNING: NaN in normals after diffusion, resetting to avg.");
				Point3m avgN(0,0,0);
				for (size_t bi = 0; bi < patch.numBoundaryVerts; bi++) avgN += patch.normals[bi];
				Scalarm nlen = avgN.Norm();
				if (nlen > 1e-10) avgN /= nlen;
				for (size_t vi = patch.numBoundaryVerts; vi < patch.normals.size(); vi++)
					patch.normals[vi] = avgN;
			}

			// Step 5: Laplacian smoothing of the still-flat patch to redistribute
			//         interior vertices evenly before bending
			smoothPatch(patch, smoothIterations);

			// Step 6: Curvature-guided displacement (final — must come after smoothing,
			//         otherwise uniform Laplacian averages out the dome)
			displaceVertices(patch, holes[hi], curvatureStrength);

			// Step 7: Merge patch into mesh
			mergePatchIntoMesh(m, patch, holes[hi]);
		}

		// Final updates
		cb(95, "Updating normals...");
		vcg::tri::UpdateTopology<CMeshO>::FaceFace(m);
		vcg::tri::UpdateNormal<CMeshO>::PerVertexNormalizedPerFace(m);
		vcg::tri::UpdateNormal<CMeshO>::PerFaceNormalized(m);
		vcg::tri::UpdateBounding<CMeshO>::Box(m);

		log("NFD Hole Filling completed: %d hole(s) filled.", totalHoles);
		cb(100, "Done.");
		break;
	}
	default: wrongActionCalled(action);
	}
	return std::map<std::string, QVariant>();
}

// ===================================================================
// Step 1: Hole Detection
// ===================================================================

std::vector<FilterNFDHoleFillPlugin::HoleBoundary>
FilterNFDHoleFillPlugin::detectHoles(CMeshO& m, int maxHoleSize)
{
	std::vector<HoleBoundary> holes;

	vcg::tri::UpdateFlags<CMeshO>::FaceBorderFromFF(m);
	vcg::tri::UpdateFlags<CMeshO>::VertexBorderFromFaceBorder(m);

	std::set<std::pair<size_t, size_t>> visitedEdges;

	for (auto fi = m.face.begin(); fi != m.face.end(); ++fi) {
		if (fi->IsD()) continue;
		for (int ei = 0; ei < 3; ei++) {
			if (vcg::face::IsBorder(*fi, ei)) {
				size_t vi = vcg::tri::Index(m, fi->V(ei));
				size_t vj = vcg::tri::Index(m, fi->V((ei + 1) % 3));

				if (visitedEdges.count({vi, vj})) continue;

				HoleBoundary hole;
				size_t startV = vi;
				size_t curV   = vi;
				size_t nextV  = vj;

				bool loopComplete = false;
				int safety = 0;

				while (safety < maxHoleSize * 2) {
					safety++;
					hole.vertexIndices.push_back(curV);
					visitedEdges.insert({curV, nextV});

					size_t prevV = curV;
					curV = nextV;
					if (curV == startV) {
						loopComplete = true;
						break;
					}
					bool foundNext = false;

					CMeshO::VertexPointer vp = &m.vert[curV];
					vcg::face::VFIterator<CMeshO::FaceType> vfi(vp);
					for (; !vfi.End(); ++vfi) {
						CMeshO::FacePointer fp = vfi.F();
						for (int e = 0; e < 3; e++) {
							size_t eV0 = vcg::tri::Index(m, fp->V(e));
							size_t eV1 = vcg::tri::Index(m, fp->V((e + 1) % 3));
							if (eV0 == curV && eV1 != prevV && vcg::face::IsBorder(*fp, e)) {
								nextV = eV1;
								foundNext = true;
								break;
							}
						}
						if (foundNext) break;
					}

					if (!foundNext) break;
				}

				if (loopComplete && (int)hole.vertexIndices.size() >= 3 &&
				    (int)hole.vertexIndices.size() <= maxHoleSize) {
					hole.positions.resize(hole.vertexIndices.size());
					for (size_t i = 0; i < hole.vertexIndices.size(); i++)
						hole.positions[i] = m.vert[hole.vertexIndices[i]].P();
					holes.push_back(hole);
				}
			}
		}
	}

	return holes;
}

// ===================================================================
// Step 2: Compute Boundary Info
//
// Vertex normals: area-weighted per-vertex normals from VCG.
// Mean curvature: cotangent Laplacian H(v) = |L_cot(v)| / 2
//   w_ij = cot(alpha_ij) + cot(beta_ij)  (angles opposite edge vi-vj)
//   L_cot(v) = (sum_j w_ij*(vj-v)) / (sum_j w_ij)
// ===================================================================

void FilterNFDHoleFillPlugin::computeBoundaryInfo(CMeshO& m, HoleBoundary& hole)
{
	size_t n = hole.vertexIndices.size();
	hole.normals.resize(n);
	hole.meanCurvatures.resize(n);

	for (size_t i = 0; i < n; i++) {
		CMeshO::VertexPointer vp = &m.vert[hole.vertexIndices[i]];

		// Area-weighted per-vertex normal from mesh
		hole.normals[i] = vp->N();
		Scalarm len = hole.normals[i].Norm();
		if (len > 1e-10) hole.normals[i] /= len;

		// Mean curvature via cotangent Laplacian
		// For each adjacent face, accumulate cotangent weights for each edge
		std::map<size_t, double> cotWeights;

		vcg::face::VFIterator<CMeshO::FaceType> vfi(vp);
		for (; !vfi.End(); ++vfi) {
			CMeshO::FacePointer fp  = vfi.F();
			int                 il  = vfi.I();  // local index of vi in this face

			// Face vertices: A = vi, B = next, C = prev (in face order)
			CMeshO::VertexPointer vA = fp->V(il);
			CMeshO::VertexPointer vB = fp->V((il + 1) % 3);
			CMeshO::VertexPointer vC = fp->V((il + 2) % 3);

			size_t idB = vcg::tri::Index(m, vB);
			size_t idC = vcg::tri::Index(m, vC);

			Point3m pA = vA->P(), pB = vB->P(), pC = vC->P();

			// Edge vi-vB: opposite angle is at vC
			double cotC = cotAngle(pC, pA, pB);
			// Edge vi-vC: opposite angle is at vB
			double cotB = cotAngle(pB, pA, pC);

			cotWeights[idB] += cotC;
			cotWeights[idC] += cotB;
		}

		// Weighted Laplacian vector
		Point3m laplacian(0, 0, 0);
		double  totalW = 0;
		for (auto& kv : cotWeights) {
			double w = std::max(kv.second, 0.0);  // clamp negative cotangents
			laplacian += (m.vert[kv.first].P() - vp->P()) * (Scalarm)w;
			totalW += w;
		}
		hole.meanCurvatures[i] = (totalW > 1e-10)
		    ? (double)(laplacian.Norm() / (Scalarm)(2.0 * totalW))
		    : 0.0;
	}
}

// ===================================================================
// Step 3: Initial Triangulation
//
// Ear clipping on the 2D projection of the boundary polygon, then
// refine large triangles by inserting their centroids as interior
// vertices (centroid subdivision).
// ===================================================================

FilterNFDHoleFillPlugin::PatchMesh
FilterNFDHoleFillPlugin::triangulatePatch(const HoleBoundary& hole, Scalarm refinementFactor)
{
	PatchMesh patch;
	size_t n = hole.vertexIndices.size();

	for (size_t i = 0; i < n; i++) {
		patch.vertices.push_back(hole.positions[i]);
		patch.isBoundary.push_back(true);
	}

	// Average boundary normal for the local frame
	Point3m avgNormal(0, 0, 0);
	for (size_t i = 0; i < n; i++) avgNormal += hole.normals[i];
	Scalarm anlen = avgNormal.Norm();
	if (anlen > 1e-10) avgNormal /= anlen;

	// Build local 2D frame
	Point3m uAxis, vAxis;
	buildLocalFrame(avgNormal, uAxis, vAxis);

	// Project boundary vertices to 2D (relative to centroid)
	Point3m centroid3D(0, 0, 0);
	for (size_t i = 0; i < n; i++) centroid3D += hole.positions[i];
	centroid3D /= (Scalarm)n;

	std::vector<double> px(n), py(n);
	for (size_t i = 0; i < n; i++) {
		Point3m d = hole.positions[i] - centroid3D;
		px[i] = (double)(d * uAxis);
		py[i] = (double)(d * vAxis);
	}

	// Signed area via shoelace (positive = CCW)
	double signedArea2 = 0;
	for (size_t i = 0; i < n; i++) {
		size_t j = (i + 1) % n;
		signedArea2 += px[i] * py[j] - px[j] * py[i];
	}

	// vertOrder maps processing index -> original boundary vertex index
	// If CW polygon, reverse the order so we process CCW
	std::vector<int> vertOrder(n);
	for (int i = 0; i < (int)n; i++) vertOrder[i] = i;
	if (signedArea2 < 0)
		std::reverse(vertOrder.begin(), vertOrder.end());

	// Reorder 2D coords to match vertOrder
	std::vector<double> opx(n), opy(n);
	for (int i = 0; i < (int)n; i++) {
		opx[i] = px[vertOrder[i]];
		opy[i] = py[vertOrder[i]];
	}

	// ---- Ear clipping ----
	// poly holds current processing indices into opx/opy (and vertOrder)
	std::vector<int> poly(n);
	for (int i = 0; i < (int)n; i++) poly[i] = i;

	// Minimum interior angle of triangle (a,b,c) in 2D — used to pick the
	// "best" ear (most equilateral) and avoid fan-from-single-pivot artifacts.
	auto triMinAngle2D = [](double ax, double ay, double bx, double by,
	                        double cx, double cy) -> double {
		double lab = std::sqrt((bx-ax)*(bx-ax) + (by-ay)*(by-ay));
		double lbc = std::sqrt((cx-bx)*(cx-bx) + (cy-by)*(cy-by));
		double lca = std::sqrt((ax-cx)*(ax-cx) + (ay-cy)*(ay-cy));
		if (lab < 1e-12 || lbc < 1e-12 || lca < 1e-12) return 0.0;
		double cosA = ((bx-ax)*(cx-ax) + (by-ay)*(cy-ay)) / (lab * lca);
		double cosB = ((ax-bx)*(cx-bx) + (ay-by)*(cy-by)) / (lab * lbc);
		double cosC = ((ax-cx)*(bx-cx) + (ay-cy)*(by-cy)) / (lca * lbc);
		cosA = std::max(-1.0, std::min(1.0, cosA));
		cosB = std::max(-1.0, std::min(1.0, cosB));
		cosC = std::max(-1.0, std::min(1.0, cosC));
		double angA = std::acos(cosA);
		double angB = std::acos(cosB);
		double angC = std::acos(cosC);
		return std::min({angA, angB, angC});
	};

	while (poly.size() > 3) {
		int m = (int)poly.size();
		bool found = false;

		// Scan ALL ears, pick the one with the largest minimum angle
		// (most equilateral, avoids thin sliver fan patterns).
		int    bestI        = -1;
		double bestMinAngle = -1.0;

		for (int i = 0; i < m; i++) {
			int pa = poly[(i - 1 + m) % m];
			int pb = poly[i];
			int pc = poly[(i + 1) % m];

			double ax = opx[pa], ay = opy[pa];
			double bx = opx[pb], by = opy[pb];
			double cx = opx[pc], cy = opy[pc];

			// CCW convexity check
			if (cross2D(bx - ax, by - ay, cx - ax, cy - ay) <= 1e-12)
				continue;

			// No other polygon vertex inside this ear triangle
			bool isEar = true;
			for (int j = 0; j < m && isEar; j++) {
				if (j == (i - 1 + m) % m || j == i || j == (i + 1) % m)
					continue;
				if (pointInTriangle2D(opx[poly[j]], opy[poly[j]],
				                      ax, ay, bx, by, cx, cy))
					isEar = false;
			}
			if (!isEar) continue;

			double minAng = triMinAngle2D(ax, ay, bx, by, cx, cy);
			if (minAng > bestMinAngle) {
				bestMinAngle = minAng;
				bestI        = i;
			}
		}

		if (bestI >= 0) {
			int m2 = (int)poly.size();
			int pa = poly[(bestI - 1 + m2) % m2];
			int pb = poly[bestI];
			int pc = poly[(bestI + 1) % m2];
			patch.faces.push_back(
			    vcg::Point3i(vertOrder[pa], vertOrder[pb], vertOrder[pc]));
			poly.erase(poly.begin() + bestI);
			found = true;
		}

		if (!found) {
			// Fallback: clip the first convex vertex (handles near-degenerate cases)
			bool clipped = false;
			for (int i = 0; i < (int)poly.size() && !clipped; i++) {
				int m2 = (int)poly.size();
				int pa = poly[(i - 1 + m2) % m2];
				int pb = poly[i];
				int pc = poly[(i + 1) % m2];
				if (cross2D(opx[pb] - opx[pa], opy[pb] - opy[pa],
				            opx[pc] - opx[pa], opy[pc] - opy[pa]) > 0) {
					patch.faces.push_back(
					    vcg::Point3i(vertOrder[pa], vertOrder[pb], vertOrder[pc]));
					poly.erase(poly.begin() + i);
					clipped = true;
				}
			}
			if (!clipped) {
				// Last resort: force-clip vertex 1 (avoid infinite loop)
				if (poly.size() > 3) {
					patch.faces.push_back(vcg::Point3i(
					    vertOrder[poly[0]], vertOrder[poly[1]], vertOrder[poly[2]]));
					poly.erase(poly.begin() + 1);
				} else break;
			}
		}
	}

	// Final triangle
	if (poly.size() == 3)
		patch.faces.push_back(
		    vcg::Point3i(vertOrder[poly[0]], vertOrder[poly[1]], vertOrder[poly[2]]));

	// Post-hoc winding fix: ensure face normals align with avgNormal
	if (!patch.faces.empty()) {
		auto& f  = patch.faces[0];
		Point3m AB = patch.vertices[f[1]] - patch.vertices[f[0]];
		Point3m AC = patch.vertices[f[2]] - patch.vertices[f[0]];
		if ((AB ^ AC) * avgNormal < 0) {
			for (auto& face : patch.faces)
				std::swap(face[1], face[2]);
		}
	}

	// ---- Delaunay-like edge flipping (max-min-angle quality improvement) ----
	// Ear clipping only guarantees a valid triangulation, not an optimal one.
	// For each interior edge shared by two triangles P=(u,v,w) and Q=(v,u,x),
	// consider flipping to diagonal (w,x): P'=(u,x,w), Q'=(v,w,x). Accept the
	// flip if it increases the minimum interior angle across the two faces.
	// Iterate until no flip improves quality.
	auto triMinAngle3D = [&](int ai, int bi, int ci) -> double {
		Point3m A = patch.vertices[ai], B = patch.vertices[bi], C = patch.vertices[ci];
		double lab = (double)(B - A).Norm();
		double lac = (double)(C - A).Norm();
		double lbc = (double)(C - B).Norm();
		if (lab < 1e-12 || lac < 1e-12 || lbc < 1e-12) return 0.0;
		double cosA = (double)((B - A) * (C - A)) / (lab * lac);
		double cosB = (double)((A - B) * (C - B)) / (lab * lbc);
		double cosC = (double)((A - C) * (B - C)) / (lac * lbc);
		cosA = std::max(-1.0, std::min(1.0, cosA));
		cosB = std::max(-1.0, std::min(1.0, cosB));
		cosC = std::max(-1.0, std::min(1.0, cosC));
		return std::min({std::acos(cosA), std::acos(cosB), std::acos(cosC)});
	};

	auto edgeKey = [](int a, int b) {
		return std::make_pair(std::min(a, b), std::max(a, b));
	};

	for (int flipPass = 0; flipPass < 10; flipPass++) {
		std::map<std::pair<int, int>, std::vector<int>> edgeFaces;
		for (int fi = 0; fi < (int)patch.faces.size(); fi++) {
			const auto& f = patch.faces[fi];
			for (int k = 0; k < 3; k++)
				edgeFaces[edgeKey(f[k], f[(k + 1) % 3])].push_back(fi);
		}

		bool          anyFlip = false;
		std::set<int> touched;
		for (auto& kv : edgeFaces) {
			auto& faces = kv.second;
			if (faces.size() != 2) continue;  // boundary or non-manifold
			int f1 = faces[0], f2 = faces[1];
			if (touched.count(f1) || touched.count(f2)) continue;

			int u = kv.first.first, v = kv.first.second;
			const auto& t1 = patch.faces[f1];
			const auto& t2 = patch.faces[f2];
			int w = -1, x = -1;
			for (int k = 0; k < 3; k++) {
				if (t1[k] != u && t1[k] != v) w = t1[k];
				if (t2[k] != u && t2[k] != v) x = t2[k];
			}
			if (w < 0 || x < 0 || w == x) continue;

			// Skip if new diagonal would connect two already-adjacent verts
			if (edgeFaces.count(edgeKey(w, x))) continue;

			double currMin = std::min(triMinAngle3D(u, v, w),
			                          triMinAngle3D(v, u, x));
			double flipMin = std::min(triMinAngle3D(u, x, w),
			                          triMinAngle3D(v, w, x));

			if (flipMin <= currMin + 1e-6) continue;

			// Build new faces and auto-fix winding against avgNormal
			// (the flipped vertex set is correct; only ordering may need a swap).
			vcg::Point3i nf1(u, x, w), nf2(v, w, x);
			auto fixWinding = [&](vcg::Point3i& f) {
				Point3m N = (patch.vertices[f[1]] - patch.vertices[f[0]]) ^
				            (patch.vertices[f[2]] - patch.vertices[f[0]]);
				if (N * avgNormal < 0) std::swap(f[1], f[2]);
			};
			fixWinding(nf1);
			fixWinding(nf2);

			patch.faces[f1] = nf1;
			patch.faces[f2] = nf2;
			touched.insert(f1);
			touched.insert(f2);
			anyFlip = true;
		}
		if (!anyFlip) break;
	}

	// ---- Iterative centroid refinement to reach target triangle size ----
	auto triArea3D = [&](const vcg::Point3i& f) -> double {
		Point3m AB = patch.vertices[f[1]] - patch.vertices[f[0]];
		Point3m AC = patch.vertices[f[2]] - patch.vertices[f[0]];
		return (double)(AB ^ AC).Norm() * 0.5;
	};

	// Target triangle area = equilateral triangle with side = refinementFactor * avgBoundaryEdge
	double avgBdEdge = 0;
	for (size_t i = 0; i < n; i++) {
		Point3m a = hole.positions[i];
		Point3m b = hole.positions[(i + 1) % n];
		avgBdEdge += (double)(b - a).Norm();
	}
	if (n > 0) avgBdEdge /= (double)n;

	double targetSide = avgBdEdge * (double)refinementFactor;
	double targetArea = (targetSide * targetSide) * 0.4330127;  // sqrt(3)/4

	const int maxPasses = 8;
	const size_t hardCapFaces = 200000;
	if (targetArea > 0) {
		for (int pass = 0; pass < maxPasses; pass++) {
			if (patch.faces.size() > hardCapFaces) break;
			std::vector<vcg::Point3i> newFaces;
			newFaces.reserve(patch.faces.size());
			bool anySplit = false;
			for (auto& f : patch.faces) {
				double a = triArea3D(f);
				if (a > targetArea * 1.5) {
					Point3m c = (patch.vertices[f[0]] + patch.vertices[f[1]] +
					             patch.vertices[f[2]]) / (Scalarm)3.0;
					int cIdx = (int)patch.vertices.size();
					patch.vertices.push_back(c);
					patch.isBoundary.push_back(false);
					newFaces.push_back(vcg::Point3i(f[0], f[1], cIdx));
					newFaces.push_back(vcg::Point3i(f[1], f[2], cIdx));
					newFaces.push_back(vcg::Point3i(f[2], f[0], cIdx));
					anySplit = true;
				} else {
					newFaces.push_back(f);
				}
			}
			patch.faces = newFaces;
			if (!anySplit) break;
		}
	}

	// ---- Second Delaunay-like edge-flip pass after refinement ----
	// Centroid subdivision can introduce new slivers around the inserted
	// interior vertex; clean them up the same way.
	for (int flipPass = 0; flipPass < 10; flipPass++) {
		std::map<std::pair<int, int>, std::vector<int>> edgeFaces;
		for (int fi = 0; fi < (int)patch.faces.size(); fi++) {
			const auto& f = patch.faces[fi];
			for (int k = 0; k < 3; k++)
				edgeFaces[edgeKey(f[k], f[(k + 1) % 3])].push_back(fi);
		}

		bool          anyFlip = false;
		std::set<int> touched;
		for (auto& kv : edgeFaces) {
			auto& faces = kv.second;
			if (faces.size() != 2) continue;
			int f1 = faces[0], f2 = faces[1];
			if (touched.count(f1) || touched.count(f2)) continue;

			int u = kv.first.first, v = kv.first.second;
			const auto& t1 = patch.faces[f1];
			const auto& t2 = patch.faces[f2];
			int w = -1, x = -1;
			for (int k = 0; k < 3; k++) {
				if (t1[k] != u && t1[k] != v) w = t1[k];
				if (t2[k] != u && t2[k] != v) x = t2[k];
			}
			if (w < 0 || x < 0 || w == x) continue;
			if (edgeFaces.count(edgeKey(w, x))) continue;

			double currMin = std::min(triMinAngle3D(u, v, w),
			                          triMinAngle3D(v, u, x));
			double flipMin = std::min(triMinAngle3D(u, x, w),
			                          triMinAngle3D(v, w, x));
			if (flipMin <= currMin + 1e-6) continue;

			vcg::Point3i nf1(u, x, w), nf2(v, w, x);
			auto fixWinding2 = [&](vcg::Point3i& f) {
				Point3m N = (patch.vertices[f[1]] - patch.vertices[f[0]]) ^
				            (patch.vertices[f[2]] - patch.vertices[f[0]]);
				if (N * avgNormal < 0) std::swap(f[1], f[2]);
			};
			fixWinding2(nf1);
			fixWinding2(nf2);

			patch.faces[f1] = nf1;
			patch.faces[f2] = nf2;
			touched.insert(f1);
			touched.insert(f2);
			anyFlip = true;
		}
		if (!anyFlip) break;
	}

	// Initialize normals: copy boundary normals; interior = avgNormal
	patch.normals.resize(patch.vertices.size(), avgNormal);
	for (size_t i = 0; i < n; i++)
		patch.normals[i] = hole.normals[i];

	patch.numBoundaryVerts = n;
	return patch;
}

// ===================================================================
// Step 4: Normal Field Diffusion (CORE)
//
// Solves the heat equation on the patch mesh using cotangent Laplacian
// and implicit Euler integration (multiple steps):
//
//   (I + lambda * L_cot) * n^{t+1} = n^{t} + lambda * sum_boundary(w*n_b)
//
// Boundary normals are fixed (Dirichlet conditions).
// System is assembled once; solved iteratively with updated RHS.
// ===================================================================

void FilterNFDHoleFillPlugin::diffuseNormalField(PatchMesh& patch, int iterations, Scalarm lambda)
{
	size_t nVerts    = patch.vertices.size();
	size_t nBoundary = patch.numBoundaryVerts;
	size_t nInterior = nVerts - nBoundary;

	if (nInterior == 0) return;

	// Build adjacency from faces
	std::vector<std::set<size_t>> adj(nVerts);
	for (const auto& f : patch.faces) {
		adj[f[0]].insert(f[1]); adj[f[0]].insert(f[2]);
		adj[f[1]].insert(f[0]); adj[f[1]].insert(f[2]);
		adj[f[2]].insert(f[0]); adj[f[2]].insert(f[1]);
	}

	// Compute cotangent weights for each undirected edge
	// w_{ij} = sum of cot(angle_opposite) over all triangles sharing edge (i,j)
	std::map<std::pair<size_t, size_t>, double> cotW;
	for (const auto& f : patch.faces) {
		size_t a = f[0], b = f[1], c = f[2];
		Point3m pA = patch.vertices[a];
		Point3m pB = patch.vertices[b];
		Point3m pC = patch.vertices[c];

		// Angle at A → opposite edge (B,C)
		double cotA = cotAngle(pA, pB, pC);
		// Angle at B → opposite edge (A,C)
		double cotB = cotAngle(pB, pA, pC);
		// Angle at C → opposite edge (A,B)
		double cotC = cotAngle(pC, pA, pB);

		auto key_bc = std::make_pair(std::min(b,c), std::max(b,c));
		auto key_ac = std::make_pair(std::min(a,c), std::max(a,c));
		auto key_ab = std::make_pair(std::min(a,b), std::max(a,b));

		cotW[key_bc] += cotA;
		cotW[key_ac] += cotB;
		cotW[key_ab] += cotC;
	}

	// Map interior vertices to compact indices 0..nInterior-1
	std::vector<int>    interiorMap(nVerts, -1);
	std::vector<size_t> interiorVerts;
	for (size_t i = nBoundary; i < nVerts; i++) {
		interiorMap[i] = (int)interiorVerts.size();
		interiorVerts.push_back(i);
	}

	typedef Eigen::SparseMatrix<double> SpMat;
	typedef Eigen::Triplet<double>      Trip;

	// Helper: get cotangent weight for edge (vi, vj), fallback to 1 if missing
	auto getW = [&](size_t vi, size_t vj) -> double {
		auto key = std::make_pair(std::min(vi,vj), std::max(vi,vj));
		auto it  = cotW.find(key);
		double w = (it != cotW.end()) ? it->second : 1.0;
		return std::max(w, 0.0);  // clamp negative cotangents
	};

	// Build system matrix A = I + lambda * L_cot
	// A_ii = 1 + lambda * sum_ALL_j(w_ij)
	// A_ij = -lambda * w_ij   (interior neighbor j only)
	std::vector<Trip> triplets;
	std::vector<double> rowSumW(nInterior, 0.0);

	for (size_t ii = 0; ii < nInterior; ii++) {
		size_t vi = interiorVerts[ii];
		for (size_t vj : adj[vi]) {
			double w = getW(vi, vj);
			rowSumW[ii] += w;
			if (interiorMap[vj] >= 0)
				triplets.push_back(Trip(ii, interiorMap[vj], -lambda * w));
		}
		triplets.push_back(Trip(ii, ii, 1.0 + (double)lambda * rowSumW[ii]));
	}

	SpMat A(nInterior, nInterior);
	A.setFromTriplets(triplets.begin(), triplets.end());

	Eigen::SimplicialLDLT<SpMat> solver;
	solver.compute(A);
	if (solver.info() != Eigen::Success) return;

	// Initialize with current interior normals (before diffusion)
	Eigen::MatrixXd normals(nInterior, 3);
	for (size_t ii = 0; ii < nInterior; ii++) {
		size_t vi = interiorVerts[ii];
		normals(ii, 0) = patch.normals[vi][0];
		normals(ii, 1) = patch.normals[vi][1];
		normals(ii, 2) = patch.normals[vi][2];
	}

	// Iterative implicit Euler steps:
	// Each step: (I + lambda*L) * n_new = n_prev + lambda * sum_boundary(w_ij * n_bj)
	for (int iter = 0; iter < iterations; iter++) {
		Eigen::MatrixXd rhs(nInterior, 3);
		for (size_t ii = 0; ii < nInterior; ii++) {
			size_t vi = interiorVerts[ii];
			rhs(ii, 0) = normals(ii, 0);
			rhs(ii, 1) = normals(ii, 1);
			rhs(ii, 2) = normals(ii, 2);

			// Boundary neighbor contributions (Dirichlet boundary condition)
			for (size_t vj : adj[vi]) {
				if (interiorMap[vj] < 0) {  // boundary vertex
					double w = getW(vi, vj);
					rhs(ii, 0) += (double)lambda * w * (double)patch.normals[vj][0];
					rhs(ii, 1) += (double)lambda * w * (double)patch.normals[vj][1];
					rhs(ii, 2) += (double)lambda * w * (double)patch.normals[vj][2];
				}
			}
		}
		normals = solver.solve(rhs);
	}

	// Write back diffused normals (normalized)
	for (size_t ii = 0; ii < nInterior; ii++) {
		size_t  vi = interiorVerts[ii];
		Point3m n((Scalarm)normals(ii,0), (Scalarm)normals(ii,1), (Scalarm)normals(ii,2));
		Scalarm len = n.Norm();
		if (len > 1e-10) n /= len;
		patch.normals[vi] = n;
	}
}

// ===================================================================
// Step 5: Curvature-Guided Vertex Displacement
//
// v_i' = v_i + d_i * n_diffused(i)
// d_i  = H_avg * avgEdgeLen * g(t_i)
// t_i  = geodesic distance to boundary (Dijkstra, normalized 0..1)
// g(t) = 4*t*(1-t)  peaks at t=0.5
// ===================================================================

void FilterNFDHoleFillPlugin::displaceVertices(PatchMesh& patch, const HoleBoundary& hole, Scalarm curvatureStrength)
{
	size_t nBoundary = patch.numBoundaryVerts;
	size_t nVerts    = patch.vertices.size();

	if (curvatureStrength <= (Scalarm)0) return;  // 0 = flat patch, skip displacement entirely

	// Geometry-based scale: treat the hole as a spherical cap whose boundary
	// lies on a small circle. Cap height h = r * tan(theta/2), where
	//   r     = mean boundary radius (distance from centroid to boundary)
	//   theta = max angle between any boundary normal and the average normal
	// This gives a correct dome height regardless of mesh density, and falls
	// to zero on flat patches (all boundary normals parallel).
	Point3m centroid(0, 0, 0);
	for (size_t i = 0; i < nBoundary; i++)
		centroid += hole.positions[i];
	if (nBoundary > 0) centroid /= (Scalarm)nBoundary;

	Scalarm holeRadius = 0;
	for (size_t i = 0; i < nBoundary; i++)
		holeRadius += (hole.positions[i] - centroid).Norm();
	if (nBoundary > 0) holeRadius /= (Scalarm)nBoundary;

	Point3m avgN(0, 0, 0);
	for (size_t i = 0; i < nBoundary; i++)
		avgN += hole.normals[i];
	Scalarm alen = avgN.Norm();
	if (alen > (Scalarm)1e-10) avgN /= alen;

	// Use AVERAGE angle instead of max — robust on non-spherical objects
	// (bunny, torus) where a few boundary normals may deviate wildly and
	// make max-angle a poor estimate of "how domed" the patch should be.
	Scalarm sumDot = (Scalarm)0;
	for (size_t i = 0; i < nBoundary; i++) {
		Scalarm d = hole.normals[i] * avgN;
		sumDot += d;
	}
	Scalarm avgDot = (nBoundary > 0) ? (sumDot / (Scalarm)nBoundary) : (Scalarm)1;
	if (avgDot < (Scalarm)-1) avgDot = (Scalarm)-1;
	if (avgDot > (Scalarm) 1) avgDot = (Scalarm) 1;
	double  theta = std::acos((double)avgDot);
	Scalarm scale = holeRadius * (Scalarm)std::tan(theta * 0.5) * curvatureStrength;

	// Build adjacency with edge lengths for Dijkstra
	std::vector<std::vector<std::pair<size_t, Scalarm>>> adj(nVerts);
	for (const auto& f : patch.faces) {
		for (int k = 0; k < 3; k++) {
			size_t  a = (size_t)f[k], b = (size_t)f[(k + 1) % 3];
			Scalarm d = (patch.vertices[a] - patch.vertices[b]).Norm();
			adj[a].push_back({b, d});
			adj[b].push_back({a, d});
		}
	}

	// Multi-source Dijkstra from all boundary vertices (geodesic distance)
	const Scalarm INF = std::numeric_limits<Scalarm>::max();
	std::vector<Scalarm> dist(nVerts, INF);

	typedef std::pair<Scalarm, size_t> PQEntry;
	std::priority_queue<PQEntry, std::vector<PQEntry>, std::greater<PQEntry>> pq;

	for (size_t i = 0; i < nBoundary; i++) {
		dist[i] = (Scalarm)0;
		pq.push({(Scalarm)0, i});
	}

	while (!pq.empty()) {
		PQEntry top = pq.top(); pq.pop();
		Scalarm d = top.first;
		size_t  u = top.second;
		if (d > dist[u]) continue;
		for (size_t k = 0; k < adj[u].size(); k++) {
			size_t  v  = adj[u][k].first;
			Scalarm nd = dist[u] + adj[u][k].second;
			if (nd < dist[v]) {
				dist[v] = nd;
				pq.push({nd, v});
			}
		}
	}

	// Find maximum geodesic distance among interior vertices
	Scalarm maxDist = (Scalarm)0;
	for (size_t i = nBoundary; i < nVerts; i++) {
		if (dist[i] < INF && dist[i] > maxDist)
			maxDist = dist[i];
	}
	if (maxDist < (Scalarm)1e-10) return;

	// Displace interior vertices along diffused normals
	for (size_t i = nBoundary; i < nVerts; i++) {
		if (dist[i] >= INF) continue;

		// Normalized geodesic distance: 0 at boundary, 1 at farthest (= center)
		Scalarm t = dist[i] / maxDist;
		if (t > (Scalarm)1.0) t = (Scalarm)1.0;

		// Spherical-cap profile: weight(t) = sqrt(2t - t^2)
		// This is the height of a unit circle at horizontal offset (1-t),
		// so the patch follows a perfect cap shape: peak = 1 at t = 1 (center),
		// 0 at t = 0 (boundary), smooth tangent at boundary.
		Scalarm s = (Scalarm)2.0 * t - t * t;
		if (s < 0) s = 0;
		Scalarm weight = (Scalarm)std::sqrt((double)s);

		patch.vertices[i] += patch.normals[i] * (scale * weight);
	}

	// ---- Post-displacement damped Laplacian (Taubin-style) ----
	// Alternating shrink (positive step) / inflate (negative step) to remove
	// per-vertex spikes caused by irregular subdivision while preserving the
	// overall dome volume.
	std::vector<std::set<size_t>> padj(nVerts);
	for (const auto& f : patch.faces) {
		padj[f[0]].insert(f[1]); padj[f[0]].insert(f[2]);
		padj[f[1]].insert(f[0]); padj[f[1]].insert(f[2]);
		padj[f[2]].insert(f[0]); padj[f[2]].insert(f[1]);
	}

	// Taubin (lambda, mu): lambda positive (shrink), mu negative (inflate)
	// with |mu| > |lambda| to keep low-frequency shape (the dome).
	const int      taubinPairs = 3;
	const Scalarm  lambdaT     = (Scalarm) 0.40;
	const Scalarm  muT         = (Scalarm)-0.44;

	auto laplacianStep = [&](Scalarm step) {
		std::vector<Point3m> newPos = patch.vertices;
		for (size_t i = nBoundary; i < nVerts; i++) {
			if (padj[i].empty()) continue;
			Point3m avg(0, 0, 0);
			for (size_t ni : padj[i]) avg += patch.vertices[ni];
			avg /= (Scalarm)padj[i].size();
			newPos[i] = patch.vertices[i] + (avg - patch.vertices[i]) * step;
		}
		patch.vertices = newPos;
	};

	for (int p = 0; p < taubinPairs; p++) {
		laplacianStep(lambdaT);
		laplacianStep(muT);
	}
}

// ===================================================================
// Step 6: Laplacian Smoothing (boundary vertices held fixed)
// ===================================================================

void FilterNFDHoleFillPlugin::smoothPatch(PatchMesh& patch, int iterations)
{
	size_t nVerts    = patch.vertices.size();
	size_t nBoundary = patch.numBoundaryVerts;

	std::vector<std::set<size_t>> adj(nVerts);
	for (const auto& f : patch.faces) {
		adj[f[0]].insert(f[1]); adj[f[0]].insert(f[2]);
		adj[f[1]].insert(f[0]); adj[f[1]].insert(f[2]);
		adj[f[2]].insert(f[0]); adj[f[2]].insert(f[1]);
	}

	for (int iter = 0; iter < iterations; iter++) {
		std::vector<Point3m> newPos = patch.vertices;
		for (size_t i = nBoundary; i < nVerts; i++) {
			if (adj[i].empty()) continue;
			Point3m avg(0, 0, 0);
			for (size_t ni : adj[i])
				avg += patch.vertices[ni];
			avg /= (Scalarm)adj[i].size();
			newPos[i] = avg;
		}
		patch.vertices = newPos;
	}
}

// ===================================================================
// Step 7: Merge patch into mesh
// ===================================================================

void FilterNFDHoleFillPlugin::mergePatchIntoMesh(
	CMeshO& m, const PatchMesh& patch, const HoleBoundary& hole)
{
	size_t nBoundary = hole.vertexIndices.size();

	std::vector<size_t> vertMap(patch.vertices.size());
	for (size_t i = 0; i < nBoundary; i++)
		vertMap[i] = hole.vertexIndices[i];

	auto vi = vcg::tri::Allocator<CMeshO>::AddVertices(m, (int)(patch.vertices.size() - nBoundary));
	for (size_t i = nBoundary; i < patch.vertices.size(); i++) {
		vi->P() = patch.vertices[i];
		vi->N() = patch.normals[i];
		vertMap[i] = vcg::tri::Index(m, &*vi);
		++vi;
	}

	auto fi = vcg::tri::Allocator<CMeshO>::AddFaces(m, (int)patch.faces.size());
	for (size_t i = 0; i < patch.faces.size(); i++) {
		fi->V(0) = &m.vert[vertMap[patch.faces[i][0]]];
		fi->V(1) = &m.vert[vertMap[patch.faces[i][1]]];
		fi->V(2) = &m.vert[vertMap[patch.faces[i][2]]];
		++fi;
	}
}

MESHLAB_PLUGIN_NAME_EXPORTER(FilterNFDHoleFillPlugin)
