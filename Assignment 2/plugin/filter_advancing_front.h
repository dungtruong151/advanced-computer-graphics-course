#ifndef FILTER_ADVANCING_FRONT_H
#define FILTER_ADVANCING_FRONT_H

#include <common/plugins/interfaces/filter_plugin.h>

class FilterAdvancingFrontPlugin : public QObject, public FilterPlugin
{
	Q_OBJECT
	MESHLAB_PLUGIN_IID_EXPORTER(FILTER_PLUGIN_IID)
	Q_INTERFACES(FilterPlugin)

public:
	enum {
		FP_ADVANCING_FRONT
	};

	FilterAdvancingFrontPlugin();
	virtual ~FilterAdvancingFrontPlugin();

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
	struct HoleBoundary {
		std::vector<size_t> vertexIndices;
		std::vector<Point3m> positions;
		std::vector<Point3m> normals;
	};

	struct PatchMesh {
		std::vector<Point3m>       vertices;
		std::vector<vcg::Point3i>  faces;
		std::vector<Point3m>       normals;
		std::vector<bool>          isBoundary;
		size_t                     numBoundaryVerts;
	};

	std::vector<HoleBoundary> detectHoles(CMeshO& m, int maxHoleSize);
	PatchMesh advancingFrontFill(const HoleBoundary& hole);
	void smoothPatch(PatchMesh& patch, int iterations);
	void mergePatchIntoMesh(CMeshO& m, const PatchMesh& patch, const HoleBoundary& hole);
};

#endif // FILTER_ADVANCING_FRONT_H
