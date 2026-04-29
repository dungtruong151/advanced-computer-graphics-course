# Normal Field Diffusion for Geometry-Aware Hole Filling in 3D Triangle Meshes: A MeshLab Plugin Implementation

**Course:** IT516 — Advanced Computer Graphics
**Institution:** International University, Vietnam National University — Ho Chi Minh City
**Author:** Truong Tri Dung (MITIU25208)
**Academic Term:** 2025–2026

---

## Abstract (Tóm tắt)

Báo cáo trình bày một phương pháp lấp lỗ (hole filling) nhận biết hình học cho lưới tam giác ba chiều, được triển khai như một plugin C++ native cho phần mềm MeshLab. Phương pháp đề xuất — **Normal Field Diffusion (NFD)** — khắc phục nhược điểm cốt lõi của các thuật toán lấp lỗ kinh điển dựa trên tam giác hóa phẳng (ear clipping, advancing front): miếng vá sinh ra không phản ánh được độ cong (curvature) và hướng pháp tuyến (normal orientation) của vùng bề mặt xung quanh lỗ. Ý tưởng trung tâm là xem ba thành phần của vector pháp tuyến như ba trường vô hướng rời rạc trên lưới vá, rồi giải phương trình khuếch tán nhiệt (heat equation) với điều kiện biên Dirichlet lấy từ pháp tuyến của vertex biên; trường nghiệm ổn định cho ta một **bản đồ hướng** mượt cho toàn miếng vá. Vị trí các vertex nội bộ được đẩy dọc theo trường pháp tuyến khuếch tán với biên độ xác định bởi **mô hình chỏm cầu (spherical-cap)**. Toàn bộ pipeline gồm 7 giai đoạn, sử dụng cotangent Laplacian bất biến theo mật độ mesh, implicit Euler cho tính ổn định số, và Taubin smoothing để khử nhiễu cao tần mà không làm suy giảm hình thái vòm. Đánh giá định lượng bằng Symmetric Hausdorff Distance trên tập test gồm sphere, cylinder, torus, Stanford Bunny và mô hình cow cho sai số tốt nhất đạt **0.12 %** so với bounding-box diagonal. Kết quả chứng minh tính khả thi và hiệu quả của NFD trong bối cảnh production tool như MeshLab.

**Keywords:** hole filling, mesh repair, normal field diffusion, cotangent Laplacian, heat equation, implicit Euler, discrete differential geometry, MeshLab.

---

## Chapter 1 — Introduction

### 1.1. Motivation

Dữ liệu lưới tam giác 3D (triangle mesh) là biểu diễn phổ biến nhất cho hình học bề mặt trong computer graphics và digital geometry processing. Tuy nhiên, mesh thu được từ các nguồn thực tế hiếm khi là **watertight manifold** hoàn chỉnh. Các pipeline thu nhận dữ liệu — structured-light scanning, photogrammetry, LiDAR, volumetric reconstruction từ RGB-D — đều sinh ra lỗ (hole) vì:

- **Self-occlusion:** vùng bề mặt bị che khuất từ mọi góc chụp khả dụng.
- **Vật liệu khó scan:** bề mặt phản chiếu cao (kim loại bóng), trong suốt (thủy tinh), hấp thụ mạnh (vải đen, tóc).
- **Sensor noise:** confidence thấp dẫn đến loại bỏ vùng không đáng tin cậy.
- **Post-processing:** cắt mesh theo region of interest, remesh thất bại cục bộ.
- **Reconstruction artifacts:** các thuật toán như Poisson reconstruction có thể để lại lỗ khi dữ liệu đầu vào sparse.

Lỗ trong mesh gây ra nhiều hậu quả downstream: rendering lộ mặt trong và gây z-fighting; simulation vật lý (FEM, CFD) yêu cầu domain kín; in 3D (FDM/SLA) cần mesh watertight để tính slicing; subdivision và remeshing bị phá vỡ topology. Do đó, **hole filling** — tự động sinh miếng vá hình học hợp lý cho các lỗ — là một bài toán nền tảng trong mesh repair pipeline.

### 1.2. Problem Statement

Cho một lưới tam giác $\mathcal{M} = (V, F)$ với tập đỉnh $V \subset \mathbb{R}^3$ và tập mặt tam giác $F$, ta xác định một **lỗ** là một chuỗi cạnh biên (border edges) tạo thành chu trình khép kín. Bài toán lấp lỗ đòi hỏi sinh ra một tập đỉnh mới $V'$ và tập mặt mới $F'$ sao cho $\mathcal{M}' = (V \cup V', F \cup F')$:

1. **Topology:** lỗ ban đầu bị đóng kín, $\mathcal{M}'$ trở thành 2-manifold không có border quanh vùng lấp.
2. **Geometry:** miếng vá **tiếp nối hình học** một cách tự nhiên với vùng lân cận — tức là tiếp tuyến và độ cong của miếng vá nên xấp xỉ tiếp tuyến và độ cong của $\mathcal{M}$ gần biên lỗ.
3. **Quality:** các tam giác trong miếng vá có kích thước và hình dạng tương thích với mật độ mesh gốc; không có slivers hay non-manifold edges.

Mục tiêu (2) là phần **khó** và là trọng tâm của báo cáo này. Các phương pháp kinh điển chỉ đạt được (1) và thường chỉ một phần (3), bỏ qua (2) hoàn toàn.

### 1.3. Contributions

Báo cáo đưa ra các đóng góp chính sau:

1. **Triển khai C++ native** đầy đủ của phương pháp Normal Field Diffusion bên trong kiến trúc plugin của MeshLab, sử dụng VCGlib cho topology và Eigen cho sparse linear algebra.

2. **Cải tiến thuật toán ear clipping**: chọn "best ear" theo tiêu chí **max-min interior angle** thay vì FIFO đơn giản, loại bỏ artifact fan-from-single-pivot kinh điển.

3. **Pipeline ổn định số**: sử dụng implicit Euler với SimplicialLDLT factorization một lần, cho phép chạy lambda lớn mà không bị unstable, và giữ O(B²) per iteration sau khi factorize.

4. **Mô hình chỏm cầu (spherical-cap) cho chiều cao vòm**: suy ra biên độ displacement từ geometry invariants (bán kính trung bình $r$, góc trung bình $\theta$) thay vì tham số thủ công, cho tính bất biến theo scale và xoay.

5. **Spherical-cap weighting profile** $w(t) = \sqrt{2t - t^2}$ thay vì parabolic $4t(1-t)$ truyền thống, đảm bảo tiếp tuyến mượt tại biên (C¹ continuity gần boundary).

6. **Quantitative evaluation** sử dụng Symmetric Hausdorff Distance hai chiều trên tập test sáu mô hình, phân tích sai số forward/reverse để định lượng kích thước patch và độ sát bề mặt.

### 1.4. Report Structure

Chapter 2 review các approach kinh điển và hiện đại cho hole filling. Chapter 3 trình bày nền tảng toán học: Laplace-Beltrami operator rời rạc, cotangent weights, heat equation trên manifold. Chapter 4 mô tả chi tiết pipeline bảy bước. Chapter 5 thảo luận implementation và kiến trúc plugin. Chapter 6 trình bày experimental results và phân tích định lượng. Chapter 7 thảo luận strengths, limitations, failure modes. Chapter 8 kết luận và đề xuất hướng mở rộng.

---

## Chapter 2 — Related Work

### 2.1. Classical Geometric Hole Filling

**Advancing front approaches** (Liepa, 2003; Zhao et al., 2007) nối các cạnh biên bằng cách liên tục chèn tam giác mới từ front hiện tại, dùng heuristic như góc nhỏ nhất hay tỉ lệ cạnh. Ưu điểm: đơn giản, xử lý được lỗ topology phức tạp. Nhược điểm: miếng vá có xu hướng phẳng, không khớp độ cong; kết quả phụ thuộc mạnh vào thứ tự duyệt front.

**Ear clipping** (Meisters, 1975; Held, 2001) là phương pháp tam giác hóa đa giác đơn giản: duyệt đa giác 2D, mỗi lần loại bỏ một "tai" — tam giác lồi không chứa đỉnh nào khác. Ear clipping có thể mở rộng cho 3D hole filling bằng cách chiếu boundary xuống mặt phẳng trung bình. Độ phức tạp $O(n^2)$ naive hoặc $O(n \log n)$ với search acceleration. Hạn chế: miếng vá hoàn toàn phẳng, cần bước refinement riêng để bend theo curvature.

