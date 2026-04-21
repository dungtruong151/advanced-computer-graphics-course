#ifndef FILTER_NFD_HOLEFILL_H
#define FILTER_NFD_HOLEFILL_H

#include <common/plugins/interfaces/filter_plugin.h>

class FilterNFDHoleFillPlugin : public QObject, public FilterPlugin
{
	Q_OBJECT
	MESHLAB_PLUGIN_IID_EXPORTER(FILTER_PLUGIN_IID)
	Q_INTERFACES(FilterPlugin)

public:
	enum {
		FP_NFD_HOLEFILL
	};

	FilterNFDHoleFillPlugin();
	virtual ~FilterNFDHoleFillPlugin();

	QString pluginName() const;
	QString filterName(ActionIDType filter) const;
	QString pythonFilterName(ActionIDType f) const;
	QString filterInfo(ActionIDType filter) const;
	FilterClass getClass(const QAction* a) const;
	FilterArity filterArity(const QAction*) const;
	int getPreConditions(const QAction*) const;
	int postCondition(const QAction*) const;
	RichParameterList initParameterList(const QAction*, const MeshModel&);
	std::map<std::string, QVariant> applyFilter(
		const QAction* action,
		const RichParameterList& parameters,
		MeshDocument& md,
		unsigned int& postConditionMask,
		vcg::CallBackPos* cb);

private:
	// ---- Data structures ----
	struct HoleBoundary {
		std::vector<size_t> vertexIndices;    // ordered boundary vertex indices
		std::vector<Point3m> positions;
		std::vector<Point3m> normals;
		std::vector<Scalarm> meanCurvatures;
	};

	struct PatchMesh {
		std::vector<Point3m> vertices;
		std::vector<vcg::Point3i> faces;
		std::vector<Point3m> normals;         // per-vertex normals (diffused)
		std::vector<bool>    isBoundary;      // true if vertex is on boundary
		size_t numBoundaryVerts;
	};

	// ---- Pipeline steps ----
	std::vector<HoleBoundary> detectHoles(CMeshO& m, int maxHoleSize);

	PatchMesh triangulatePatch(const HoleBoundary& hole, Scalarm refinementFactor);

	void computeBoundaryInfo(CMeshO& m, HoleBoundary& hole);

	void diffuseNormalField(PatchMesh& patch, int iterations, Scalarm lambda);

	void displaceVertices(PatchMesh& patch, const HoleBoundary& hole, Scalarm curvatureStrength);

	void smoothPatch(PatchMesh& patch, int iterations);

	void mergePatchIntoMesh(CMeshO& m, const PatchMesh& patch, const HoleBoundary& hole);
};

#endif // FILTER_NFD_HOLEFILL_H
