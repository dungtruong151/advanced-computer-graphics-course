#ifndef FILTER_DELAUNAY_H
#define FILTER_DELAUNAY_H

#include <common/plugins/interfaces/filter_plugin.h>

class FilterDelaunayPlugin : public QObject, public FilterPlugin
{
	Q_OBJECT
	MESHLAB_PLUGIN_IID_EXPORTER(FILTER_PLUGIN_IID)
	Q_INTERFACES(FilterPlugin)

public:
	enum { FP_DELAUNAY_2D };

	FilterDelaunayPlugin();
	virtual ~FilterDelaunayPlugin();

	QString pluginName() const;
	QString filterName(ActionIDType filter) const;
	QString pythonFilterName(ActionIDType f) const;
	QString filterInfo(ActionIDType filter) const;
	FilterClass getClass(const QAction* a) const;
	FilterArity filterArity(const QAction*) const;
	int getPreConditions(const QAction *) const;
	int postCondition(const QAction*) const;
	RichParameterList initParameterList(const QAction*, const MeshModel &m);
	std::map<std::string, QVariant> applyFilter(
			const QAction* action,
			const RichParameterList & parameters,
			MeshDocument &md,
			unsigned int& postConditionMask,
			vcg::CallBackPos * cb);

private:
	// Bowyer-Watson Delaunay triangulation
	struct Triangle {
		int v0, v1, v2;
		Triangle(int a, int b, int c) : v0(a), v1(b), v2(c) {}
	};

	struct Edge {
		int v0, v1;        // original order (for building new triangles)
		int smin, smax;    // sorted order (for comparison)
		Edge(int a, int b) : v0(a), v1(b), smin(std::min(a,b)), smax(std::max(a,b)) {}
		bool operator==(const Edge& other) const {
			return smin == other.smin && smax == other.smax;
		}
	};

	bool isInsideCircumcircle(
		const std::vector<Point3m>& points,
		const Triangle& tri,
		const Point3m& p) const;

	bool delaunayTriangulation2D(
			MeshDocument &md,
			vcg::CallBackPos *cb,
			int numPoints,
			int randomSeed,
			Scalarm scale);
};

#endif