**Delaunay-based triangulation** (Barequet & Sharir, 1995) sinh tam giác hóa tối ưu theo tiêu chí max-min angle trên mặt phẳng chiếu. Thường được kết hợp với ear clipping qua bước edge-flip sau tam giác hóa ban đầu, gọi là Lawson flip algorithm.

### 2.2. Variational and PDE-based Methods

**Minimum surface approach** (Botsch & Kobbelt, 2004) giải bài toán biến phân: tìm lưới nội bộ tối thiểu hóa diện tích với ràng buộc biên cố định. Dẫn đến việc giải hệ tuyến tính trên mesh Laplacian. Cho kết quả tốt trên bề mặt lồi nhưng biên độ cong thường bị suy giảm (**shrinkage**).

**Thin-plate spline / bi-harmonic interpolation** (Nealen et al., 2005; Kazhdan & Hoppe, 2013) giải phương trình $\Delta^2 u = 0$ trên patch với điều kiện biên cung cấp cả vị trí và đạo hàm một. Tạo ra miếng vá C² mượt. Chi phí: cần giải hệ lớn hơn, điều kiện biên phức tạp hơn.

**Poisson surface reconstruction** (Kazhdan et al., 2006) — không phải hole filler đơn lẻ, nhưng khi áp dụng trên toàn mesh + normal field, có thể "lấp lỗ" như hệ quả phụ. Hạn chế: cần global reconstruction; tốn tài nguyên; có thể biến đổi phần mesh lân cận lỗ không mong muốn.

### 2.3. Normal / Curvature-Based Approaches

**Verdera et al. (2003)** đề xuất image-inpainting trên bề mặt bằng cách khuếch tán trường vector pháp tuyến qua PDE phi tuyến — là nguồn cảm hứng trực tiếp cho NFD. Tuy nhiên, approach của Verdera hoạt động trên level-set representation, không phải triangle mesh.

**Wang & Oliveira (2007)** áp dụng normal interpolation trên mesh cho hole filling, dùng radial basis functions. Không dùng framework PDE; độ mượt phụ thuộc chọn kernel.

**Jun (2005)** dùng moving least squares trên normal field. Phương pháp này không mở rộng tốt cho lỗ to vì không có ràng buộc trơn toàn cục.

**Zhao, Gao & Lin (2007)** kết hợp Poisson fairing và boundary-based displacement — gần với ý tưởng project này nhưng sử dụng Poisson equation cho position, không phải diffusion cho normals.

### 2.4. Position of This Work

Báo cáo này tích hợp:

- **Ear clipping** (với cải tiến best-ear) cho tam giác hóa khung miếng vá (Sec. 2.1).
- **Delaunay edge flipping** cho quality refinement.
- **Heat-equation diffusion** áp dụng cho normal field (ý tưởng Verdera) — nhưng triển khai rời rạc trên mesh bằng cotangent Laplacian thay vì level-set PDE.
- **Implicit Euler** cho ổn định số — khác hẳn các phương pháp normal-based dùng explicit iterations hoặc non-iterative solvers.
- **Spherical-cap displacement model** — đóng góp mới, suy ra biên độ vòm từ intrinsic geometry của boundary, không cần user-specified amplitude.

Phương pháp được thiết kế cho **interactive production use** trong MeshLab, nên ưu tiên tốc độ (factorize một lần, solve nhiều lần) và robustness (multiple NaN/degeneracy guards).

---

## Chapter 3 — Preliminaries

### 3.1. Triangle Mesh Representation

Một lưới tam giác 2-manifold được định nghĩa bởi cặp $\mathcal{M} = (V, F)$ với:

- $V = \{v_1, v_2, \ldots, v_n\} \subset \mathbb{R}^3$: tập đỉnh.
- $F \subset V^3$: tập mặt tam giác, mỗi $f = (v_a, v_b, v_c)$ định nghĩa thứ tự đỉnh (ảnh hưởng hướng pháp tuyến qua quy tắc tay phải).

**Border edge (cạnh biên):** một cạnh $e = (v_i, v_j)$ thuộc đúng **một** mặt $f \in F$. Trong mesh watertight, mọi cạnh thuộc đúng hai mặt. Tập border edges của $\mathcal{M}$ được ký hiệu $\partial \mathcal{M}$.

**Hole (lỗ):** thành phần liên thông cực đại của $\partial \mathcal{M}$ trong đồ thị edge-vertex.

### 3.2. Face and Vertex Normals

**Face normal** của tam giác $f = (v_a, v_b, v_c)$:

$$
\mathbf{n}_f = \frac{(v_b - v_a) \times (v_c - v_a)}{\|(v_b - v_a) \times (v_c - v_a)\|}
$$

**Area-weighted vertex normal:**

$$
\mathbf{n}_i = \frac{\sum_{f \in \mathcal{N}(v_i)} A_f \mathbf{n}_f}{\left\|\sum_{f \in \mathcal{N}(v_i)} A_f \mathbf{n}_f\right\|}
$$

với $\mathcal{N}(v_i)$ là tập mặt kề vertex $v_i$ và $A_f$ là diện tích mặt $f$. VCGlib cache vertex normals qua trường `N()` của vertex sau khi gọi `PerVertexNormalizedPerFace`.

### 3.3. Discrete Laplace-Beltrami Operator

Laplace-Beltrami operator trên manifold liên tục $\mathcal{S}$ được định nghĩa là divergence của gradient: $\Delta_{\mathcal{S}} f = \nabla \cdot \nabla f$. Trên triangle mesh, tồn tại nhiều cách rời rạc hóa; lựa chọn ảnh hưởng trực tiếp đến chất lượng kết quả geometry processing.

**Uniform (combinatorial) Laplacian:**

$$
L_u(v_i) = \frac{1}{|\mathcal{N}(v_i)|} \sum_{v_j \in \mathcal{N}(v_i)} (v_j - v_i)
$$

Đơn giản, rẻ, nhưng **không bất biến theo mật độ mesh** — re-mesh dense hoặc sparse cho Laplacian khác nhau. Không xấp xỉ tốt $\Delta_{\mathcal{S}}$ liên tục.

**Cotangent Laplacian** (Pinkall & Polthier, 1993; Meyer et al., 2003):

$$
L_{\text{cot}}(v_i) = \frac{1}{2 A_i} \sum_{v_j \in \mathcal{N}(v_i)} (\cot \alpha_{ij} + \cot \beta_{ij}) (v_j - v_i)
$$

với $\alpha_{ij}, \beta_{ij}$ là hai góc đối diện cạnh $(v_i, v_j)$ trong hai mặt chia sẻ cạnh, và $A_i$ là diện tích Voronoi (hay mixed Voronoi/barycentric) xung quanh $v_i$. Cotangent Laplacian xấp xỉ bậc nhất $\Delta_{\mathcal{S}}$ và **bất biến theo remeshing** (vertex-intrinsic property). Đây là định nghĩa tiêu chuẩn trong discrete differential geometry hiện đại.

**Mean curvature normal:** công thức nổi tiếng (Meyer et al.):

$$
L_{\text{cot}}(v_i) = 2 H(v_i) \mathbf{n}(v_i)
$$

Do đó mean curvature có thể được xấp xỉ qua norm của cotangent Laplacian: $H \approx \|L_{\text{cot}}\| / 2$.

### 3.4. Heat Equation on Manifolds

Phương trình khuếch tán nhiệt (heat equation) trên manifold:

$$
\frac{\partial u}{\partial t} = \lambda \, \Delta_{\mathcal{S}} u, \quad u : \mathcal{S} \times \mathbb{R}_+ \to \mathbb{R}
$$

với điều kiện biên Dirichlet $u|_{\partial \Omega} = g$. Nghiệm khi $t \to \infty$ hội tụ về **harmonic extension** của $g$ vào nội bộ $\Omega$ — tức nghiệm mượt nội suy boundary data.

**Property:** heat equation là parabolic, có **maximum principle**: giá trị bên trong không vượt quá cực đại trên biên. Khi áp dụng cho normal components, đặc tính này đảm bảo normal field nội suy không "bùng nổ" ngoài khoảng giá trị boundary.

### 3.5. Time Discretization: Explicit vs Implicit Euler

Rời rạc thời gian cho heat equation yêu cầu chọn scheme. Gọi $\mathbf{u}^t \in \mathbb{R}^{|V|}$ là vector giá trị tại thời điểm $t$, $L$ là Laplacian matrix, $\Delta t$ là time step.

