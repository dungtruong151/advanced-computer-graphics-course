#include "filter_advancing_front.h"

#include <vcg/complex/algorithms/update/topology.h>
#include <vcg/complex/algorithms/update/normal.h>
#include <vcg/complex/algorithms/update/bounding.h>
#include <vcg/complex/algorithms/update/flag.h>
#include <vcg/complex/allocate.h>
#include <cmath>
#include <set>
#include <map>
#include <vector>
#include <string>
#include <algorithm>
#include <limits>

// ===================================================================
// Plugin boilerplate
// ===================================================================

FilterAdvancingFrontPlugin::FilterAdvancingFrontPlugin()
{
	typeList = {FP_ADVANCING_FRONT, FP_DETECT_HOLE_BOUNDARY};
	for (ActionIDType tt : types())
		actionList.push_back(new QAction(filterName(tt), this));
}

FilterAdvancingFrontPlugin::~FilterAdvancingFrontPlugin() {}

QString FilterAdvancingFrontPlugin::pluginName() const
{
	return "FilterAdvancingFront";
}

QString FilterAdvancingFrontPlugin::filterName(ActionIDType filterId) const
{
	switch (filterId) {
	case FP_ADVANCING_FRONT: return "Advancing Front Hole Filling";
	case FP_DETECT_HOLE_BOUNDARY: return "Detect Hole Boundary (Red)";
	default: assert(0); return QString();
	}
}

QString FilterAdvancingFrontPlugin::pythonFilterName(ActionIDType f) const
{
	switch (f) {
	case FP_ADVANCING_FRONT: return "apply_advancing_front_hole_filling";
	case FP_DETECT_HOLE_BOUNDARY: return "detect_hole_boundary_red";
	default: assert(0); return QString();
	}
}

QString FilterAdvancingFrontPlugin::filterInfo(ActionIDType filterId) const
{
	switch (filterId) {
	case FP_ADVANCING_FRONT:
		return "Fill holes using the Advancing Front method. "
		       "This method progressively grows triangles from the hole boundary "
		       "inward by selecting the vertex with the smallest angle between "
		       "adjacent boundary edges. Three angle-based rules control triangle "
		       "creation for uniform mesh quality. A final Laplacian smoothing "
		       "pass ensures a smooth transition with the surrounding surface.";
	case FP_DETECT_HOLE_BOUNDARY:
		return "Detect and highlight hole boundaries by coloring them red. "
		       "This filter identifies all boundary vertices that form holes in the mesh "
		       "and colors them red for easy visualization.";
	default: assert(0); return "Unknown Filter";
	}
}

FilterAdvancingFrontPlugin::FilterClass FilterAdvancingFrontPlugin::getClass(const QAction* a) const
{
	switch (ID(a)) {
	case FP_ADVANCING_FRONT: return FilterPlugin::Remeshing;
	case FP_DETECT_HOLE_BOUNDARY: return FilterPlugin::Selection;
	default: assert(0); return FilterPlugin::Generic;
	}
}

FilterPlugin::FilterArity FilterAdvancingFrontPlugin::filterArity(const QAction*) const
{
	return SINGLE_MESH;
}

int FilterAdvancingFrontPlugin::getPreConditions(const QAction*) const
{
	return MeshModel::MM_FACENUMBER;
}

int FilterAdvancingFrontPlugin::getRequirements(const QAction* action)
{
	switch (ID(action)) {
	case FP_DETECT_HOLE_BOUNDARY:
		return MeshModel::MM_VERTCOLOR;
	case FP_ADVANCING_FRONT:
		return MeshModel::MM_NONE;
	default:
		return MeshModel::MM_NONE;
	}
}

int FilterAdvancingFrontPlugin::postCondition(const QAction* action) const
{
	switch (ID(action)) {
	case FP_DETECT_HOLE_BOUNDARY:
		return MeshModel::MM_VERTCOORD | MeshModel::MM_VERTCOLOR;
	case FP_ADVANCING_FRONT:
		return MeshModel::MM_VERTCOORD | MeshModel::MM_FACENORMAL | MeshModel::MM_VERTNORMAL;
	default:
		return MeshModel::MM_VERTCOORD;
	}
}

