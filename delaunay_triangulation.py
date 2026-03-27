import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay

# Generate 10 random points
np.random.seed(42)
points = np.random.rand(10, 2) * 100

# Compute Delaunay triangulation
tri = Delaunay(points)

# Plot
fig, ax = plt.subplots(figsize=(8, 8))
ax.triplot(points[:, 0], points[:, 1], tri.simplices, color='blue', linewidth=1)
ax.plot(points[:, 0], points[:, 1], 'ro', markersize=8)

for i, (x, y) in enumerate(points):
    ax.annotate("P{}".format(i), (x, y), textcoords="offset points", xytext=(5, 5), fontsize=10)

ax.set_title('Delaunay Triangulation (10 Random Points)')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
