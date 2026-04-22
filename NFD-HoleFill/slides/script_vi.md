# Kịch bản thuyết trình (Tiếng Việt) — ~10 phút

Tốc độ mục tiêu: ~150 từ/phút. Nói tự nhiên, không đọc nguyên slide — slide
là điểm tựa. Thời lượng dự kiến trong ngoặc vuông đầu mỗi phần.

---

## Slide tiêu đề  [≈ 20 giây]

Chào thầy và các bạn. Em tên là Trương Trí Dũng, MSSV MITIU25208. Hôm nay
em xin trình bày đồ án môn IT516 của mình: **Lấp lỗ trên lưới 3D dựa trên
khuếch tán trường pháp tuyến** — Normal Field Diffusion-Guided Hole
Filling. Bài nói khoảng 10 phút, và em sẽ dành thời gian cho Q&A ở cuối.

---

## Slide 1 — Đặt vấn đề  [≈ 45 giây]

Lấp lỗ là một bài toán cơ bản trong xử lý lưới 3D. Khi chúng ta quét một
vật thể thực, lỗ luôn xuất hiện — do occlusion, do sensor noise, hoặc do
bề mặt phản xạ mà máy quét không nhìn được. Các phương pháp kinh điển như
Liepa 2003, advancing front, hay volumetric diffusion đều có thể đóng
được lỗ, nhưng kết quả thường bị phẳng, hoặc bị làm mượt quá mức, và
không **thật sự bám theo** độ cong xung quanh lỗ. Nên câu hỏi đặt ra là:
có cách nào lấp lỗ mà vẫn **tôn trọng hình học** của vùng lân cận không?

---

## Slide 2 — Ý tưởng  [≈ 45 giây]

Câu trả lời của đồ án là: được, nếu ta lan truyền đúng thông tin. Thay vì
chỉ khuếch tán vị trí — vốn là cách các phương pháp dựa trên Laplacian
đang làm — chúng ta lan truyền **vector pháp tuyến** từ biên vào trong
lỗ. Trực giác là: pháp tuyến mang hướng của bề mặt tại điểm đó; nếu ta
nội suy các pháp tuyến biên một cách trơn tru trên toàn bộ patch, ta sẽ
khôi phục được xấp xỉ hướng của mặt đã mất. Sau đó ta dịch chuyển các
đỉnh của patch dọc theo các pháp tuyến đã khuếch tán đó để thật sự *dựng*
bề mặt. Cách tiếp cận này dùng thông tin hình học vi phân — pháp tuyến
và độ cong — chứ không chỉ dùng smoothing vị trí.

---

## Slide 3 — Pipeline 6 bước  [≈ 40 giây]

Đây là toàn bộ pipeline. Cho một lưới có lỗ, bước 1 là **phát hiện lỗ**
bằng cách tìm các vòng cạnh biên. Bước 2 tạo triangulation ban đầu bằng
ear clipping cộng với chia centroid. Bước 3 tính pháp tuyến và độ cong
trung bình tại các đỉnh biên. Bước 4 — cái được highlight, trái tim của
phương pháp — khuếch tán pháp tuyến vào trong lỗ bằng phương trình
nhiệt. Bước 5 dịch chuyển các đỉnh nội tại dọc theo các pháp tuyến đã
khuếch tán. Và bước 6 chạy smoothing nhẹ. Tiếp theo em sẽ đi sâu vào các
bước quan trọng nhất.

---

## Slide 4 — Phân tích biên  [≈ 40 giây]

Tại mỗi đỉnh biên, chúng ta lấy ra hai đại lượng. Thứ nhất là **pháp
tuyến đỉnh**, tính bằng trung bình có trọng số diện tích của các pháp
tuyến mặt lân cận. Thứ hai là **độ cong trung bình** thông qua cotangent
Laplacian — công thức kinh điển với trọng số `cot α + cot β` trên mỗi
cạnh. Hai đại lượng này cho biết bề mặt đang hướng về đâu và đang cong
nhanh như thế nào tại biên. Chúng sẽ trở thành **điều kiện biên
Dirichlet** cho phương trình khuếch tán ở bước sau.

---

## Slide 5 — Khuếch tán trường pháp tuyến (Core)  [≈ 70 giây]

Đây là phần lõi của phương pháp. Ta coi patch như một lưới nhỏ và giải
**phương trình nhiệt** trên nó: đạo hàm riêng của pháp tuyến theo thời
gian bằng lambda nhân với Laplacian của pháp tuyến. Pháp tuyến biên được
giữ cố định — đó là điều kiện Dirichlet — và ta rời rạc hoá bằng
**implicit Euler**. Kết quả là một hệ tuyến tính: ma trận đơn vị cộng
lambda nhân cotangent Laplacian, nhân trường pháp tuyến mới, bằng trường
cũ cộng một term đóng góp từ biên. Ma trận sparse và đối xứng xác định
dương, nên ta assemble một lần và phân rã bằng **SimplicialLDLT của
Eigen**, rồi tái sử dụng phân rã đó cho mọi iteration. Kết quả là một
trường pháp tuyến mượt, blend các hướng biên trên toàn bộ patch.