void FilterAdvancingFrontPlugin::initParameterList(const QAction* action, MeshModel& m, RichParameterList& parlst)
{
	switch (ID(action)) {
	case FP_ADVANCING_FRONT:
		parlst.addParam(RichInt("MaxHoleSize", 100,
			"Max Hole Size (edges)",
			"Maximum number of boundary edges for a hole to be filled."));
		parlst.addParam(RichInt("SmoothingIterations", 3,
			"Smoothing Iterations",
			"Number of Laplacian smoothing iterations on the filled patch."));
		break;
	case FP_DETECT_HOLE_BOUNDARY:
		// No parameters needed for boundary detection
		break;
	default: assert(0);
	}
}

// ===================================================================
// Main apply function
// ===================================================================

std::map<std::string, QVariant> FilterAdvancingFrontPlugin::applyFilter(
	const QAction* action,
	const RichParameterList& parameters,
	MeshDocument& md,
	unsigned int& /*postConditionMask*/,
	vcg::CallBackPos* cb)
{
	auto report = [&](int progress, const char* message) {
		if (cb) cb(progress, message);
	};

	switch (ID(action)) {
	case FP_DETECT_HOLE_BOUNDARY: {
		MeshModel* mm = md.mm();
		CMeshO& m = mm->cm;
		
		report(0, "Updating topology...");
		
		// Enable vertex color component on the mesh container first
		if (!vcg::tri::HasPerVertexColor(m)) {
			m.vert.EnableColor();
		}
		
		// Then update the mesh model mask
		mm->updateDataMask(MeshModel::MM_VERTCOLOR | MeshModel::MM_FACEFACETOPO);
		
		m.face.EnableFFAdjacency();
		vcg::tri::UpdateTopology<CMeshO>::FaceFace(m);
		vcg::tri::UpdateFlags<CMeshO>::FaceBorderFromFF(m);
		vcg::tri::UpdateFlags<CMeshO>::VertexBorderFromFaceBorder(m);
		
		report(30, "Detecting hole boundaries...");
		int boundaryCount = 0;
		CMeshO::VertexIterator vi;
		for (vi = m.vert.begin(); vi != m.vert.end(); ++vi) {
			if (!(*vi).IsD() && (*vi).IsB()) {
				// Color boundary vertices red
				(*vi).C() = vcg::Color4b(255, 0, 0, 255);
				boundaryCount++;
			}
		}
		
		log("Detected %d boundary vertices and colored them red.", boundaryCount);
		report(100, "Done.");
		break;
	}
	case FP_ADVANCING_FRONT: {
		CMeshO& m = md.mm()->cm;

		int maxHoleSize      = std::max(3, parameters.getInt("MaxHoleSize"));
		int smoothIterations = std::max(0, parameters.getInt("SmoothingIterations"));

		// Enable Ocf optional components
		report(0, "Updating topology...");
		m.face.EnableFFAdjacency();
		m.face.EnableVFAdjacency();
		m.vert.EnableVFAdjacency();
		vcg::tri::UpdateTopology<CMeshO>::FaceFace(m);
		vcg::tri::UpdateTopology<CMeshO>::VertexFace(m);
		vcg::tri::UpdateFlags<CMeshO>::FaceBorderFromFF(m);
		vcg::tri::UpdateFlags<CMeshO>::VertexBorderFromFaceBorder(m);
		vcg::tri::UpdateNormal<CMeshO>::PerVertexNormalizedPerFace(m);

		// Detect holes
		report(5, "Detecting holes...");
		std::vector<HoleBoundary> holes = detectHoles(m, maxHoleSize);

		if (holes.empty()) {
			log("No holes found (or all holes exceed max size).");
			break;
		}
		log("Found %d hole(s) to fill.", (int)holes.size());

		int totalHoles = (int)holes.size();
		for (int hi = 0; hi < totalHoles; hi++) {
			int progress = 10 + (80 * hi / totalHoles);
			std::string progressMsg = "Filling hole " + std::to_string(hi + 1) + "/" + std::to_string(totalHoles) + "...";
			report(progress, progressMsg.c_str());

			log("Hole %d/%d: %d boundary edges.", hi + 1, totalHoles, (int)holes[hi].vertexIndices.size());

			// Fit a sphere to the boundary for curvature-aware filling
			FittedSphere sphere = fitSphere(holes[hi]);
			if (sphere.valid)
				log("  Sphere fit: center=(%.3f,%.3f,%.3f) radius=%.3f",
				    sphere.center[0], sphere.center[1], sphere.center[2], sphere.radius);
			else
				log("  No sphere fit (flat region) — filling flat.");

			// Advancing front triangulation (with sphere projection)
			PatchMesh patch = advancingFrontFill(holes[hi], sphere);
			if (patch.faces.empty()) continue;

			// Laplacian smoothing (with sphere projection)
			smoothPatch(patch, smoothIterations, sphere);

			// Merge into mesh
			mergePatchIntoMesh(m, patch, holes[hi]);
		}

		// Final updates
		report(95, "Updating normals...");
		vcg::tri::UpdateTopology<CMeshO>::FaceFace(m);
		vcg::tri::UpdateNormal<CMeshO>::PerVertexNormalizedPerFace(m);
		vcg::tri::UpdateNormal<CMeshO>::PerFaceNormalized(m);
		vcg::tri::UpdateBounding<CMeshO>::Box(m);

		log("Advancing Front Hole Filling completed: %d hole(s) filled.", totalHoles);
		report(100, "Done.");
		break;
	}
	default: wrongActionCalled(action);
	}
	return std::map<std::string, QVariant>();
}