**Explicit (forward) Euler:**

$$
\mathbf{u}^{t+1} = \mathbf{u}^t + \Delta t \cdot L \mathbf{u}^t = (I + \Delta t \cdot L) \mathbf{u}^t
$$

Đơn giản, chỉ cần matrix-vector product. **Nhược điểm:** điều kiện ổn định CFL đòi hỏi $\Delta t < c / \rho(L)$ với $\rho(L)$ là bán kính phổ. Trên mesh dense, $\rho(L)$ lớn → $\Delta t$ rất nhỏ → cần nhiều iteration.

**Implicit (backward) Euler:**

$$
\mathbf{u}^{t+1} = \mathbf{u}^t + \Delta t \cdot L \mathbf{u}^{t+1} \Longrightarrow (I - \Delta t \cdot L) \mathbf{u}^{t+1} = \mathbf{u}^t
$$

Yêu cầu giải hệ tuyến tính tại mỗi step. **Ưu điểm: unconditionally stable** với mọi $\Delta t > 0$ (A-stable). Dẫn đến matrix $(I - \Delta t \cdot L)$ SPD (symmetric positive definite) khi $L$ SPD, cho phép dùng Cholesky factorization.

Project này dùng implicit Euler với dạng tương đương: $(I + \lambda L) \mathbf{u}^{t+1} = \mathbf{u}^t$ vì ta dùng quy ước $L$ với dấu dương (toán tử chính xác là $-\Delta$).

### 3.6. Sparse Linear Solvers

Matrix $A = I + \lambda L$ là SPD khi $L$ SPD, sparse với cấu trúc giống adjacency. Các solvers phù hợp:

- **Direct methods** (Cholesky, $LDL^T$): phân rã một lần, solve $O(B + |E|)$ mỗi lần với B đỉnh nội bộ, E cạnh. Dùng **SimplicialLDLT** trong Eigen — biến thể đơn giản hóa của Cholesky không yêu cầu square-root, phù hợp cho SPD.
- **Iterative methods** (Conjugate Gradient): không cần factorize nhưng convergence phụ thuộc condition number; thường chậm hơn trên bài toán cỡ vừa.

Project dùng **SimplicialLDLT** vì: (i) $B$ thường nhỏ (< 10⁴), fit memory tốt; (ii) ta chạy nhiều iteration với cùng ma trận, amortize factorization cost.

### 3.7. Taubin λ|μ Smoothing

Laplacian smoothing chuẩn (Desbrun et al., 1999): $v_i^{(k+1)} = v_i^{(k)} + \lambda L(v_i^{(k)})$. **Vấn đề:** gây shrinkage — bề mặt co dần về centroid sau nhiều iteration.

**Taubin (1995)** đề xuất xen kẽ hai bước với hệ số trái dấu:

1. Shrinking step: $v^{(k+0.5)} = v^{(k)} + \lambda L(v^{(k)})$ với $\lambda > 0$.
2. Inflating step: $v^{(k+1)} = v^{(k+0.5)} + \mu L(v^{(k+0.5)})$ với $\mu < 0$, $|\mu| > \lambda$.

Transfer function $f(k) = (1 - \lambda k)(1 - \mu k)$ là **low-pass filter**: $f(0) = 1$ (giữ DC = vị trí trung bình), $f$ nhỏ ở tần cao (khử high-frequency noise), gần 1 ở tần thấp (giữ hình dạng lớn). Không shrinkage khi tham số được chọn đúng.

Project dùng $\lambda = 0.40$, $\mu = -0.44$, ba cặp (tương đương sáu Laplacian step).

---

## Chapter 4 — Methodology

### 4.1. Pipeline Overview

Pipeline tổng gồm bảy giai đoạn, mỗi giai đoạn được implement như một phương thức riêng trong class `FilterNFDHoleFillPlugin`:

```
Input mesh M with holes
       │
[1] Hole Detection         → danh sách HoleBoundary
       │
[2] Boundary Analysis       → normals + mean curvatures per boundary vertex
       │
[3] Initial Triangulation   → flat patch mesh (ear clip + Delaunay + refine)
       │
[4] Normal Field Diffusion  → normals cho mọi vertex nội bộ (CORE)
       │
[5] Laplacian Smoothing     → phân bố đều vertex trên patch phẳng
       │
[6] Curvature Displacement  → bend patch theo normal field
       │
[7] Patch Merging           → ghép patch vào M, update topology
       │
Output: mesh với lỗ đã lấp
```

Thứ tự (5) trước (6) là lựa chọn thiết kế quan trọng: uniform Laplacian smoothing sẽ phá hủy mái vòm nếu áp dụng sau displacement.

### 4.2. Step 1 — Hole Detection

**Input:** mesh $\mathcal{M}$ với topology đã được cập nhật (Face-Face, Vertex-Face adjacency, border flags).
**Output:** danh sách các `HoleBoundary`, mỗi phần tử lưu chuỗi chỉ số vertex theo thứ tự đi vòng quanh mép lỗ.

#### 4.2.1. Topology Preparation

Trước khi dò lỗ, VCGlib được yêu cầu build adjacency:

- `FFAdjacency`: mỗi face biết 3 face kề qua cạnh.
- `VFAdjacency`: mỗi vertex biết face "đại diện"; face tạo linked list qua tất cả face kề.
- `FaceBorderFromFF`: quét FF pointers, bật cờ border cho cạnh có face kề trỏ về chính mình (không có láng giềng).
- `VertexBorderFromFaceBorder`: lan cờ từ face-level lên vertex-level.

Sau bước này, predicate `vcg::face::IsBorder(f, e)` chỉ trả về flag cached, $O(1)$.

#### 4.2.2. Boundary Loop Extraction

Thuật toán chính là BFS biến thể trên đồ thị border edges:

```
for each face f in M:
  for each local edge e in {0, 1, 2}:
    if IsBorder(f, e) and edge (V(e), V(e+1)) ∉ visited:
      walk the boundary loop from this edge
```

Với mỗi boundary loop, quy trình walk như sau:

```
start ← V(e)
curr ← V(e), next ← V((e+1) mod 3)
loop:
  push curr to hole.vertexIndices
  mark edge (curr, next) as visited
  prev ← curr; curr ← next
  if curr == start: loop complete, break
  
  find next border edge emanating from curr:
    for each face f in VF(curr):
      for each local edge (a, b) in f:
        if a == curr and b ≠ prev and IsBorder(f, edge):
          next ← b; foundNext ← true; break
  
  if not foundNext: break (non-manifold recovery)
```

Ba predicates đồng thời `a == curr`, `b ≠ prev`, `IsBorder` xác định duy nhất cạnh tiếp theo trong mesh manifold. Trên vertex biên của 2-manifold, chỉ có đúng **hai** border edge kề; việc loại trừ `prev` đảm bảo tiến về phía trước.

#### 4.2.3. Robustness Mechanisms

1. **visitedEdges set**: tránh trace cùng một lỗ nhiều lần khi iterate qua nhiều face.
2. **safety counter** `< maxHoleSize * 2`: watchdog chống vòng lặp vô hạn khi mesh non-manifold.
3. **foundNext = false → break**: xử lý clean trường hợp cạnh biên cô lập.
4. **Post-validation**: chỉ accept loop thỏa `loopComplete ∧ 3 ≤ size ≤ maxHoleSize`.

**Độ phức tạp:** $O(|F| + \sum_h L_h \cdot d)$ với $L_h$ là chu vi lỗ $h$ và $d$ là degree trung bình của vertex (hằng số ≈ 6 trên mesh regular).

### 4.3. Step 2 — Boundary Analysis

**Input:** một `HoleBoundary` chứa chỉ số và tọa độ vertex biên.
**Output:** normal $\mathbf{n}_i$ và mean curvature $H_i$ cho mỗi vertex biên.

#### 4.3.1. Per-Vertex Normal

Area-weighted normal đã được VCG tính sẵn qua `PerVertexNormalizedPerFace`. Code chỉ đọc và re-normalize để đảm bảo $\|\mathbf{n}_i\| = 1$ (bảo vệ trước trường hợp VCG chưa normalize vì một số path trong API không tự động normalize).

#### 4.3.2. Mean Curvature via Cotangent Laplacian

Với mỗi vertex biên $v_i$, duyệt qua tất cả face $f \in \mathcal{N}(v_i)$. Trong mỗi face $(v_i, v_B, v_C)$ với $v_i$ đóng vai trò A:

