#include "filter_delaunay.h"

#include <vcg/complex/algorithms/update/bounding.h>
#include <vcg/complex/algorithms/update/normal.h>
#include <vcg/complex/algorithms/update/topology.h>

#include <vector>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <ctime>

using namespace vcg;

// ============================================================
// Constructor
// ============================================================
FilterDelaunayPlugin::FilterDelaunayPlugin()
{
	typeList = {FP_DELAUNAY_2D};

	for (ActionIDType tt : types())
		actionList.push_back(new QAction(filterName(tt), this));
}

FilterDelaunayPlugin::~FilterDelaunayPlugin()
{
}

// ============================================================
// Plugin metadata
// ============================================================
QString FilterDelaunayPlugin::pluginName() const
{
	return "FilterDelaunay";
}

QString FilterDelaunayPlugin::filterName(ActionIDType filterId) const
{
	switch (filterId) {
	case FP_DELAUNAY_2D:
		return "Delaunay Triangulation 2D";
	default:
		assert(0);
		return QString();
	}
}

QString FilterDelaunayPlugin::pythonFilterName(ActionIDType f) const
{
	switch (f) {
	case FP_DELAUNAY_2D:
		return "delaunay_triangulation_2d";
	default:
		assert(0);
		return QString();
	}
}

QString FilterDelaunayPlugin::filterInfo(ActionIDType filterId) const
{
	switch (filterId) {
	case FP_DELAUNAY_2D:
		return "Generate a 2D Delaunay Triangulation from random points using the "
		       "Bowyer-Watson algorithm. Creates a new mesh where vertices are random "
		       "2D points and faces are the Delaunay triangles. The Delaunay "
		       "triangulation maximizes the minimum angle of all triangles, avoiding "
		       "skinny triangles.";
	default:
		assert(0);
		return QString();
	}
}

FilterDelaunayPlugin::FilterClass FilterDelaunayPlugin::getClass(const QAction *a) const
{
	switch (ID(a)) {
	case FP_DELAUNAY_2D:
		return FilterPlugin::MeshCreation;
	default:
		assert(0);
		return FilterPlugin::Generic;
	}
}

FilterPlugin::FilterArity FilterDelaunayPlugin::filterArity(const QAction *) const
{
	return NONE;
}

int FilterDelaunayPlugin::getPreConditions(const QAction *) const
{
	return MeshModel::MM_NONE;
}

int FilterDelaunayPlugin::postCondition(const QAction *) const
{
	return MeshModel::MM_VERTCOORD | MeshModel::MM_FACENORMAL | MeshModel::MM_VERTNORMAL;
}

// ============================================================
// Parameters
// ============================================================
RichParameterList FilterDelaunayPlugin::initParameterList(const QAction *action, const MeshModel &)
{
	RichParameterList parlst;
	switch (ID(action)) {
	case FP_DELAUNAY_2D:
		parlst.addParam(RichInt(
			"NumPoints", 10, "Number of Points",
			"Number of random 2D points to generate (recommended: 10 to 15)."));
		parlst.addParam(RichInt(
			"RandomSeed", 42, "Random Seed",
			"Seed for random number generator. Use 0 for a time-based seed."));
		parlst.addParam(RichFloat(
			"Scale", 100.0f, "Scale",
			"Scale factor for the random point positions."));
		break;
	default:
		assert(0);
	}
	return parlst;
}

// ============================================================
// Apply filter
// ============================================================
std::map<std::string, QVariant> FilterDelaunayPlugin::applyFilter(
	const QAction *filter,
	const RichParameterList &parameters,
	MeshDocument &md,
	unsigned int &,
	vcg::CallBackPos *cb)
{
	switch (ID(filter)) {
	case FP_DELAUNAY_2D:
		delaunayTriangulation2D(
			md, cb,
			parameters.getInt("NumPoints"),
			parameters.getInt("RandomSeed"),
			parameters.getFloat("Scale"));
		break;
	default:
		wrongActionCalled(filter);
	}
	return std::map<std::string, QVariant>();
}