// ===================================================================
// Step 1: Hole Detection (same as NFD plugin)
// ===================================================================

std::vector<FilterAdvancingFrontPlugin::HoleBoundary>
FilterAdvancingFrontPlugin::detectHoles(CMeshO& m, int maxHoleSize)
{
	std::vector<HoleBoundary> holes;

	vcg::tri::UpdateFlags<CMeshO>::FaceBorderFromFF(m);
	vcg::tri::UpdateFlags<CMeshO>::VertexBorderFromFaceBorder(m);

	std::set<std::pair<size_t, size_t>> visitedEdges;
	auto edgeKey = [](size_t a, size_t b) {
		return std::make_pair(std::min(a, b), std::max(a, b)); // undirected edge key
	};

	for (auto fi = m.face.begin(); fi != m.face.end(); ++fi) {
		if (fi->IsD()) continue;
		for (int ei = 0; ei < 3; ei++) {
			if (vcg::face::IsBorder(*fi, ei)) {
				size_t vi = vcg::tri::Index(m, fi->V(ei));
				size_t vj = vcg::tri::Index(m, fi->V((ei + 1) % 3));

				if (visitedEdges.count(edgeKey(vi, vj))) continue;

				HoleBoundary hole;
				size_t startV = vi;
				size_t curV   = vi;
				size_t nextV  = vj;
				bool loopComplete = false;
				int safety = 0;
				const int maxSteps = std::max(32, maxHoleSize * 3);

				while (safety < maxSteps) {
					safety++;
					hole.vertexIndices.push_back(curV);
					visitedEdges.insert(edgeKey(curV, nextV));

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
							if (!vcg::face::IsBorder(*fp, e)) continue;

							size_t eV0 = vcg::tri::Index(m, fp->V(e));
							size_t eV1 = vcg::tri::Index(m, fp->V((e + 1) % 3));
							size_t candidate = std::numeric_limits<size_t>::max();
							if (eV0 == curV && eV1 != prevV)
								candidate = eV1;
							else if (eV1 == curV && eV0 != prevV)
								candidate = eV0;
							if (candidate == std::numeric_limits<size_t>::max()) continue;

							// Avoid revisiting an already-walked edge (except closing edge to start).
							if (candidate != startV && visitedEdges.count(edgeKey(curV, candidate))) continue;

							nextV = candidate;
							foundNext = true;
							break;
						}
						if (foundNext) break;
					}

					if (!foundNext) break;
				}

				if (loopComplete && (int)hole.vertexIndices.size() >= 3 &&
				    (int)hole.vertexIndices.size() <= maxHoleSize) {
					hole.positions.resize(hole.vertexIndices.size());
					hole.normals.resize(hole.vertexIndices.size());
					for (size_t i = 0; i < hole.vertexIndices.size(); i++) {
						hole.positions[i] = m.vert[hole.vertexIndices[i]].P();
						hole.normals[i] = m.vert[hole.vertexIndices[i]].N();
						Scalarm len = hole.normals[i].Norm();
						if (len > 1e-10) hole.normals[i] /= len;
					}
					holes.push_back(hole);
				}
			}
		}
	}

	return holes;
}