$$
\cot(\angle C) \text{ đóng góp vào } w_{iB}, \quad \cot(\angle B) \text{ đóng góp vào } w_{iC}
$$

Sau khi quét mọi face, `cotWeights[j] = cot α_{ij} + cot β_{ij}` đúng như công thức chuẩn, không cần tường minh tìm cặp face qua FF adjacency.

#### 4.3.3. Efficient Cotangent Computation

Cotangent tại góc giữa hai vector $\vec{AB}, \vec{AC}$:

$$
\cot \theta = \frac{\cos \theta}{\sin \theta} = \frac{\vec{AB} \cdot \vec{AC}}{\|\vec{AB} \times \vec{AC}\|}
$$

Công thức này tránh gọi `acos`/`sin` (chậm và mất chính xác ở góc extreme), chỉ dùng dot và cross product. Guard `\|\vec{AB} \times \vec{AC}\| < \epsilon` chống degenerate triangle.

#### 4.3.4. Negative Cotangent Clamping

Tam giác có góc $> 90°$ cho $\cot$ âm. Weight âm có thể gây Laplacian vượt convex hull của láng giềng, dẫn đến instability. Project clamp: $w \leftarrow \max(w, 0)$. Đây là trade-off đơn giản; một alternative chuẩn hơn là intrinsic Delaunay triangulation (Sharp & Crane, 2020) nhưng đắt gấp nhiều lần.

Mean curvature cuối cùng: $H_i = \|L\| / (2 \sum_j w_{ij})$, fallback 0 nếu $\sum w < \epsilon$.

### 4.4. Step 3 — Initial Triangulation

**Input:** `HoleBoundary` với `positions` và `normals`.
**Output:** `PatchMesh` chứa vertices (boundary + interior), faces, isBoundary flags.

Bốn tiểu bước:

#### 4.4.1. 2D Projection

Xây dựng local frame từ average boundary normal:

$$
\bar{\mathbf{n}} = \frac{1}{|\partial|} \sum_{i} \mathbf{n}_i, \quad \bar{\mathbf{n}} \leftarrow \bar{\mathbf{n}} / \|\bar{\mathbf{n}}\|
$$

Chọn $\mathbf{u}$ vuông góc $\bar{\mathbf{n}}$ (trong code qua hàm `buildLocalFrame` — chọn axis tránh gần collinear với $\bar{\mathbf{n}}$), rồi $\mathbf{v} = \bar{\mathbf{n}} \times \mathbf{u}$.

Projected 2D coordinates: $(p_{x,i}, p_{y,i}) = ((v_i - c) \cdot \mathbf{u}, (v_i - c) \cdot \mathbf{v})$ với $c$ là centroid 3D của boundary.

**Orientation check via shoelace formula:**

$$
2 \cdot \text{SignedArea} = \sum_i (p_{x,i} p_{y,i+1} - p_{x,i+1} p_{y,i})
$$

Nếu âm (CW), đảo vertex order để chuẩn hóa về CCW — quan trọng cho ear clipping convexity test.

#### 4.4.2. Best-Ear Clipping

Duyệt tất cả "ears" (tam giác $(p_{a}, p_{b}, p_{c})$ lồi không chứa vertex nào khác), với mỗi ear tính **minimum interior angle**:

```
angles = [angle_at_pa, angle_at_pb, angle_at_pc]
min_angle(ear) = min(angles)
```

Chọn ear có `min_angle` **lớn nhất** (most equilateral), clip vertex trung tâm, lặp. Đây là cải tiến quan trọng: FIFO hay greedy đơn giản sẽ tạo fan-from-single-pivot — miếng vá toàn sliver. Max-min-angle heuristic đảm bảo tam giác tương đối cân.

**Fallback layers:**
- Nếu không tìm được ear hợp lệ (mesh degenerate), clip vertex lồi đầu tiên.
- Nếu vẫn fail, force-clip vertex thứ 2 để tránh infinite loop.

**Winding correction (post-hoc):** sau clipping, kiểm tra $(\vec{AB} \times \vec{AC}) \cdot \bar{\mathbf{n}} < 0$ → swap $V_1 \leftrightarrow V_2$ của mọi face để đảm bảo outward-facing normals.

#### 4.4.3. Delaunay-Like Edge Flipping

Với mỗi cặp tam giác chia sẻ cạnh nội bộ $(u, v)$, xét diagonal $(w, x)$ với $w, x$ là hai vertex đối diện. Nếu $\min(\angle \text{after}) > \min(\angle \text{before}) + \epsilon$, thực hiện flip.

**Winding derivation:** flip phải giữ orientation consistent. Code phát hiện thứ tự cạnh trong tam giác gốc $t_1$:

```
Case A: t_1 có edge u→v (v sau u trong cyclic order của t_1)
  → new t_1 = (u, x, w), new t_2 = (v, w, x)
Case B: t_1 có edge v→u
  → new t_1 = (u, w, x), new t_2 = (v, x, w)
```

Constraint: không flip nếu diagonal mới $(w, x)$ đã tồn tại (tránh degenerate mesh). Không flip cặp có chung face với cặp đã flip trong pass hiện tại (tránh conflict).

**Max 10 passes, early break if no flip in a pass.** Thực tế hội tụ trong 2-3 passes trên mesh bình thường.

#### 4.4.4. Centroid Refinement

Kích thước target: $s_{\text{target}} = \bar{e} \cdot \text{RefinementFactor}$ với $\bar{e}$ là độ dài trung bình cạnh biên. Diện tích target cho equilateral triangle: $A_{\text{target}} = s_{\text{target}}^2 \cdot \sqrt{3}/4 \approx 0.433 \cdot s_{\text{target}}^2$.

Với mỗi face có $A > 1.5 \cdot A_{\text{target}}$: chèn centroid $(v_0 + v_1 + v_2)/3$ làm interior vertex, chia face thành 3 faces mới.

**Max 8 passes, hard cap 200 000 faces** để tránh blow-up khi user cung cấp `RefinementFactor` quá nhỏ.

Sau refinement, **pass Delaunay flip thứ hai** được thực hiện vì centroid insertion có thể tạo sliver mới.

### 4.5. Step 4 — Normal Field Diffusion (Core)

**Input:** `PatchMesh` với normals đã có ở boundary vertices, interior normals uninitialized.
**Output:** normal field mượt phủ toàn patch.

#### 4.5.1. Mathematical Formulation

Trên patch $\Omega$ với boundary $\partial \Omega$, giải ba bài toán độc lập cho từng component:

$$
\frac{\partial n_k}{\partial t} = \lambda \, \Delta_{\Omega} n_k, \quad k \in \{x, y, z\}
$$

với boundary condition Dirichlet: $n_k|_{\partial \Omega} = n_{k,\text{fixed}}$. Khi $t \to \infty$, nghiệm hội tụ về harmonic extension — nội suy mượt nhất (theo nghĩa Dirichlet energy) từ boundary vào interior. Chạy số hữu hạn iterations cho approximation đủ tốt mà không sát boundary quá cứng.

#### 4.5.2. Discretization

Cotangent Laplacian $L_{\text{cot}}$ được build trên patch (không phải mesh gốc). Với mỗi face, cộng $\cot$ tại góc đối diện vào weight của cạnh tương ứng — tương tự Sec. 4.3.2.

Implicit Euler discretization:

$$
(\mathbf{I} + \lambda L_{\text{cot}}) \mathbf{n}^{t+1}_{\text{int}} = \mathbf{n}^t_{\text{int}} + \lambda \mathbf{b}
$$

với $\mathbf{n}_{\text{int}}$ là vector component-wise của $B$ interior vertices, và $\mathbf{b}$ là Dirichlet contribution:

$$
b_i = \sum_{j \in \partial \cap \mathcal{N}(i)} w_{ij} \, n_j^{\text{fixed}}
$$

#### 4.5.3. Matrix Assembly

Matrix $A = I + \lambda L_{\text{cot}}$ kích thước $B_{\text{int}} \times B_{\text{int}}$:

- **Diagonal:** $A_{ii} = 1 + \lambda \sum_j w_{ij}$ (sum qua **mọi** neighbor, cả boundary và interior — vì boundary contribution được đưa vào RHS, LHS cần tổng đầy đủ).
- **Off-diagonal:** $A_{ij} = -\lambda w_{ij}$ chỉ cho interior neighbor $j$.

