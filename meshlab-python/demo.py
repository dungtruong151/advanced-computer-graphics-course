import pymeshlab

# Tao MeshSet - doi tuong chinh de lam viec voi mesh
ms = pymeshlab.MeshSet()

# Tao mot hinh cau don gian
ms.create_sphere()
print(f"Sphere: {ms.current_mesh().vertex_number()} vertices, {ms.current_mesh().face_number()} faces")

# Ap dung subdivision de tang do min
ms.apply_filter('meshing_surface_subdivision_loop', iterations=2)
print(f"After subdivision: {ms.current_mesh().vertex_number()} vertices, {ms.current_mesh().face_number()} faces")

# Luu ket qua ra file
output_file = "sphere_subdivided.ply"
ms.save_current_mesh(output_file)
print(f"Saved to {output_file}")

# Tao them mot mesh khac - hinh torus
ms.create_torus()
print(f"\nTorus: {ms.current_mesh().vertex_number()} vertices, {ms.current_mesh().face_number()} faces")

# Smooth mesh
ms.apply_filter('apply_coord_laplacian_smoothing', stepsmoothnum=3)
print("Applied Laplacian smoothing")

ms.save_current_mesh("torus_smooth.ply")
print("Saved to torus_smooth.ply")

print("\nDone! You can open the .ply files in MeshLab to view them.")