// ===================================================================
// Step 1b: Sphere Fitting
//
// Fit a sphere to the boundary vertices using their positions and
// normals. For a sphere, all surface normals pass through the center.
// We find the point closest to all normal-lines via least squares:
//   A = sum_i (I - n_i * n_i^T)
//   b = sum_i (I - n_i * n_i^T) * v_i
//   center = A^{-1} * b
// ===================================================================

FilterAdvancingFrontPlugin::FittedSphere
FilterAdvancingFrontPlugin::fitSphere(const HoleBoundary& hole)
{
	FittedSphere sphere;
	sphere.valid = false;
	size_t n = hole.positions.size();
	if (n < 3) return sphere;

	// Build 3x3 system: A * center = b
	// A = sum_i (I - n_i * n_i^T), b = A * v_i summed
	Scalarm A[3][3] = {{0,0,0},{0,0,0},{0,0,0}};
	Scalarm b[3] = {0, 0, 0};

	int validNormals = 0;
	for (size_t i = 0; i < n; i++) {
		Point3m ni = hole.normals[i];
		if (ni.Norm() < 1e-10) continue;
		ni.Normalize();
		validNormals++;

		Point3m vi = hole.positions[i];
		// M = I - n*n^T
		for (int r = 0; r < 3; r++) {
			for (int c = 0; c < 3; c++) {
				Scalarm Mrc = ((r == c) ? (Scalarm)1.0 : (Scalarm)0.0) - ni[r] * ni[c];
				A[r][c] += Mrc;
				b[r] += Mrc * vi[c];
			}
		}
	}

	if (validNormals < 3) return sphere;

	// Solve 3x3 system via Cramer's rule
	auto det3 = [](Scalarm m[3][3]) -> Scalarm {
		return m[0][0]*(m[1][1]*m[2][2] - m[1][2]*m[2][1])
		     - m[0][1]*(m[1][0]*m[2][2] - m[1][2]*m[2][0])
		     + m[0][2]*(m[1][0]*m[2][1] - m[1][1]*m[2][0]);
	};

	Scalarm detA = det3(A);
	if (std::abs(detA) < 1e-10) {
		// Normals are nearly parallel (flat region) — sphere fitting not meaningful
		return sphere;
	}

	// Cramer's rule for each component
	Point3m center;
	for (int col = 0; col < 3; col++) {
		Scalarm Acopy[3][3];
		for (int r = 0; r < 3; r++)
			for (int c = 0; c < 3; c++)
				Acopy[r][c] = (c == col) ? b[r] : A[r][c];
		center[col] = det3(Acopy) / detA;
	}

	// Compute average radius
	Scalarm avgR = 0;
	for (size_t i = 0; i < n; i++)
		avgR += (hole.positions[i] - center).Norm();
	avgR /= (Scalarm)n;

	// Validate: check that the radii are consistent (low variance)
	Scalarm variance = 0;
	for (size_t i = 0; i < n; i++) {
		Scalarm ri = (hole.positions[i] - center).Norm();
		variance += (ri - avgR) * (ri - avgR);
	}
	variance /= (Scalarm)n;
	Scalarm stddev = std::sqrt(variance);

	// Accept if standard deviation is less than 20% of radius
	if (avgR > 1e-10 && stddev / avgR < 0.2) {
		sphere.center = center;
		sphere.radius = avgR;
		sphere.valid = true;
	}

	return sphere;
}