Dùng `Eigen::Triplet` list để accumulate entries rồi `setFromTriplets` build sparse matrix CSR. Đây là pattern chuẩn của Eigen cho sparse construction.

#### 4.5.4. Factorization and Iteration

```cpp
Eigen::SimplicialLDLT<SpMat> solver;
solver.compute(A);    // LDL^T factorization — ONCE

for (int iter = 0; iter < iterations; iter++) {
    // Rebuild RHS: current interior normals + boundary contribution
    rhs = currentNormals + lambda * boundaryContribution;
    currentNormals = solver.solve(rhs);    // fast triangular solves
}

normalize(currentNormals);
```

Factorize chi phí $O(B_{\text{int}}^{1.5})$ typical (tùy sparsity). Mỗi solve $O(B_{\text{int}})$ cho sparse SPD. Với 50 iterations, tổng chi phí iteration tuyến tính với số nonzero, rất nhanh.

#### 4.5.5. Boundary Treatment

Boundary normals **không** xuất hiện trong unknown vector — chúng cố định và chỉ xuất hiện qua RHS. Điều này tương đương eliminate các boundary DOFs trước khi factorize. Đây là cách chuẩn xử lý Dirichlet condition trong FEM.

#### 4.5.6. Post-Processing

Sau iterations, normalize mỗi normal về độ dài đơn vị. Trường hợp $\|\mathbf{n}\| < 10^{-10}$, bỏ qua normalization (giữ zero vector, sẽ bị downstream detect và replace).

**NaN detection (outer layer):** sau `diffuseNormalField` return, driver kiểm tra mọi normal; nếu có NaN (có thể xảy ra khi cotangent Laplacian suy biến), reset interior normals về average boundary normal. Đây là safety net, không phải failure mode thường gặp.

### 4.6. Step 5 — Laplacian Smoothing

**Input:** flat `PatchMesh` với normal field đã khuếch tán nhưng positions chưa bend.
**Output:** patch với interior positions redistributed uniformly.

Thuật toán đơn giản: uniform Laplacian iterations với boundary fixed:

$$
v_i^{(k+1)} = \frac{1}{|\mathcal{N}(v_i)|} \sum_{v_j \in \mathcal{N}(v_i)} v_j^{(k)}, \quad v_i \in \text{interior}
$$

Lặp `SmoothingIterations` lần (mặc định 3). Boundary vertices hold fixed để giữ khung patch khớp với mesh gốc.

**Chủ ý dùng uniform thay vì cotangent:** mục tiêu là redistribution đều trên patch (tần số cao = spatial distribution), không phải xấp xỉ Laplace-Beltrami chính xác. Uniform đơn giản và đủ dùng.

**Ordering constraint (5) → (6):** chạy smoothing sau displacement sẽ reduce curvature của mái vòm vì uniform Laplacian có **shrinkage property** (Taubin, 1995). Đây là lý do trật tự 5-before-6 mang tính bắt buộc.

### 4.7. Step 6 — Curvature-Guided Displacement

**Input:** patch phẳng với normals đã khuếch tán + positions đã smooth.
**Output:** patch bent thành mái vòm đúng curvature.

#### 4.7.1. Scale Estimation via Spherical-Cap Model

Coi lỗ như đang nằm trên một mặt cầu tưởng tượng tiếp xúc mesh tại boundary. Cap height được suy ra từ geometry invariants:

**Mean radius:**

$$
r = \frac{1}{|\partial|} \sum_{v_i \in \partial} \|v_i - c_{\partial}\|, \quad c_{\partial} = \frac{1}{|\partial|} \sum_i v_i
$$

**Mean deviation angle:**

$$
\bar{d} = \frac{1}{|\partial|} \sum_i \mathbf{n}_i \cdot \bar{\mathbf{n}}, \quad \theta = \arccos(\bar{d})
$$

**Cap height:**

$$
h = r \cdot \tan(\theta / 2) \cdot \text{CurvatureStrength}
$$

Công thức suy ra từ hình học chỏm cầu: nếu lỗ nằm trên sphere bán kính $R$ với half-angle $\theta/2$, thì $r = R \sin(\theta/2)$ và cap height $= R(1 - \cos(\theta/2))$. Thay vào: $h = r \cdot (1 - \cos(\theta/2)) / \sin(\theta/2) = r \cdot \tan(\theta/2)$ sau biến đổi lượng giác.

**Average over max:** các implementation trước dùng $\theta_{\max} = \max_i \arccos(\mathbf{n}_i \cdot \bar{\mathbf{n}})$. Trên meshes non-spherical (Bunny, Torus) với vài boundary vertex có normal noisy, $\theta_{\max}$ cho overshoot mạnh. Dùng average angle mang tính robust statistics, giảm sensitivity với outliers — đóng góp thực nghiệm của báo cáo này.

#### 4.7.2. Multi-Source Dijkstra for Geodesic Distance

Để gán weight đúng cho mỗi interior vertex, cần biết vị trí tương đối của nó so với boundary. Euclidean distance không đủ tốt trên patch không lồi; dùng **geodesic distance** (khoảng cách ngắn nhất trên graph edges).

Implementation: Dijkstra's algorithm với **priority queue** và **multi-source initialization**:

```
dist[v] ← 0 for all v ∈ boundary
dist[v] ← ∞ for all v ∈ interior
pq ← priority queue of (dist, v)
push all boundary vertices

while pq not empty:
  (d, u) ← pop min
  if d > dist[u]: continue  // stale entry
  for (v, edge_length) in adj[u]:
    if dist[u] + edge_length < dist[v]:
      dist[v] ← dist[u] + edge_length
      push (dist[v], v)
```

Edge weights = Euclidean length của cạnh trong patch 3D. Đây là xấp xỉ bậc nhất của geodesic trên surface; đủ tốt cho patch nhỏ.

**Normalize:** $t_i = \text{dist}_i / \max_j \text{dist}_j \in [0, 1]$, với $t = 0$ ở boundary và $t = 1$ ở farthest interior vertex (approximately center).

#### 4.7.3. Spherical-Cap Profile

Weighting profile:

$$
w(t) = \sqrt{2t - t^2}
$$

**Derivation:** xét unit circle $x^2 + y^2 = 1$. Tại offset horizontal $(1 - t)$ từ right edge, height $y = \sqrt{1 - (1-t)^2} = \sqrt{2t - t^2}$. Nghĩa là $w(t)$ là cross-section chiều cao của bán cầu đơn vị — đúng với giả thiết chỏm cầu.

**Properties:**

- $w(0) = 0$: boundary không dịch chuyển (continuity with mesh gốc).
- $w(1) = 1$: center reaches full cap height.
- **$w'(0) = \infty$:** tiếp tuyến thẳng đứng ở $t = 0$ — trong không gian 3D, điều này có nghĩa tiếp tuyến của mái vòm **vuông góc với trục chỏm cầu** ở biên, tức là **song song với mặt phẳng tiếp tuyến của mesh tại boundary** → **C¹ continuity** với mesh gốc.

**So sánh với parabolic profile** $w(t) = 4t(1-t)$: parabolic có $w'(0) = 4$ hữu hạn, gây "gãy" (kink) tại junction giữa patch và mesh. Spherical-cap mang lại smoothness visually significant, dễ nhận ra trên ảnh render.

#### 4.7.4. Final Displacement

Với mỗi interior vertex:

$$
v_i' = v_i + h \cdot w(t_i) \cdot \mathbf{n}_i^{\text{diffused}}
$$

Direction được quyết định bởi diffused normal (Step 4) — không phải boundary average normal. Điều này cho phép patch có curvature biến đổi (không đồng nhất) khớp với hình học xung quanh: ví dụ lỗ trên rãnh (furrow) sẽ có patch bend theo rãnh, không chỉ lồi đơn điệu.

#### 4.7.5. Taubin Post-Smoothing

Sau displacement, có thể xuất hiện spikes do diffused normal của vài vertex còn noise. Áp dụng Taubin $(\lambda = 0.40, \mu = -0.44)$ ba cặp:

```
for pair in 3:
  uniform_laplacian_step(lambda = +0.40)   // shrink
  uniform_laplacian_step(mu     = -0.44)   // inflate
```

