/**
 * i18n.js - All translatable strings.
 *
 * To add/edit a translation: find the key and change the vi/en value.
 * To add a new language: add a third property (e.g. "ja") to each entry.
 *
 * Keys used in two places:
 *   1. data-i18n="key" attributes in HTML (header, footer, toc)
 *   2. content.js section definitions (titles, paragraphs, list items, etc.)
 */
const I18N = {
  // ---- Header & Footer ----
  title:    { vi: 'Ôn Tập Giữa Kì - IT516', en: 'Midterm Review - IT516' },
  examInfo: { vi: '90 phút · 4 câu hỏi lớn · Theory 30đ + Thực hành 70đ · 1 mặt A4 viết tay',
              en: '90 min · 4 big questions · Theory 30pts + Practice 70pts · 1 handwritten A4 sheet' },
  toc:      { vi: 'Mục lục', en: 'Contents' },
  footer:   { vi: 'Ôn Tập Giữa Kì 2026', en: 'Midterm Review 2026' },

  // ---- Section titles (also used for TOC) ----
  s1_title:  { vi: '1. Computer Graphics là gì?', en: '1. What is Computer Graphics?' },
  s2_title:  { vi: '2. Mathematical Background',  en: '2. Mathematical Background' },
  s3_title:  { vi: '3. Geometric Transformations', en: '3. Geometric Transformations' },
  s4_title:  { vi: '4. Image Representation & Processing', en: '4. Image Representation & Processing' },
  s5_title:  { vi: '5. Curves & Surfaces (Bezier)', en: '5. Curves & Surfaces (Bezier)' },
  s6_title:  { vi: '6. Simplification, Triangulation, Hole Filling', en: '6. Simplification, Triangulation, Hole Filling' },
  s7_title:  { vi: '7. OpenGL Overview',           en: '7. OpenGL Overview' },
  s8_title:  { vi: '8. Delaunay Triangulation — Python', en: '8. Delaunay Triangulation — Python' },
  s9_title:  { vi: '9. Python OpenGL Programming', en: '9. Python OpenGL Programming' },
  s10_title: { vi: '10. Ghi nhớ cho tờ A4',        en: '10. A4 Cheat Sheet Tips' },

  // ---- Section 1 ----
  s1_def:        { vi: 'Computer Graphics là lĩnh vực liên quan đến việc <em>tạo, thao tác, lưu trữ</em> các đối tượng hình học (modelling) và hình ảnh của chúng (rendering), hiển thị trên màn hình hoặc thiết bị phần cứng.',
                   en: 'Computer Graphics is the field concerned with <em>creating, manipulating, and storing</em> geometric objects (modelling) and their images (rendering), displaying them on screens or hardware devices.' },
  s1_areas:      { vi: 'Các lĩnh vực chính', en: 'Key Areas' },
  s1_apps:       { vi: 'Ứng dụng',           en: 'Applications' },
  s1_gpu:        { vi: 'cầu nối giữa mainboard và thiết bị hiển thị, có buffer memory',
                   en: 'bridge between mainboard and display, contains buffer memory' },

  // ---- Section 2 ----
  s2_scalars:    { vi: 'Thành viên của tập hợp, có phép cộng và nhân. Không có tính chất hình học.',
                   en: 'Members of sets with addition and multiplication. No geometric properties.' },
  s2_vectors:    { vi: 'Có <strong>hướng</strong> và <strong>độ lớn</strong>. VD: lực, vận tốc.',
                   en: 'Have <strong>direction</strong> and <strong>magnitude</strong>. E.g. force, velocity.' },
  s2_points:     { vi: '<strong>Points</strong> gắn với vị trí trong không gian. Point và Vector là 2 kiểu khác nhau. Translation của point = point mới, translation của direction = cùng direction.',
                   en: '<strong>Points</strong> are locations in space. Points and Vectors are different types. Translation of a point = new point, translation of a direction = same direction.' },
  s2_add:        { vi: 'Cộng:', en: 'Addition:' },
  s2_smul:       { vi: 'Nhân scalar:', en: 'Scalar mult:' },
  s2_inv:        { vi: 'Nghịch đảo:', en: 'Inverse:' },
  s2_inv_desc:   { vi: 'cùng độ lớn, ngược hướng', en: 'same magnitude, opposite direction' },
  s2_norm:       { vi: 'độ dài', en: 'length' },
  s2_dot:        { vi: 'Dot Product (Tích vô hướng)', en: 'Dot Product' },
  s2_dot_orth:   { vi: 'Vuông góc khi U · V = 0', en: 'Orthogonal when U · V = 0' },
  s2_dot_use:    { vi: 'Tính góc, phép chiếu',     en: 'Compute angle, projection' },
  s2_cross:      { vi: 'Cross Product (Tích có hướng)', en: 'Cross Product' },
  s2_cross_perp: { vi: 'Vuông góc với cả U và V',  en: 'Perpendicular to both U and V' },
  s2_cross_area: { vi: 'diện tích hình bình hành',  en: 'parallelogram area' },
  s2_cross_norm: { vi: 'Tính normal mặt phẳng. Không giao hoán: U×V = -(V×U)',
                   en: 'Compute plane normal. Not commutative: U×V = -(V×U)' },
  s2_lindep:     { vi: '<strong>Độc lập tuyến tính:</strong> α₁v₁ + ... + αₙvₙ = 0 chỉ khi tất cả αᵢ = 0.<br><strong>Basis:</strong> n vectors độc lập tuyến tính trong không gian n chiều.',
                   en: '<strong>Linear independence:</strong> α₁v₁ + ... + αₙvₙ = 0 only when all αᵢ = 0.<br><strong>Basis:</strong> any set of n linearly independent vectors in n-dim space.' },
  s2_tests:      { vi: 'Các bài test thường gặp', en: 'Common Geometric Tests' },
  s2_test1:      { vi: 'Đồng phẳng (coplanarity), giao điểm 2 cạnh, song song',
                   en: 'Coplanarity, edge intersection, parallelism' },
  s2_test2:      { vi: 'Hướng xoay tam giác, giao đường/mặt phẳng',
                   en: 'Triangle orientation, line/plane intersection' },

  // ---- Section 3 ----
  s3_idea:       { vi: 'Transformations là các hàm. Matrices biểu diễn hàm đó. Ma trận 2×2 = 2D Linear Transformations.<br><strong>Tính chất:</strong> T(ax + y) = aT(x) + T(y)',
                   en: 'Transformations are functions. Matrices represent them. 2×2 matrices = 2D Linear Transformations.<br><strong>Property:</strong> T(ax + y) = aT(x) + T(y)' },
  s3_scale_desc: { vi: 'VD: Scale x gấp 2: [2,0;0,1]·[x,y] = [2x, y]',
                   en: 'Ex: Scale x by 2: [2,0;0,1]·[x,y] = [2x, y]' },
  s3_rot_ex:     { vi: 'VD: Xoay P(2,3) góc 90°: [0,-1;1,0]·[2,3] = (-3, 2)',
                   en: 'Ex: Rotate P(2,3) by 90°: [0,-1;1,0]·[2,3] = (-3, 2)' },
  s3_trans_desc: { vi: 'Translation cần <strong>tọa độ thuần nhất</strong> (thêm w): Point (x,y,1), Vector (x,y,0).',
                   en: 'Translation requires <strong>homogeneous coordinates</strong> (add w): Point (x,y,1), Vector (x,y,0).' },
  s3_homo_use:   { vi: 'Cho phép biểu diễn Scale + Rotate + Translate bằng nhân ma trận 3×3.',
                   en: 'Allows representing Scale + Rotate + Translate as 3×3 matrix multiplication.' },
  s3_compose:    { vi: 'Kết hợp Transformations', en: 'Composing Transformations' },
  s3_compose_d:  { vi: 'Nhân ma trận. <strong>Thứ tự quan trọng!</strong> M = R × T: áp dụng T trước, rồi R. Đọc phải → trái.',
                   en: 'Multiply matrices. <strong>Order matters!</strong> M = R × T: apply T first, then R. Read right → left.' },
  s3_3d_desc:    { vi: 'Mở rộng lên 4×4 với homogeneous coordinates (x, y, z, w).',
                   en: 'Extended to 4×4 with homogeneous coordinates (x, y, z, w).' },
  s3_rotz:       { vi: 'Rotation quanh trục Z', en: 'Rotation around Z' },
  s3_rotz_note:  { vi: 'Tương tự cho R<sub>x</sub>, R<sub>y</sub>.', en: 'Similarly for R<sub>x</sub>, R<sub>y</sub>.' },

  // ---- Section 4 ----
  s4_pixel:      { vi: 'Biểu diễn 2D = tập hợp hữu hạn giá trị số gọi là <strong>pixels</strong>',
                   en: '2D representation as a finite set of digital values called <strong>pixels</strong>' },
  s4_values:     { vi: 'Giá trị pixel: gray level, RGB, độ cao, opacity...',
                   en: 'Pixel values: gray level, RGB, height, opacity...' },
  s4_digit:      { vi: 'Digitization = xấp xỉ cảnh thực', en: 'Digitization = approximation of real scene' },
  s4_fb:         { vi: 'bộ nhớ lưu ảnh, mỗi bit ↔ 1 pixel trên monitor',
                   en: 'memory storing image, each bit ↔ 1 pixel on monitor' },
  s4_ext:        { vi: 'focus hình dạng', en: 'focus on shape' },
  s4_int:        { vi: 'focus màu sắc, texture', en: 'focus on color, texture' },
  s4_tech:       { vi: 'Kỹ thuật',  en: 'Technique' },
  s4_desc:       { vi: 'Mô tả',    en: 'Description' },
  s4_chain:      { vi: 'Chuỗi hướng (4- hoặc 8-connectivity)', en: 'Direction sequences (4- or 8-connectivity)' },
  s4_poly:       { vi: 'Xấp xỉ bằng đa giác',   en: 'Approximate with polygons' },
  s4_sig:        { vi: 'Biểu diễn bằng hàm 1D',  en: '1D function representation' },
  s4_skel:       { vi: 'Rút gọn thành khung xương', en: 'Reduce to structural skeleton' },
  s4_levels:     { vi: '3 Mức độ xử lý', en: '3 Processing Levels' },

  // ---- Section 5 ----
  s5_approx:     { vi: 'Máy tính xấp xỉ đường cong bằng nhiều đoạn thẳng ngắn',
                   en: 'Computers approximate curves with many small line segments' },
  s5_spline:     { vi: 'Định nghĩa "knots" (điểm mốc), dùng đa thức bậc thấp (cubic) để tránh wiggling.',
                   en: 'Define "knots" (key points), use low-degree polynomials (cubic) to avoid wiggling.' },
  s5_cont:       { vi: 'Continuity (Tính liên tục)', en: 'Continuity' },
  s5_order:      { vi: 'Bậc',       en: 'Order' },
  s5_meaning:    { vi: 'Ý nghĩa',   en: 'Meaning' },
  s5_c0:         { vi: 'Cùng điểm nối', en: 'Same join point' },
  s5_c1:         { vi: '+ cùng tiếp tuyến (derivative bậc 1)', en: '+ same tangent (1st derivative)' },
  s5_c2:         { vi: '+ cùng độ cong (derivative bậc 2)',    en: '+ same curvature (2nd derivative)' },
  s5_bez1:       { vi: 'Dùng control points định hình đường cong',  en: 'Uses control points to shape the curve' },
  s5_bez2:       { vi: 'Luôn đi qua điểm đầu và cuối',             en: 'Always passes through first and last points' },
  s5_bez3:       { vi: 'Tiếp tuyến tại đầu/cuối = hướng control polygon', en: 'Tangent at endpoints = direction of control polygon' },
  s5_bez4:       { vi: 'Nằm trong convex hull của control points',  en: 'Lies within convex hull of control points' },
  s5_surf:       { vi: 'mở rộng lên 2 chiều, lưới control points m×n.',
                   en: 'extends to 2D using m×n control point grid.' },

  // ---- Section 6 ----
  s6_delaunay:   { vi: '<strong>Điều kiện Delaunay:</strong> Không có đỉnh nào nằm bên trong đường tròn ngoại tiếp (circumcircle) của bất kỳ tam giác nào.',
                   en: '<strong>Delaunay condition:</strong> No vertex lies inside the circumcircle of any triangle.' },
  s6_maxmin:     { vi: 'Maximize minimum angle → tránh tam giác suy biến',
                   en: 'Maximize minimum angle → avoid degenerate triangles' },
  s6_bw1:        { vi: 'Tạo super-triangle bao tất cả điểm',       en: 'Create super-triangle enclosing all points' },
  s6_bw2:        { vi: 'Thêm từng điểm',                            en: 'Insert each point' },
  s6_bw3:        { vi: 'Tìm "bad triangles" (circumcircle chứa điểm mới)', en: 'Find "bad triangles" (circumcircle contains new point)' },
  s6_bw4:        { vi: 'Xóa bad triangles → tạo polygon hole',      en: 'Remove bad triangles → create polygon hole' },
  s6_bw5:        { vi: 'Nối điểm mới với cạnh polygon → tam giác mới', en: 'Connect new point to polygon edges → new triangles' },
  s6_bw6:        { vi: 'Lặp lại, cuối cùng xóa super-triangle',    en: 'Repeat, finally remove super-triangle vertices' },
  s6_ec:         { vi: 'gộp 2 đỉnh thành 1 → xóa 2 tam giác',     en: 'merge 2 vertices into 1 → remove 2 triangles' },
  s6_vd:         { vi: 'xóa đỉnh, re-triangulate',                  en: 'remove vertex, re-triangulate' },
  s6_qem:        { vi: 'Dùng Quadric Error Metric để ưu tiên',      en: 'Use Quadric Error Metric to prioritize' },
  s6_hf1:        { vi: 'Tìm boundary edges của lỗ',                 en: 'Find hole boundary edges' },
  s6_hf2:        { vi: 'Chọn đỉnh có góc nhỏ nhất giữa 2 cạnh kề', en: 'Select vertex with smallest angle between adjacent edges' },
  s6_hf3:        { vi: '3 rules: θ<75° → 1 tri; 75-135° → 2 tri; ≥135° → 3 tri',
                   en: '3 rules: θ<75° → 1 tri; 75-135° → 2 tri; ≥135° → 3 tri' },
  s6_hf4:        { vi: 'Lặp đến khi đóng, rồi Laplacian Smoothing', en: 'Repeat until closed, then Laplacian Smoothing' },

  // ---- Section 7 ----
  s7_def:        { vi: 'API đồ họa cấp thấp, cross-platform, procedural (không phải descriptive). Hoạt động như state machine.',
                   en: 'Low-level graphics API, cross-platform, procedural (not descriptive). Works as a state machine.' },
  s7_desc:       { vi: 'Mô tả', en: 'Description' },
  s7_tex:        { vi: 'Áp ảnh 2D lên bề mặt 3D',              en: 'Apply 2D images to 3D surfaces' },
  s7_zbuf:       { vi: 'Tự động loại mặt bị che',               en: 'Auto-remove hidden surfaces' },
  s7_dbl:        { vi: 'Vẽ back buffer, swap → mượt',           en: 'Draw to back buffer, swap → smooth' },
  s7_light:      { vi: 'Hiệu ứng ánh sáng',                    en: 'Lighting effects' },
  s7_shade:      { vi: 'Tô bóng mượt',                          en: 'Smooth shading effects' },
  s7_alpha:      { vi: 'Độ trong suốt',                         en: 'Transparency/opacity' },
  s7_tmat:       { vi: 'Thay đổi vị trí, kích thước, phối cảnh', en: 'Change position, size, perspective' },

  // ---- Section 8 ----
  s8_m1:         { vi: 'Cách 1: Python — scipy',                      en: 'Method 1: Python — scipy' },
  s8_m2:         { vi: 'Cách 2: Python — Bowyer-Watson (tự code)',    en: 'Method 2: Python — Bowyer-Watson (from scratch)' },
  s8_m3:         { vi: 'Cách 3: C++ — Bowyer-Watson (standalone)',    en: 'Method 3: C++ — Bowyer-Watson (standalone)' },

  // ---- Section 9 ----
  s9_funcs:      { vi: 'Các hàm quan trọng',  en: 'Key Functions' },
  s9_func:       { vi: 'Hàm',          en: 'Function' },
  s9_purpose:    { vi: 'Chức năng',     en: 'Purpose' },
  s9_begin:      { vi: 'Bắt đầu/kết thúc vẽ', en: 'Begin/end drawing' },
  s9_vertex:     { vi: 'Đỉnh 3D',      en: '3D vertex' },
  s9_color:      { vi: 'Đặt màu',      en: 'Set color' },
  s9_trs:        { vi: 'Dịch chuyển / Xoay / Co dãn', en: 'Translate / Rotate / Scale' },
  s9_pushpop:    { vi: 'Lưu / khôi phục ma trận',     en: 'Save / restore matrix' },
  s9_persp:      { vi: 'Phối cảnh',     en: 'Perspective projection' },
  s9_shapes:     { vi: 'Vẽ hình cơ bản', en: 'Basic Shapes' },

  // ---- Section 10 ----
  s10_what:      { vi: 'Nên ghi những gì vào tờ A4?', en: 'What to write on your A4 sheet?' },
  s10_side1:     { vi: 'Mặt 1: Theory + Math',        en: 'Side 1: Theory + Math' },
  s10_side2:     { vi: 'Mặt 2: Code',                 en: 'Side 2: Code' },
  s10_mat2d:     { vi: 'Ma trận 2D/3D: Scale, Rotate, Translate', en: '2D/3D matrices: Scale, Rotate, Translate' },
  s10_dotcross:  { vi: 'Công thức + ý nghĩa',         en: 'Formulas + meaning' },
  s10_bezcont:   { vi: 'tính chất, continuity C0/C1/C2', en: 'properties, continuity C0/C1/C2' },
  s10_delcond:   { vi: 'Điều kiện Delaunay',           en: 'Delaunay condition' },
  s10_calcex:    { vi: 'VD tính toán: xoay điểm, kết hợp transformations',
                   en: 'Calculation examples: rotate point, compose transforms' },
  s10_tips:      { vi: 'Lưu ý:', en: 'Tips:' },
  s10_t1:        { vi: 'Theory: ngắn gọn + đưa VD cụ thể',              en: 'Theory: concise + concrete examples' },
  s10_t2:        { vi: 'Math: trình bày rõ từng bước tính ma trận',      en: 'Math: show clear step-by-step matrix calculations' },
  s10_t3:        { vi: 'Thực hành: viết code đúng syntax, có comment',   en: 'Practice: correct syntax, add comments' },
  s10_t4:        { vi: 'Algorithms: nêu ý tưởng + các bước',             en: 'Algorithms: state idea + steps' },
};

/** Get translated string. Falls back to key if not found. */
function t(key) {
  const entry = I18N[key];
  if (!entry) return key;
  return entry[currentLang] || entry.vi || key;
}

let currentLang = 'vi';