// ===================================================================
// Step 2: Advancing Front Hole Filling
//
// Algorithm:
//   While the boundary front has more than 3 vertices:
//     1. Find the vertex with the smallest angle between its
//        two adjacent boundary edges
//     2. Apply one of three rules based on the angle:
//        - Rule 1 (angle < 75):  close with 1 triangle
//        - Rule 2 (angle < 135): create 1 new vertex, 2 triangles
//        - Rule 3 (angle >= 135): create 2 new vertices, 3 triangles
//     3. Update the boundary front
//   Close the final triangle
// ===================================================================

FilterAdvancingFrontPlugin::PatchMesh
FilterAdvancingFrontPlugin::advancingFrontFill(const HoleBoundary& hole, const FittedSphere& sphere)
{
	PatchMesh patch;
	size_t n = hole.vertexIndices.size();
	if (n < 3) return patch;

	// Initialize patch with boundary vertices
	for (size_t i = 0; i < n; i++) {
		patch.vertices.push_back(hole.positions[i]);
		patch.normals.push_back(hole.normals[i]);
		patch.isBoundary.push_back(true);
	}

	// Compute average normal (for orienting new vertices)
	Point3m avgNormal(0, 0, 0);
	for (size_t i = 0; i < n; i++) avgNormal += hole.normals[i];
	Scalarm nlen = avgNormal.Norm();
	if (nlen > 1e-10) avgNormal /= nlen;

	// Compute average edge length (for sizing new vertices)
	Scalarm avgEdgeLen = 0;
	for (size_t i = 0; i < n; i++) {
		size_t j = (i + 1) % n;
		avgEdgeLen += (hole.positions[i] - hole.positions[j]).Norm();
	}
	avgEdgeLen /= (Scalarm)n;

	// Helper: project a point onto the fitted sphere
	auto projectOnSphere = [&](Point3m p) -> Point3m {
		if (!sphere.valid) return p;
		Point3m dir = p - sphere.center;
		Scalarm len = dir.Norm();
		if (len < 1e-10) return p;
		return sphere.center + dir * (sphere.radius / len);
	};

	// Active front: circular list of vertex indices into patch.vertices
	std::vector<int> front(n);
	for (int i = 0; i < (int)n; i++) front[i] = i;
	const Scalarm PI = (Scalarm)3.14159265358979323846;

	// Helper: compute angle at vertex front[idx] between its two edges
	auto computeAngle = [&](const std::vector<int>& f, int idx) -> Scalarm {
		int sz = (int)f.size();
		int prevIdx = (idx - 1 + sz) % sz;
		int nextIdx = (idx + 1) % sz;

		Point3m vPrev = patch.vertices[f[prevIdx]];
		Point3m vCurr = patch.vertices[f[idx]];
		Point3m vNext = patch.vertices[f[nextIdx]];

		Point3m e1 = vPrev - vCurr;
		Point3m e2 = vNext - vCurr;

		Scalarm len1 = e1.Norm();
		Scalarm len2 = e2.Norm();
		if (len1 < 1e-10 || len2 < 1e-10) return PI;

		e1 /= len1;
		e2 /= len2;

		Scalarm cosA = e1 * e2;  // dot product
		cosA = std::max((Scalarm)-1.0, std::min((Scalarm)1.0, cosA));
		return std::acos(cosA);
	};

	// Angle thresholds (in radians)
	const Scalarm RULE1_THRESHOLD = (Scalarm)(75.0 * PI / 180.0);   // 75 degrees
	const Scalarm RULE2_THRESHOLD = (Scalarm)(135.0 * PI / 180.0);  // 135 degrees

	int maxIter = (int)(n * 8 + 32);  // safety limit

	while ((int)front.size() > 3 && maxIter > 0) {
		maxIter--;

		// Find vertex with smallest angle on the front
		int bestIdx = 0;
		Scalarm bestAngle = computeAngle(front, 0);
		for (int i = 1; i < (int)front.size(); i++) {
			Scalarm a = computeAngle(front, i);
			if (a < bestAngle) {
				bestAngle = a;
				bestIdx = i;
			}
		}

		int sz = (int)front.size();
		int prevIdx = (bestIdx - 1 + sz) % sz;
		int nextIdx = (bestIdx + 1) % sz;

		int vPrev = front[prevIdx];
		int vCurr = front[bestIdx];
		int vNext = front[nextIdx];

		Point3m pPrev = patch.vertices[vPrev];
		Point3m pCurr = patch.vertices[vCurr];
		Point3m pNext = patch.vertices[vNext];

		if (bestAngle < RULE1_THRESHOLD) {
			// ── Rule 1: angle < 75 deg ──
			// Close with a single triangle, remove vCurr from front
			patch.faces.push_back(vcg::Point3i(vPrev, vCurr, vNext));
			front.erase(front.begin() + bestIdx);

		} else if (bestAngle < RULE2_THRESHOLD) {
			// ── Rule 2: 75 <= angle < 135 deg ──
			// Create 1 new vertex at the ideal position, form 2 triangles
			Point3m e1 = (pPrev - pCurr);
			Point3m e2 = (pNext - pCurr);
			Scalarm len1 = e1.Norm();
			Scalarm len2 = e2.Norm();
			if (len1 > 1e-10) e1 /= len1;
			if (len2 > 1e-10) e2 /= len2;

			// New vertex at the angle bisector direction
			Point3m bisector = e1 + e2;
			Scalarm blen = bisector.Norm();
			if (blen > 1e-10) bisector /= blen;

			Point3m newPos = projectOnSphere(pCurr + bisector * avgEdgeLen);
			int newIdx = (int)patch.vertices.size();
			patch.vertices.push_back(newPos);
			patch.normals.push_back(avgNormal);
			patch.isBoundary.push_back(false);

			// 2 triangles: (prev, curr, new) and (curr, next, new)
			patch.faces.push_back(vcg::Point3i(vPrev, vCurr, newIdx));
			patch.faces.push_back(vcg::Point3i(vCurr, vNext, newIdx));

			// Replace vCurr with newIdx in front
			front[bestIdx] = newIdx;

		} else {
			// ── Rule 3: angle >= 135 deg ──
			// Create 2 new vertices, form 3 triangles
			Point3m e1 = (pPrev - pCurr);
			Point3m e2 = (pNext - pCurr);
			Scalarm len1 = e1.Norm();
			Scalarm len2 = e2.Norm();
			if (len1 > 1e-10) e1 /= len1;
			if (len2 > 1e-10) e2 /= len2;

			// Two new vertices at 1/3 and 2/3 of the angle
			Point3m bisector = e1 + e2;
			Scalarm blen = bisector.Norm();
			if (blen > 1e-10) bisector /= blen;

			// Rotate bisector toward e1 and e2 for the two new points
			Point3m newPos1 = pCurr + (e1 + bisector) * (avgEdgeLen * (Scalarm)0.5);
			Point3m newPos2 = pCurr + (e2 + bisector) * (avgEdgeLen * (Scalarm)0.5);

			// Normalize distances to avgEdgeLen
			Point3m dir1 = newPos1 - pCurr;
			Point3m dir2 = newPos2 - pCurr;
			Scalarm d1 = dir1.Norm();
			Scalarm d2 = dir2.Norm();
			if (d1 > 1e-10) newPos1 = pCurr + dir1 * (avgEdgeLen / d1);
			if (d2 > 1e-10) newPos2 = pCurr + dir2 * (avgEdgeLen / d2);
			newPos1 = projectOnSphere(newPos1);
			newPos2 = projectOnSphere(newPos2);

			int newIdx1 = (int)patch.vertices.size();
			patch.vertices.push_back(newPos1);
			patch.normals.push_back(avgNormal);
			patch.isBoundary.push_back(false);

			int newIdx2 = (int)patch.vertices.size();
			patch.vertices.push_back(newPos2);
			patch.normals.push_back(avgNormal);
			patch.isBoundary.push_back(false);

			// 3 triangles: (prev, curr, new1), (new1, curr, new2), (new2, curr, next)
			// But curr is removed, so: (prev, new1, curr) won't work if we remove curr.
			// Correct: (vPrev, vCurr, newIdx1), (newIdx1, vCurr, newIdx2), (newIdx2, vCurr, vNext)
			// Then remove vCurr from front and insert newIdx1, newIdx2
			patch.faces.push_back(vcg::Point3i(vPrev, vCurr, newIdx1));
			patch.faces.push_back(vcg::Point3i(newIdx1, vCurr, newIdx2));
			patch.faces.push_back(vcg::Point3i(newIdx2, vCurr, vNext));

			// Replace vCurr with newIdx1, newIdx2 in front
			front[bestIdx] = newIdx1;
			front.insert(front.begin() + bestIdx + 1, newIdx2);
		}
	}

	// Abort unsafe partial patches.
	if (front.size() != 3) {
		patch.faces.clear();
		patch.numBoundaryVerts = n;
		return patch;
	}

	// Close the final triangle
	patch.faces.push_back(vcg::Point3i(front[0], front[1], front[2]));

	// Post-hoc winding fix: ensure face normals align with avgNormal
	if (!patch.faces.empty()) {
		auto& f = patch.faces[0];
		Point3m AB = patch.vertices[f[1]] - patch.vertices[f[0]];
		Point3m AC = patch.vertices[f[2]] - patch.vertices[f[0]];
		if ((AB ^ AC) * avgNormal < 0) {
			for (auto& face : patch.faces)
				std::swap(face[1], face[2]);
		}
	}

	patch.numBoundaryVerts = n;
	return patch;
}