Transfer function $H(k) = (1 - 0.40 \, k)(1 + 0.44 \, k)$ cho $k \in [0, k_{\max}]$ với $k$ là eigenvalue của Laplacian. $H(0) = 1$ (giữ DC), $H$ nhỏ ở $k$ lớn (khử high-freq spikes), nhưng $\int_0^{k_c} H > \int_0^{k_c} 1$ cho $k_c$ nhỏ, tức **no net shrinkage** cho low-frequency shape (mái vòm).

### 4.8. Step 7 — Patch Merging

**Input:** mesh gốc $\mathcal{M}$, patch bent, `HoleBoundary` gốc.
**Output:** $\mathcal{M}$ đã tích hợp patch.

Quy trình:

1. **Boundary vertex re-indexing:** patch boundary vertex được remap về original index trong $\mathcal{M}$. Không tạo vertex mới cho boundary → đảm bảo no duplicate, topology seamless.
2. **Interior vertex addition:** `AddVertices` cấp phát vertex mới trong $\mathcal{M}$. Color được set bằng average color của boundary vertices (tránh miếng vá trắng nổi bật).
3. **Face addition:** mỗi face trong patch được thêm vào $\mathcal{M}$. Face color set từ average color của faces kề với boundary — visual continuity.
4. **Topology update:** gọi `UpdateTopology<CMeshO>::FaceFace(m)` để rebuild FF pointers. Gọi `UpdateNormal` để recompute face và vertex normals. Gọi `UpdateBounding::Box` cho viewport.

Sau Step 7, $\mathcal{M}$ là watertight ở vùng lấp (assuming original mesh watertight ngoài lỗ), và có thể được export lại qua `File > Export Mesh As`.

---

## Chapter 5 — Implementation

### 5.1. Plugin Architecture

MeshLab sử dụng kiến trúc plugin dựa trên **Qt MOC (Meta-Object Compiler)** và **dynamic DLL loading**. Plugin được cài đặt bằng cách:

1. **Kế thừa `FilterPlugin`**: class `FilterNFDHoleFillPlugin` override các virtual methods `pluginName()`, `filterName()`, `filterInfo()`, `initParameterList()`, `applyFilter()`.

2. **Khai báo filter ID**: enum `FP_NFD_HOLEFILL` trong header phân biệt các filter (nếu plugin có nhiều filter).

3. **Parameter metadata**: `initParameterList` khai báo tên, type, default, description của mỗi user parameter. MeshLab tự động tạo UI dialog tương ứng.

4. **MOC integration**: macro `Q_OBJECT` và `Q_PLUGIN_METADATA` trong class declaration cho phép Qt runtime discovery.

5. **CMake target**: `CMakeLists.txt` của plugin build target `filter_nfd_holefill` dạng `MODULE` library, link với `meshlab-common`, `vcg`, `Qt5::Core`.

Output DLL được copy vào `build2/src/distrib/plugins/`. MeshLab scan directory này khi khởi động và load mọi plugin thỏa metadata.

### 5.2. VCGlib Usage

**CMeshO** là mesh type tiêu chuẩn của MeshLab: template `TriMesh` với vertex, face có Optional Components Framework (OCF) cho các optional attributes (normal, color, quality, flags).

Các API VCGlib key sử dụng:

- `vcg::tri::UpdateTopology`: build FF, VF adjacency.
- `vcg::tri::UpdateFlags`: mark borders, boundary vertices.
- `vcg::tri::UpdateNormal`: compute per-vertex, per-face normals.
- `vcg::face::IsBorder`: predicate cached.
- `vcg::face::VFIterator`: duyệt face quanh vertex.
- `vcg::tri::Index(m, v)`: convert pointer về index.
- `vcg::tri::Allocator::AddVertices/AddFaces`: grow mesh dynamically.

### 5.3. Eigen Integration

**Eigen** là template-based linear algebra library header-only. Project dùng:

- `Eigen::SparseMatrix<double>` với storage `ColMajor` (default).
- `Eigen::Triplet<double>` cho accumulate entries trước khi `setFromTriplets`.
- `Eigen::SimplicialLDLT<SpMat>` cho Cholesky-like factorization.
- `Eigen::MatrixXd` cho dense vector of normals (kích thước $B \times 3$).

Lưu ý performance: `solver.solve()` trả về Eigen expression template, assign vào `MatrixXd` sẽ trigger evaluation một lần duy nhất — tránh double evaluation.

### 5.4. Parameter Summary

| Parameter | Type | Default | Range | Step Affected |
|---|---|---:|---|---|
| `MaxHoleSize` | int | 100 | > 3 | 1 |
| `DiffusionIterations` | int | 50 | 1–500 | 4 |
| `DiffusionLambda` | float | 0.5 | 0.1–1.0 | 4 |
| `SmoothingIterations` | int | 3 | 0–20 | 5 |
| `RefinementFactor` | float | 1.0 | 0.1+ | 3 |
| `CurvatureStrength` | float | 1.0 | 0+ | 6 |
| `UseDelaunayFlipping` | bool | true | — | 3 |

### 5.5. Build System

- **Compiler:** MSVC 19.41+ (VS 2022 Community).
- **Generator:** Ninja (đi kèm VS).
- **Config:** Release for production; Debug khi development.
- **Dependencies:** Qt 5.15.2 msvc2019_64, VCGlib sub-module, Eigen header-only.

Build workflow:

```bash
cd meshlab-src
mkdir build2 && cd build2
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build .                              # full build (once)
cmake --build . --target filter_nfd_holefill # incremental rebuild
```

Script `build_nfd.bat` tự động hóa: gọi `vcvarsall.bat x64`, chạy target `filter_nfd_holefill`. Chạy từ build directory đảm bảo ABI compatibility — **không** copy DLL sang installation MeshLab khác.

### 5.6. Code Organization

```
plugin/
├── filter_nfd_holefill.h       (70 lines, class declaration)
├── filter_nfd_holefill.cpp     (~1245 lines, full algorithm)
└── CMakeLists.txt              (build config)
```

File `.cpp` được tổ chức theo pipeline:

- Lines 1–170: plugin boilerplate (Qt macros, filter registration, parameter list).
- Lines 170–320: main `applyFilter` driver.
- Lines 320–395: Step 1 (`detectHoles`).
- Lines 395–460: Step 2 (`computeBoundaryInfo`).
- Lines 460–850: Step 3 (`triangulatePatch` — phần lớn nhất do ear clipping + Delaunay + refine).
- Lines 850–990: Step 4 (`diffuseNormalField`).
- Lines 990–1145: Step 6 (`displaceVertices`, đã bao gồm Taubin).
- Lines 1145–1175: Step 5 (`smoothPatch`).
- Lines 1175–end: Step 7 (`mergePatchIntoMesh`).

Mọi hàm đều static hoặc member; không có state toàn cục → thread-safe trên per-mesh basis (MeshLab chưa parallelize multiple-mesh processing, nhưng plugin sẵn sàng).

---

## Chapter 6 — Experimental Results

### 6.1. Test Dataset

Tập test gồm 7 mô hình được sinh hoặc import, mỗi test có cặp `*_gt.ply` (ground truth watertight) và `*_hole.ply` (cùng mesh với một hoặc nhiều face bị xóa tạo lỗ):

| Model | #Verts (GT) | #Faces (GT) | Hole(s) | Description |
|---|---:|---:|---:|---|
| sphere_small | 2 562 | 5 120 | 1 | Icosphere subdivision 4, small hole |
| sphere_large | 2 562 | 5 120 | 1 | Same sphere, larger hole |
| sphere_two | 2 562 | 5 120 | 2 | Two separate holes |
| cylinder_side | ~4 000 | ~8 000 | 1 | Hole on side of cylinder |
| torus | ~4 000 | ~8 000 | 1 | Hole on torus, non-trivial curvature |
| bunny | 35 947 | 69 451 | 6 | Stanford Bunny with multiple holes |
| cow | ~3 000 | ~6 000 | 1 | Watertight cow with cutout |

Dataset được generate bằng script `data/generate_test_meshes.py` sử dụng trimesh và numpy.

### 6.2. Evaluation Metric: Symmetric Hausdorff Distance

Hausdorff distance giữa hai tập compact $A, B \subset \mathbb{R}^3$:

$$
d_H(A, B) = \max\left(\sup_{a \in A} \inf_{b \in B} \|a - b\|, \sup_{b \in B} \inf_{a \in A} \|a - b\|\right)
$$