// ============================================================
// Circumcircle test for Bowyer-Watson
// Computes circumcircle center and radius, then checks distance.
// Works regardless of triangle winding order.
// ============================================================
bool FilterDelaunayPlugin::isInsideCircumcircle(
	const std::vector<Point3m> &points,
	const Triangle &tri,
	const Point3m &p) const
{
	Scalarm ax = points[tri.v0].X();
	Scalarm ay = points[tri.v0].Y();
	Scalarm bx = points[tri.v1].X();
	Scalarm by = points[tri.v1].Y();
	Scalarm cx = points[tri.v2].X();
	Scalarm cy = points[tri.v2].Y();

	Scalarm D = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));
	if (std::abs(D) < 1e-12)
		return false; // degenerate triangle

	Scalarm ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / D;
	Scalarm uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / D;

	Scalarm r2 = (ax - ux) * (ax - ux) + (ay - uy) * (ay - uy);
	Scalarm d2 = (p.X() - ux) * (p.X() - ux) + (p.Y() - uy) * (p.Y() - uy);

	return d2 < r2;
}

// ============================================================
// Bowyer-Watson Delaunay Triangulation
// ============================================================
bool FilterDelaunayPlugin::delaunayTriangulation2D(
	MeshDocument &md,
	vcg::CallBackPos *cb,
	int numPoints,
	int randomSeed,
	Scalarm scale)
{
	if (numPoints < 3) {
		log("Error: Need at least 3 points for triangulation");
		return false;
	}

	// Seed random number generator
	if (randomSeed == 0)
		srand((unsigned int)time(NULL));
	else
		srand((unsigned int)randomSeed);

	cb(0, "Generating random points...");

	// Step 1: Generate random 2D points (z = 0)
	std::vector<Point3m> points;

	for (int i = 0; i < numPoints; i++) {
		Scalarm x = (Scalarm(rand()) / RAND_MAX) * scale;
		Scalarm y = (Scalarm(rand()) / RAND_MAX) * scale;
		points.push_back(Point3m(x, y, 0));
	}

	cb(10, "Creating super-triangle...");

	// Step 2: Create super-triangle that contains all points
	Scalarm margin = scale * 10.0;
	int st0 = (int)points.size();
	int st1 = st0 + 1;
	int st2 = st0 + 2;
	points.push_back(Point3m(-margin,            -margin,            0));
	points.push_back(Point3m(scale + margin * 3, -margin,            0));
	points.push_back(Point3m(-margin,            scale + margin * 3, 0));

	std::vector<Triangle> triangles;
	triangles.push_back(Triangle(st0, st1, st2));

	cb(20, "Running Bowyer-Watson algorithm...");

	// Step 3: Insert each point using Bowyer-Watson
	for (int i = 0; i < numPoints; i++) {
		cb(20 + 60 * i / numPoints, "Inserting points...");

		// Find all triangles whose circumcircle contains the point
		std::vector<Triangle> badTriangles;
		for (size_t t = 0; t < triangles.size(); t++) {
			if (isInsideCircumcircle(points, triangles[t], points[i])) {
				badTriangles.push_back(triangles[t]);
			}
		}

		// Find the boundary polygon (edges not shared by two bad triangles)
		std::vector<Edge> boundary;
		for (size_t t = 0; t < badTriangles.size(); t++) {
			Edge edges[3] = {
				Edge(badTriangles[t].v0, badTriangles[t].v1),
				Edge(badTriangles[t].v1, badTriangles[t].v2),
				Edge(badTriangles[t].v2, badTriangles[t].v0)
			};

			for (int e = 0; e < 3; e++) {
				bool shared = false;
				for (size_t t2 = 0; t2 < badTriangles.size(); t2++) {
					if (t2 == t) continue;
					Edge otherEdges[3] = {
						Edge(badTriangles[t2].v0, badTriangles[t2].v1),
						Edge(badTriangles[t2].v1, badTriangles[t2].v2),
						Edge(badTriangles[t2].v2, badTriangles[t2].v0)
					};
					for (int e2 = 0; e2 < 3; e2++) {
						if (edges[e] == otherEdges[e2]) {
							shared = true;
							break;
						}
					}
					if (shared) break;
				}
				if (!shared) {
					boundary.push_back(edges[e]);
				}
			}
		}

		// Remove bad triangles
		std::vector<Triangle> newTriangles;
		for (size_t t = 0; t < triangles.size(); t++) {
			bool isBad = false;
			for (size_t b = 0; b < badTriangles.size(); b++) {
				if (triangles[t].v0 == badTriangles[b].v0 &&
				    triangles[t].v1 == badTriangles[b].v1 &&
				    triangles[t].v2 == badTriangles[b].v2) {
					isBad = true;
					break;
				}
			}
			if (!isBad) {
				newTriangles.push_back(triangles[t]);
			}
		}
		triangles = newTriangles;

		// Create new triangles from boundary edges to the new point
		for (size_t e = 0; e < boundary.size(); e++) {
			triangles.push_back(Triangle(boundary[e].v0, boundary[e].v1, i));
		}
	}

	cb(80, "Removing super-triangle...");

	// Step 4: Remove triangles that share vertices with the super-triangle
	std::vector<Triangle> finalTriangles;
	for (size_t t = 0; t < triangles.size(); t++) {
		if (triangles[t].v0 != st0 && triangles[t].v0 != st1 && triangles[t].v0 != st2 &&
		    triangles[t].v1 != st0 && triangles[t].v1 != st1 && triangles[t].v1 != st2 &&
		    triangles[t].v2 != st0 && triangles[t].v2 != st1 && triangles[t].v2 != st2) {
			finalTriangles.push_back(triangles[t]);
		}
	}

	cb(90, "Building mesh...");

	// Step 5: Create MeshLab mesh from the triangulation
	MeshModel *mm = md.addNewMesh("", "Delaunay Triangulation");
	CMeshO &mesh = mm->cm;

	// Add vertices (only the original points, not the super-triangle)
	auto vi = tri::Allocator<CMeshO>::AddVertices(mesh, numPoints);
	for (int i = 0; i < numPoints; i++) {
		vi[i].P() = points[i];
	}

	// Validate face indices before adding
	int validFaces = 0;
	for (size_t i = 0; i < finalTriangles.size(); i++) {
		if (finalTriangles[i].v0 >= 0 && finalTriangles[i].v0 < numPoints &&
		    finalTriangles[i].v1 >= 0 && finalTriangles[i].v1 < numPoints &&
		    finalTriangles[i].v2 >= 0 && finalTriangles[i].v2 < numPoints) {
			validFaces++;
		}
	}

	// Add only valid faces
	auto fi = tri::Allocator<CMeshO>::AddFaces(mesh, validFaces);
	int fIdx = 0;
	for (size_t i = 0; i < finalTriangles.size(); i++) {
		if (finalTriangles[i].v0 >= 0 && finalTriangles[i].v0 < numPoints &&
		    finalTriangles[i].v1 >= 0 && finalTriangles[i].v1 < numPoints &&
		    finalTriangles[i].v2 >= 0 && finalTriangles[i].v2 < numPoints) {
			fi[fIdx].V(0) = &mesh.vert[finalTriangles[i].v0];
			fi[fIdx].V(1) = &mesh.vert[finalTriangles[i].v1];
			fi[fIdx].V(2) = &mesh.vert[finalTriangles[i].v2];
			fIdx++;
		}
	}

	// Update mesh properties
	tri::UpdateBounding<CMeshO>::Box(mesh);
	tri::UpdateNormal<CMeshO>::PerVertexNormalizedPerFaceNormalized(mesh);

	log("Delaunay Triangulation completed: %i vertices, %i triangles",
	    mesh.vn, mesh.fn);

	cb(100, "Done!");

	return true;
}

MESHLAB_PLUGIN_NAME_EXPORTER(FilterDelaunayPlugin)