// ===================================================================
// Step 3: Laplacian Smoothing (boundary vertices held fixed)
// ===================================================================

void FilterAdvancingFrontPlugin::smoothPatch(PatchMesh& patch, int iterations, const FittedSphere& sphere)
{
	size_t nVerts    = patch.vertices.size();
	size_t nBoundary = patch.numBoundaryVerts;

	// Build adjacency from faces
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

			// Project smoothed position back onto sphere
			if (sphere.valid) {
				Point3m dir = avg - sphere.center;
				Scalarm len = dir.Norm();
				if (len > 1e-10)
					avg = sphere.center + dir * (sphere.radius / len);
			}

			newPos[i] = avg;
		}
		patch.vertices = newPos;
	}
}

// ===================================================================
// Step 4: Merge patch into mesh
// ===================================================================

void FilterAdvancingFrontPlugin::mergePatchIntoMesh(
	CMeshO& m, const PatchMesh& patch, const HoleBoundary& hole)
{
	size_t nBoundary = hole.vertexIndices.size();

	std::vector<size_t> vertMap(patch.vertices.size());
	for (size_t i = 0; i < nBoundary; i++)
		vertMap[i] = hole.vertexIndices[i];

	// Add interior vertices
	if (patch.vertices.size() > nBoundary) {
		auto vi = vcg::tri::Allocator<CMeshO>::AddVertices(m, (int)(patch.vertices.size() - nBoundary));
		for (size_t i = nBoundary; i < patch.vertices.size(); i++) {
			vi->P() = patch.vertices[i];
			vi->N() = patch.normals[i];
			vertMap[i] = vcg::tri::Index(m, &*vi);
			++vi;
		}
	}

	// Add faces
	auto fi = vcg::tri::Allocator<CMeshO>::AddFaces(m, (int)patch.faces.size());
	for (size_t i = 0; i < patch.faces.size(); i++) {
		fi->V(0) = &m.vert[vertMap[patch.faces[i][0]]];
		fi->V(1) = &m.vert[vertMap[patch.faces[i][1]]];
		fi->V(2) = &m.vert[vertMap[patch.faces[i][2]]];
		++fi;
	}
}

MESHLAB_PLUGIN_NAME_EXPORTER(FilterAdvancingFrontPlugin)