Trên mesh, tính qua sampling: lấy $N$ điểm uniform sample trên $A$, với mỗi điểm tìm closest point trên $B$, lấy max/mean. MeshLab cung cấp filter `Filters > Sampling > Hausdorff Distance` thực hiện chính xác điều này, cho cả forward ($A \to B$) và reverse ($B \to A$).

**Interpretations:**

- **Forward (filled → GT):** đo *"patch có trên GT không?"* — sai số bề mặt của patch.
- **Reverse (GT → filled):** đo *"GT có được phủ bởi filled không?"* — độ phủ của patch.
- **Symmetric max:** $\max(\text{fwd}_{\max}, \text{rev}_{\max})$.
- **RMS:** căn bậc hai của mean squared distances — ổn định hơn max với outliers.
- **% BBox:** chuẩn hóa max / bounding-box diagonal, cho cross-model comparison.

### 6.3. Quantitative Results

| Model | Sym. Hausd. | % BBox | RMS (fwd) | RMS (rev) | Ghi chú |
|---|---:|---:|---:|---:|---|
| sphere_small | 4.3 × 10⁻³ | **0.12 %** | 2.4 × 10⁻⁴ | 3.1 × 10⁻⁴ | Excellent |
| sphere_large | 2.1 × 10⁻² | 0.59 % | 2.1 × 10⁻³ | 2.5 × 10⁻³ | ~5× hơn do lỗ lớn |
| torus | 2.4 × 10⁻² | 0.34 % | 5.6 × 10⁻⁵ | 1.8 × 10⁻³ | Reverse-dominated |
| cow | 3.3 × 10⁻¹ | 2.61 % | 1.4 × 10⁻³ | 3.3 × 10⁻¹ | Patch hụt vùng phủ |
| bunny | 8.8 × 10⁻³ | 3.50 % | 4.5 × 10⁻⁴ | 8.8 × 10⁻³ | Max spike tại 1 lỗ sắc |

### 6.4. Analysis

#### 6.4.1. Sphere Family

Sphere test cho kết quả tốt nhất vì spherical-cap model hoàn hảo với geometry này. Sai số tăng theo kích thước lỗ như dự đoán: lỗ lớn → boundary normal deviation $\theta$ lớn hơn → biên độ displacement lớn hơn → sai số hình học tuyệt đối lớn hơn, nhưng tỉ lệ % BBox vẫn $< 1$%.

#### 6.4.2. Torus: Reverse-Dominated Error

Torus có forward RMS rất thấp ($5.6 \times 10^{-5}$) nhưng reverse cao ($1.8 \times 10^{-3}$). Interpretation: patch **nằm trên GT** (forward small) nhưng **không phủ hết vùng lỗ** (reverse large). Khắc phục: tăng `RefinementFactor` để patch dày hơn gần boundary.

#### 6.4.3. Bunny: Multiple Holes with Shape Variation

Bunny có 6 lỗ, trong đó 5 lỗ được lấp tốt (sai số tương đương sphere_small) nhưng 1 lỗ sắc gây max spike — vùng này boundary normals lệch rất mạnh, `CurvatureStrength = 1.0` overshoot. Thực nghiệm cho thấy giảm xuống 0.7 loại bỏ spike.

#### 6.4.4. Cow: Large Hole Challenge

Cow có lỗ tương đối lớn so với mesh size (chu vi ~100 cạnh). Reverse dominate: patch **không đủ rộng** để phủ GT. Giảm `RefinementFactor = 0.6` và tăng `DiffusionIterations = 100` cải thiện đáng kể.

### 6.5. Qualitative Results

Với mỗi test, so sánh visual:

- **Ảnh before:** mesh với lỗ, thường có "lỗ đen" lộ mặt trong khi render two-sided.
- **Ảnh after:** patch cong tự nhiên, đồng bộ color với vùng xung quanh nếu mesh gốc có color per-vertex.
- **Delaunay on/off comparison:** trên slides `delaunay_off.png` vs `delaunay_on.png`, sự khác biệt rõ ràng — off-version có slivers rõ rệt, on-version regular.

### 6.6. Comparison with MeshLab Built-in Filters

Chạy cùng input qua `Filters > Remeshing > Close Holes` (MeshLab built-in):

| Model | NFD Hausdorff | Close Holes Hausdorff | Improvement |
|---|---:|---:|---:|
| sphere_small | 4.3 × 10⁻³ | 1.1 × 10⁻² | **2.5×** |
| sphere_large | 2.1 × 10⁻² | 7.8 × 10⁻² | 3.7× |
| torus | 2.4 × 10⁻² | 4.2 × 10⁻² | 1.75× |
| bunny | 8.8 × 10⁻³ | 1.5 × 10⁻² | 1.7× |

NFD consistently better, đặc biệt trên lỗ lớn (close holes chỉ tạo flat cap, không bend).

### 6.7. Performance

Benchmark trên Intel i7-12700H, single-threaded:

| Model | Hole Size | Total Time | Dominated By |
|---|---:|---:|---|
| sphere_small | 30 edges | 45 ms | Triangulation |
| sphere_large | 80 edges | 210 ms | Diffusion (factorize) |
| bunny (6 holes) | ~40 each | 890 ms | Total over 6 holes |

Diffusion (factorize + 50 solves) chiếm 40–60% total time trên lỗ vừa. Triangulation chiếm 20–30%. Dijkstra $\lesssim$ 10%. Các bước khác marginal.

---

## Chapter 7 — Discussion

### 7.1. Strengths

1. **Geometry-aware patching.** Không như close-holes filler, patches phản ánh curvature xung quanh.
2. **Density invariance.** Cotangent Laplacian và spherical-cap model không phụ thuộc mật độ mesh — re-sample không thay đổi kết quả đáng kể.
3. **Unconditional stability.** Implicit Euler cho phép chọn $\lambda$ lớn mà không unstable.
4. **Computational efficiency.** Factorize one-time, solve many giúp diffusion nhanh sau iteration 1.
5. **Robustness.** Nhiều safety layer (clamp negative cot, NaN detection, hard caps) xử lý mesh thực tế không lý tưởng.
6. **Production integration.** Plugin tích hợp native trong MeshLab, UI tham số tiêu chuẩn Qt, tương thích với pipeline xử lý hàng loạt qua MeshLab scripting.

### 7.2. Limitations

1. **Genus-0 assumption within patch.** Dò lỗ dùng single-loop walking; không xử lý lỗ topology phức tạp (nested holes, lỗ chia sẻ vertex giữa hai lỗ riêng biệt).

2. **No texture recovery.** Chỉ fill geometry + vertex color average; texture UV không được nội suy. Công trình gốc của Verdera có tái tạo texture qua inpainting — mở rộng tương lai.

3. **Large-hole sensitivity.** Với lỗ rất lớn (> 50% mesh), Euler frame không đủ ổn định (boundary normals span wide range), cần approach khác như curvature-aware deformation.

4. **Sharp features.** Patches đều mượt; không preserve sharp crease/corner nếu chúng gốc xuyên qua lỗ. Feature-preserving extension cần detect feature edge gần boundary và constrain diffusion tương ứng.

5. **No convergence guarantee.** 50 iterations là heuristic; không check tolerance-based stopping criterion. Với mesh có condition number lớn, có thể cần nhiều iterations hơn.

6. **Heuristic parameters.** `CurvatureStrength`, `RefinementFactor` cần tuning thủ công trên mesh khác nhau. Auto-tuning từ mesh statistics là future work.

### 7.3. Failure Modes

**Mode 1 — Wildly varying boundary normals:** nếu vertex biên có normals noisy cực đoan (e.g. mesh scan quality kém), $\theta$ estimate bias → height overshoot. Mitigation: pre-smooth boundary normals, hoặc dùng median thay vì mean.

**Mode 2 — Non-planar hole boundary far from spherical:** saddle-shaped hole boundary vi phạm spherical-cap assumption; patch có thể bend sai hướng tại một số vùng. Mitigation: localized cap models per boundary segment.

**Mode 3 — Disconnected interior:** sau triangulation, nếu tồn tại vertex không connected (floating island — hiếm nhưng có thể với degenerate input), Dijkstra để `dist = ∞` và vertex không displaced. Hệ quả: patch có vertex phẳng giữa mái vòm. Mitigation: post-check connectivity sau triangulation.

**Mode 4 — Non-manifold input:** Project giả thiết 2-manifold input. Non-manifold edge (> 2 face) có thể gây misdetect boundary. Mitigation: pre-filter qua MeshLab's `Filters > Cleaning > Non-Manifold` trước khi chạy NFD.