---

## Slide 6 — Dịch chuyển theo độ cong  [≈ 55 giây]

Khi mỗi đỉnh nội tại đã có pháp tuyến, ta di chuyển nó dọc pháp tuyến
một lượng `d`. Ta dùng **profile spherical cap** — chính là độ cao giải
tích của một chỏm cầu nhỏ trên một mặt cầu. Hệ số scale được tính từ
bán kính trung bình của biên và góc lan toả của các pháp tuyến biên, nên
nó tự điều chỉnh. Profile phụ thuộc vào `t`, là **khoảng cách geodesic**
từ biên đã chuẩn hoá về [0, 1] — tính bằng Dijkstra. Hiệu quả: patch
phồng ra mượt từ biên và đạt đỉnh ở giữa, đúng kiểu một chỏm cầu nối
tiếp độ cong xung quanh.

---

## Slide 7 — Delaunay edge flipping  [≈ 50 giây]

Ear clipping và chia centroid chỉ cho ta triangulation *hợp lệ*, chứ
chưa *tối ưu* — ta sẽ có các tam giác mảnh, gọi là sliver, tại các đỉnh
junction. Cách xử lý kinh điển đã được dạy ở lớp là **flip cạnh theo
tiêu chí max-min-angle**: với mỗi cạnh trong chung bởi hai tam giác, ta
flip đường chéo nếu góc nhỏ nhất của hai tam giác **tăng lên**. Chúng ta
chạy hai pass — một sau ear clipping, một sau chia centroid. Với NFD
điều này quan trọng, vì cotangent weight blow up trên sliver; loại bỏ
sliver giữ cho Laplacian well-conditioned. Hình bên trái là triangulation
raw còn sliver, hình bên phải là sau khi Delaunay edge-flip đã chạy.

---

## Slide 8 — Post-processing  [≈ 30 giây]

Sau khi dịch chuyển, ta chạy hai pass smoothing ngắn, cả hai đều giữ cố
định các đỉnh biên. Đầu tiên là **constrained Laplacian** để phân phối
lại đỉnh nội tại đều hơn. Thứ hai là **Taubin lambda-mu smoothing** —
luân phiên shrink và inflate — loại bỏ các gai nhọn per-vertex mà không
làm xẹp cái dome tổng thể. Kết quả là một patch sạch, tam giác đều.

---

## Slide 9 — Implementation và tham số  [≈ 55 giây]

Plugin viết bằng C++14, dùng VCG Library cho các thao tác lưới, và
Eigen 3 cho solver sparse. Tích hợp vào MeshLab qua CMake, nằm ở
`Filters > Remeshing > NFD Hole Filling`. Bảng liệt kê 7 tham số người
dùng. Hai cái hay được chỉnh nhất là **CurvatureStrength** — giảm xuống
nếu patch phồng quá — và **RefinementFactor** — giảm xuống nếu muốn
patch dày đặc hơn hoặc còn sliver. Các tham số còn lại có thể giữ
default.

---

## Slide 10 — Kết quả trực quan  [≈ 35 giây]

Đây là một cặp before-and-after điển hình. Bên trái, lưới đầu vào còn
lỗ trên bề mặt. Bên phải, chính lưới đó sau khi chạy NFD với tham số
mặc định. Để ý rằng patch không chỉ làm phẳng chỗ lỗ — nó bám theo độ
cong xung quanh và blend mượt với biên.

---

## Slide 11 — Đánh giá định lượng  [≈ 60 giây]

Về đánh giá số, em dùng luôn **filter Hausdorff Distance có sẵn trong
MeshLab**, chạy cả hai chiều — filled so với ground truth, và ngược lại.
Điểm chính nằm ở cột RMS: với mọi model đã test, RMS chiều forward đều
dưới 0.2 phần trăm bbox diagonal. Nghĩa là các đỉnh của patch về cơ bản
nằm trên mặt thật. Hausdorff max bị chi phối bởi các peak tại một điểm —
với bunny là đỉnh tai, với cow là vùng hạn chế bởi mật độ — nhưng mean
và RMS vẫn rất nhỏ.

---

## Slide 12 — Kết luận  [≈ 40 giây]

Tóm lại: NFD tạo ra các patch nhất quán về mặt hình học với forward RMS
dưới một phần trăm trên mọi model đã test, và tích hợp gọn vào MeshLab.
So với proposal gốc em đã bổ sung: Delaunay edge-flipping để cải thiện
chất lượng tam giác, profile dịch chuyển spherical-cap với scale tự
calibrate, và Taubin smoothing để khử gai. Hướng phát triển tiếp: scale
per-vertex từ độ cong trung bình cục bộ để patch thích ứng được với
vùng không phải cầu, và bảo toàn sharp feature cho input dạng CAD.

---

## Slide Thank You  [≈ 10 giây]

Bài nói của em đến đây là hết. Em cảm ơn thầy và các bạn đã lắng nghe,
và em sẵn sàng trả lời câu hỏi.
