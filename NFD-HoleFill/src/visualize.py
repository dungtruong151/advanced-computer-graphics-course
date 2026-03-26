"""
Visualization utilities for NFD-HoleFill.
Uses matplotlib 3D as fallback when pyvista is not available.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def trimesh_to_poly3d(mesh, color='lightblue', alpha=0.7, edgecolor='gray'):
    """Convert trimesh to matplotlib Poly3DCollection."""
    verts = mesh.vertices
    faces = mesh.faces
    polygons = [verts[face] for face in faces]
    collection = Poly3DCollection(polygons, alpha=alpha,
                                  facecolor=color, edgecolor=edgecolor,
                                  linewidth=0.1)
    return collection


def set_axes_equal(ax, mesh):
    """Set equal aspect ratio for 3D plot."""
    verts = mesh.vertices
    max_range = (verts.max(axis=0) - verts.min(axis=0)).max() / 2.0
    mid = verts.mean(axis=0)
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)


def visualize_mesh(mesh, title="Mesh", color='lightblue'):
    """Simple mesh visualization with matplotlib."""
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.add_collection3d(trimesh_to_poly3d(mesh, color=color))
    set_axes_equal(ax, mesh)
    ax.set_title(title)
    plt.tight_layout()
    plt.show()


def visualize_comparison(mesh_original, mesh_with_hole, mesh_nfd,
                         mesh_baseline=None, screenshot_path=None):
    """
    Side-by-side comparison of meshes using matplotlib.
    """
    n_cols = 4 if mesh_baseline else 3
    fig = plt.figure(figsize=(5 * n_cols, 5))

    meshes = [
        (mesh_original, "Ground Truth", 'lightblue'),
        (mesh_with_hole, "With Hole", 'lightyellow'),
        (mesh_nfd, "NFD-HoleFill (Ours)", 'lightgreen'),
    ]
    if mesh_baseline:
        meshes.append((mesh_baseline, "Baseline (Flat+Smooth)", 'lightsalmon'))

    for i, (mesh, title, color) in enumerate(meshes):
        ax = fig.add_subplot(1, n_cols, i + 1, projection='3d')
        ax.add_collection3d(trimesh_to_poly3d(mesh, color=color))
        set_axes_equal(ax, mesh)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel('X', fontsize=8)
        ax.set_ylabel('Y', fontsize=8)
        ax.set_zlabel('Z', fontsize=8)

    plt.tight_layout()

    if screenshot_path:
        plt.savefig(screenshot_path, dpi=150, bbox_inches='tight')
        print(f"Saved comparison to {screenshot_path}")
    else:
        plt.show()


def visualize_normals(mesh, normals_dict, title="Normal Field", scale=0.05):
    """Visualize normal vectors on the mesh using quiver plot."""
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    ax.add_collection3d(trimesh_to_poly3d(mesh, alpha=0.3))

    # Draw normal arrows
    points = []
    directions = []
    for vi, normal in normals_dict.items():
        if vi < len(mesh.vertices):
            points.append(mesh.vertices[vi])
            directions.append(normal * scale)

    if points:
        points = np.array(points)
        directions = np.array(directions)
        ax.quiver(points[:, 0], points[:, 1], points[:, 2],
                  directions[:, 0], directions[:, 1], directions[:, 2],
                  color='red', arrow_length_ratio=0.3, linewidth=1)

    set_axes_equal(ax, mesh)
    ax.set_title(title)
    plt.tight_layout()
    plt.show()


def plot_metrics_comparison(results, save_path=None):
    """Bar chart comparing metrics between NFD and baseline."""
    if 'baseline' not in results:
        print("No baseline results to compare.")
        return

    metrics = ['hausdorff_max', 'hausdorff_mean', 'rms_error', 'normal_deviation_deg']
    labels = ['Hausdorff\n(max)', 'Hausdorff\n(mean)', 'RMS\nError', 'Normal Dev.\n(degrees)']

    nfd_vals = [results['nfd'][m] for m in metrics]
    base_vals = [results['baseline'][m] for m in metrics]

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width / 2, base_vals, width,
                   label='Baseline', color='lightsalmon', edgecolor='gray')
    bars2 = ax.bar(x + width / 2, nfd_vals, width,
                   label='NFD-HoleFill (Ours)', color='lightgreen', edgecolor='gray')

    ax.set_ylabel('Value')
    ax.set_title('Hole Filling Quality Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.4f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.4f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved metrics chart to {save_path}")
    else:
        plt.show()