### 7.4. Comparison with Alternatives

| Method | Bend Curvature | Speed | Topology Flexibility | Smoothness |
|---|:---:|:---:|:---:|:---:|
| Close Holes (flat) | ✗ | Fast | Good | Low |
| Advancing Front | Partial | Medium | Good | Medium |
| Poisson Reconstruction | ✓ | Slow | Excellent | High |
| Thin-plate (C²) | ✓ | Slow | Limited | Very high |
| **NFD (this work)** | ✓ | Medium | Genus-0 only | Medium-high |

NFD positions as middle-ground: cao hơn flat/ear-clip, rẻ hơn Poisson/thin-plate, suitable cho interactive editing với single-hole focus.

---

## Chapter 8 — Conclusion and Future Work

### 8.1. Conclusion

Báo cáo trình bày thiết kế và triển khai của một MeshLab plugin hole-filling dựa trên Normal Field Diffusion. Đóng góp chính gồm: (i) pipeline bảy bước tích hợp ear clipping cải tiến, cotangent Laplacian diffusion với implicit Euler, và spherical-cap displacement; (ii) lựa chọn thiết kế không hiển nhiên — profile $\sqrt{2t - t^2}$ thay vì parabol, mean angle thay vì max angle, Taubin ở phase cuối — mang lại robustness và chất lượng; (iii) đánh giá quantitative trên sáu mô hình với Symmetric Hausdorff cho sai số tốt nhất 0.12% BBox, consistent improvement 1.7–3.7× so với MeshLab built-in Close Holes filter.

Phương pháp minh họa rằng PDE-based geometry processing, vốn kinh điển trong continuous differential geometry, có thể được triển khai hiệu quả trên triangle mesh với cotangent Laplacian làm operator xấp xỉ và các sparse solver hiện đại (Eigen SimplicialLDLT) đảm bảo tốc độ thực tế. Pipeline được thiết kế modular và production-ready, sẵn sàng deploy cho end users qua MeshLab UI.

### 8.2. Future Work

**Short-term improvements:**

- **Adaptive parameter selection:** auto-tune `CurvatureStrength` từ boundary normal statistics (variance, quantile).
- **Convergence-based stopping:** replace fixed iteration count bằng $\|\mathbf{n}^{t+1} - \mathbf{n}^t\| < \tau$ check.
- **Feature preservation:** detect crease edges near boundary, add anisotropic diffusion constraint.

**Medium-term extensions:**

- **Texture inpainting:** mở rộng diffusion cho texture coordinates và color field, theo tinh thần công trình gốc Verdera et al.
- **Topology-robust detection:** xử lý lỗ nested, lỗ chia sẻ vertex, lỗ với self-intersection (common trong mesh photogrammetry).
- **Localized spherical-cap:** thay global scalar height bằng per-vertex height suy ra từ local curvature, handling saddle-shaped boundaries.

**Long-term research directions:**

- **Neural hole filling:** so sánh NFD với learning-based approaches (e.g. 3D-EPN, PCN, AtlasNet) — định lượng trade-off giữa geometric-prior methods và data-driven.
- **Volumetric extension:** generalize pipeline cho volumetric mesh (tet-mesh) với lỗ 2D trên surface shell — bài toán non-trivial trong simulation preprocessing.
- **GPU parallelization:** solver GPU (e.g. cuSolver) cho xử lý real-time mesh stream từ Kinect/RealSense.

### 8.3. Academic Reflection

Project thể hiện tương tác giữa ba lĩnh vực: **discrete differential geometry** (cotangent Laplacian, mean curvature), **PDE numerical analysis** (implicit Euler, Cholesky factorization), và **computer graphics engineering** (plugin architecture, VCGlib, Qt). Mỗi lĩnh vực đóng góp kỹ thuật thiết yếu — không lĩnh vực nào đủ một mình. Đây là trải nghiệm đại diện cho research trong Advanced Computer Graphics: vấn đề practical (mesh repair) yêu cầu nền tảng mathematical (Laplace-Beltrami) và software engineering (plugin integration) bổ sung cho nhau.

---

## References

1. Barequet, G., & Sharir, M. (1995). Filling gaps in the boundary of a polyhedron. *Computer Aided Geometric Design*, 12(2), 207–229.

2. Botsch, M., & Kobbelt, L. (2004). An intuitive framework for real-time freeform modeling. *ACM SIGGRAPH*, 23(3), 630–634.

3. Desbrun, M., Meyer, M., Schröder, P., & Barr, A. H. (1999). Implicit fairing of irregular meshes using diffusion and curvature flow. *Proceedings of SIGGRAPH 1999*, 317–324.

4. Held, M. (2001). FIST: Fast industrial-strength triangulation of polygons. *Algorithmica*, 30(4), 563–596.

5. Jun, Y. (2005). A piecewise hole filling algorithm in reverse engineering. *Computer-Aided Design*, 37(2), 263–270.

6. Kazhdan, M., Bolitho, M., & Hoppe, H. (2006). Poisson surface reconstruction. *Symposium on Geometry Processing*, 61–70.

7. Kazhdan, M., & Hoppe, H. (2013). Screened Poisson surface reconstruction. *ACM Transactions on Graphics*, 32(3), 29.

8. Liepa, P. (2003). Filling holes in meshes. *Symposium on Geometry Processing*, 200–205.

9. Meisters, G. H. (1975). Polygons have ears. *American Mathematical Monthly*, 82(6), 648–651.

10. Meyer, M., Desbrun, M., Schröder, P., & Barr, A. H. (2003). Discrete differential-geometry operators for triangulated 2-manifolds. *Visualization and Mathematics III*, Springer, 35–57.

11. Nealen, A., Igarashi, T., Sorkine, O., & Alexa, M. (2005). Laplacian mesh optimization. *Graphite '06*, 381–389.

12. Pinkall, U., & Polthier, K. (1993). Computing discrete minimal surfaces and their conjugates. *Experimental Mathematics*, 2(1), 15–36.

13. Sharp, N., & Crane, K. (2020). A Laplacian for nonmanifold triangle meshes. *Symposium on Geometry Processing*, 39(5).

14. Taubin, G. (1995). A signal processing approach to fair surface design. *Proceedings of SIGGRAPH 1995*, 351–358.

15. Verdera, J., Caselles, V., Bertalmío, M., & Sapiro, G. (2003). Inpainting surface holes. *International Conference on Image Processing*, 2, 903–906.

16. Wang, J., & Oliveira, M. M. (2007). Filling holes on locally smooth surfaces reconstructed from point clouds. *Image and Vision Computing*, 25(1), 103–113.

17. Zhao, W., Gao, S., & Lin, H. (2007). A robust hole-filling algorithm for triangular mesh. *The Visual Computer*, 23(12), 987–997.

---

## Appendix A — Parameter Tuning Guide

Bảng tham chiếu cho common scenarios:

| Scenario | MaxHoleSize | DiffusionIters | CurvatureStrength | RefinementFactor |
|---|---:|---:|---:|---:|
| Default (unknown mesh) | 100 | 50 | 1.0 | 1.0 |
| Small hole, smooth surface | 100 | 30 | 1.0 | 1.0 |
| Large hole, sphere-like | 300 | 100 | 1.0 | 0.7 |
| Bunny / irregular mesh | 150 | 50 | 0.7 | 1.0 |
| Very dense mesh, speed priority | 100 | 20 | 1.0 | 2.0 |
| Flat surface hole | 100 | 50 | 0.0 | 1.0 |
| Teaching demo (before/after) | 100 | 50 | 1.0 | 1.0 + `UseDelaunayFlipping=off` |

## Appendix B — Symbol Reference

| Symbol | Meaning |
|---|---|
| $\mathcal{M} = (V, F)$ | Triangle mesh (vertices, faces) |
| $\partial \Omega$ | Boundary of hole domain |
| $\mathbf{n}_i$ | Unit normal at vertex $v_i$ |
| $L_{\text{cot}}$ | Cotangent Laplacian matrix |
| $w_{ij}$ | Cotangent weight of edge $(v_i, v_j)$ |
| $\alpha, \beta$ | Opposite angles across edge |
| $H$ | Mean curvature |
| $\lambda, \mu$ | Taubin smoothing coefficients |
| $r, \theta$ | Hole radius, deviation angle |
| $h$ | Spherical-cap height |
| $w(t)$ | Displacement weighting profile |
| $t_i$ | Normalized geodesic distance |
