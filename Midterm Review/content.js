/**
 * content.js - Section definitions.
 *
 * Each section is a plain object describing its structure.
 * Translatable text uses t('key') which reads from i18n.js.
 * Static content (formulas, code, matrices) is written directly.
 *
 * Supported block types: html, note, note-important, table, matrix,
 *   formula, code, steps, pipeline, two-col
 */

const CODE_SNIPPETS = {
  scipy: `<span class="kw">import</span> numpy <span class="kw">as</span> np
<span class="kw">from</span> scipy.spatial <span class="kw">import</span> Delaunay
<span class="kw">import</span> matplotlib.pyplot <span class="kw">as</span> plt

points = np.array([[<span class="num">0</span>,<span class="num">0</span>],[<span class="num">1</span>,<span class="num">0</span>],[<span class="num">2</span>,<span class="num">0</span>],[<span class="num">0</span>,<span class="num">1</span>],[<span class="num">1</span>,<span class="num">1</span>],[<span class="num">2</span>,<span class="num">1</span>],[<span class="num">0.5</span>,<span class="num">0.5</span>],[<span class="num">1.5</span>,<span class="num">0.5</span>]])
tri = <span class="fn">Delaunay</span>(points)
plt.<span class="fn">triplot</span>(points[:,<span class="num">0</span>], points[:,<span class="num">1</span>], tri.simplices)
plt.<span class="fn">plot</span>(points[:,<span class="num">0</span>], points[:,<span class="num">1</span>], <span class="st">'o'</span>)
plt.<span class="fn">show</span>()`,

  bowyerWatson: `<span class="kw">import</span> numpy <span class="kw">as</span> np
<span class="kw">import</span> matplotlib.pyplot <span class="kw">as</span> plt

<span class="kw">def</span> <span class="fn">circumcircle_contains</span>(tri_pts, point):
    ax,ay = tri_pts[<span class="num">0</span>]; bx,by = tri_pts[<span class="num">1</span>]
    cx,cy = tri_pts[<span class="num">2</span>]; dx,dy = point
    mat = np.array([
        [ax-dx, ay-dy, (ax-dx)**<span class="num">2</span>+(ay-dy)**<span class="num">2</span>],
        [bx-dx, by-dy, (bx-dx)**<span class="num">2</span>+(by-dy)**<span class="num">2</span>],
        [cx-dx, cy-dy, (cx-dx)**<span class="num">2</span>+(cy-dy)**<span class="num">2</span>]])
    <span class="kw">return</span> np.linalg.<span class="fn">det</span>(mat) > <span class="num">0</span>

<span class="kw">def</span> <span class="fn">bowyer_watson</span>(points):
    pts = [<span class="fn">tuple</span>(p) <span class="kw">for</span> p <span class="kw">in</span> points]
    mn = [<span class="fn">min</span>(p[i] <span class="kw">for</span> p <span class="kw">in</span> pts)-<span class="num">10</span> <span class="kw">for</span> i <span class="kw">in</span> (<span class="num">0</span>,<span class="num">1</span>)]
    mx = [<span class="fn">max</span>(p[i] <span class="kw">for</span> p <span class="kw">in</span> pts)+<span class="num">10</span> <span class="kw">for</span> i <span class="kw">in</span> (<span class="num">0</span>,<span class="num">1</span>)]
    dx, dy = mx[<span class="num">0</span>]-mn[<span class="num">0</span>], mx[<span class="num">1</span>]-mn[<span class="num">1</span>]
    sp = [(mn[<span class="num">0</span>]-dx,mn[<span class="num">1</span>]-dy),(mx[<span class="num">0</span>]+<span class="num">2</span>*dx,mn[<span class="num">1</span>]-dy),(mn[<span class="num">0</span>]+dx/<span class="num">2</span>,mx[<span class="num">1</span>]+<span class="num">2</span>*dy)]
    sv = <span class="fn">set</span>(sp); triangles = [<span class="fn">tuple</span>(sp)]
    <span class="kw">for</span> pt <span class="kw">in</span> pts:
        bad = [t <span class="kw">for</span> t <span class="kw">in</span> triangles <span class="kw">if</span> <span class="fn">circumcircle_contains</span>(<span class="fn">list</span>(t), pt)]
        poly = []
        <span class="kw">for</span> t <span class="kw">in</span> bad:
            <span class="kw">for</span> i <span class="kw">in</span> <span class="fn">range</span>(<span class="num">3</span>):
                e = (t[i], t[(i+<span class="num">1</span>)%<span class="num">3</span>])
                <span class="kw">if not</span> <span class="kw">any</span>(o!=t <span class="kw">and</span> e[<span class="num">0</span>] <span class="kw">in</span> o <span class="kw">and</span> e[<span class="num">1</span>] <span class="kw">in</span> o <span class="kw">for</span> o <span class="kw">in</span> bad):
                    poly.<span class="fn">append</span>(e)
        <span class="kw">for</span> t <span class="kw">in</span> bad: triangles.<span class="fn">remove</span>(t)
        <span class="kw">for</span> e <span class="kw">in</span> poly: triangles.<span class="fn">append</span>((e[<span class="num">0</span>],e[<span class="num">1</span>],pt))
    <span class="kw">return</span> [t <span class="kw">for</span> t <span class="kw">in</span> triangles <span class="kw">if not</span> <span class="fn">any</span>(v <span class="kw">in</span> sv <span class="kw">for</span> v <span class="kw">in</span> t)]

<span class="cm"># Demo</span>
np.random.<span class="fn">seed</span>(<span class="num">42</span>)
pts = np.random.<span class="fn">rand</span>(<span class="num">20</span>,<span class="num">2</span>)*<span class="num">10</span>
<span class="kw">for</span> t <span class="kw">in</span> <span class="fn">bowyer_watson</span>(pts):
    p = <span class="fn">list</span>(t)+[t[<span class="num">0</span>]]
    plt.<span class="fn">plot</span>([x[<span class="num">0</span>] <span class="kw">for</span> x <span class="kw">in</span> p],[x[<span class="num">1</span>] <span class="kw">for</span> x <span class="kw">in</span> p],<span class="st">'b-'</span>,lw=<span class="num">0.8</span>)
plt.<span class="fn">plot</span>(pts[:,<span class="num">0</span>],pts[:,<span class="num">1</span>],<span class="st">'ro'</span>,ms=<span class="num">4</span>); plt.<span class="fn">show</span>()`,

  bowyerWatsonCpp: `<span class="cm">// Bowyer-Watson Delaunay Triangulation in C++</span>
<span class="cm">// Compile: g++ -o delaunay delaunay.cpp -std=c++17</span>

<span class="kw">#include</span> &lt;iostream&gt;
<span class="kw">#include</span> &lt;vector&gt;
<span class="kw">#include</span> &lt;cmath&gt;
<span class="kw">#include</span> &lt;algorithm&gt;
<span class="kw">#include</span> &lt;cstdlib&gt;

<span class="kw">struct</span> <span class="fn">Point</span> {
    <span class="kw">double</span> x, y;
};

<span class="kw">struct</span> <span class="fn">Triangle</span> {
    <span class="kw">int</span> v0, v1, v2;
};

<span class="kw">struct</span> <span class="fn">Edge</span> {
    <span class="kw">int</span> a, b;
    <span class="kw">bool</span> <span class="kw">operator</span>==(<span class="kw">const</span> Edge& o) <span class="kw">const</span> {
        <span class="kw">return</span> (a == o.a && b == o.b) || (a == o.b && b == o.a);
    }
};

<span class="cm">// Check if point p is inside the circumcircle of triangle</span>
<span class="kw">bool</span> <span class="fn">inCircumcircle</span>(<span class="kw">const</span> std::vector&lt;Point&gt;& pts,
                    <span class="kw">const</span> Triangle& tri, <span class="kw">const</span> Point& p) {
    <span class="kw">double</span> ax = pts[tri.v0].x, ay = pts[tri.v0].y;
    <span class="kw">double</span> bx = pts[tri.v1].x, by = pts[tri.v1].y;
    <span class="kw">double</span> cx = pts[tri.v2].x, cy = pts[tri.v2].y;

    <span class="kw">double</span> D = <span class="num">2.0</span> * (ax*(by-cy) + bx*(cy-ay) + cx*(ay-by));
    <span class="kw">if</span> (std::<span class="fn">abs</span>(D) &lt; <span class="num">1e-12</span>) <span class="kw">return false</span>;

    <span class="kw">double</span> ux = ((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay)
               + (cx*cx+cy*cy)*(ay-by)) / D;
    <span class="kw">double</span> uy = ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx)
               + (cx*cx+cy*cy)*(bx-ax)) / D;

    <span class="kw">double</span> r2 = (ax-ux)*(ax-ux) + (ay-uy)*(ay-uy);
    <span class="kw">double</span> d2 = (p.x-ux)*(p.x-ux) + (p.y-uy)*(p.y-uy);
    <span class="kw">return</span> d2 &lt; r2;
}

std::vector&lt;Triangle&gt; <span class="fn">delaunay</span>(<span class="kw">const</span> std::vector&lt;Point&gt;& input) {
    <span class="kw">int</span> n = input.size();
    std::vector&lt;Point&gt; pts = input;

    <span class="cm">// Step 1: Create super-triangle</span>
    <span class="kw">double</span> margin = <span class="num">1000.0</span>;
    <span class="kw">int</span> s0 = n, s1 = n+<span class="num">1</span>, s2 = n+<span class="num">2</span>;
    pts.push_back({-margin, -margin});
    pts.push_back({ <span class="num">3</span>*margin, -margin});
    pts.push_back({-margin,  <span class="num">3</span>*margin});

    std::vector&lt;Triangle&gt; tris = {{s0, s1, s2}};

    <span class="cm">// Step 2: Insert each point</span>
    <span class="kw">for</span> (<span class="kw">int</span> i = <span class="num">0</span>; i &lt; n; i++) {
        <span class="cm">// Find bad triangles</span>
        std::vector&lt;Triangle&gt; bad;
        <span class="kw">for</span> (<span class="kw">auto</span>& t : tris)
            <span class="kw">if</span> (<span class="fn">inCircumcircle</span>(pts, t, pts[i]))
                bad.push_back(t);

        <span class="cm">// Find boundary polygon</span>
        std::vector&lt;Edge&gt; boundary;
        <span class="kw">for</span> (<span class="kw">auto</span>& t : bad) {
            Edge edges[] = {{t.v0,t.v1},{t.v1,t.v2},{t.v2,t.v0}};
            <span class="kw">for</span> (<span class="kw">auto</span>& e : edges) {
                <span class="kw">bool</span> shared = <span class="kw">false</span>;
                <span class="kw">for</span> (<span class="kw">auto</span>& t2 : bad) {
                    <span class="kw">if</span> (&t2 == &t) <span class="kw">continue</span>;
                    Edge e2[] = {{t2.v0,t2.v1},{t2.v1,t2.v2},{t2.v2,t2.v0}};
                    <span class="kw">for</span> (<span class="kw">auto</span>& ee : e2)
                        <span class="kw">if</span> (e == ee) { shared = <span class="kw">true</span>; <span class="kw">break</span>; }
                    <span class="kw">if</span> (shared) <span class="kw">break</span>;
                }
                <span class="kw">if</span> (!shared) boundary.push_back(e);
            }
        }

        <span class="cm">// Remove bad triangles</span>
        tris.erase(std::<span class="fn">remove_if</span>(tris.begin(), tris.end(),
            [&](<span class="kw">const</span> Triangle& t) {
                <span class="kw">for</span> (<span class="kw">auto</span>& b : bad)
                    <span class="kw">if</span> (t.v0==b.v0 && t.v1==b.v1 && t.v2==b.v2)
                        <span class="kw">return true</span>;
                <span class="kw">return false</span>;
            }), tris.end());

        <span class="cm">// Create new triangles</span>
        <span class="kw">for</span> (<span class="kw">auto</span>& e : boundary)
            tris.push_back({e.a, e.b, i});
    }

    <span class="cm">// Step 3: Remove super-triangle</span>
    tris.erase(std::<span class="fn">remove_if</span>(tris.begin(), tris.end(),
        [&](<span class="kw">const</span> Triangle& t) {
            <span class="kw">return</span> t.v0>=n || t.v1>=n || t.v2>=n;
        }), tris.end());

    <span class="kw">return</span> tris;
}

<span class="kw">int</span> <span class="fn">main</span>() {
    std::vector&lt;Point&gt; points = {
        {<span class="num">0</span>,<span class="num">0</span>}, {<span class="num">4</span>,<span class="num">0</span>}, {<span class="num">2</span>,<span class="num">3</span>}, {<span class="num">1</span>,<span class="num">1</span>},
        {<span class="num">3</span>,<span class="num">1</span>}, {<span class="num">5</span>,<span class="num">2</span>}, {<span class="num">1</span>,<span class="num">4</span>}, {<span class="num">3</span>,<span class="num">5</span>}
    };

    <span class="kw">auto</span> tris = <span class="fn">delaunay</span>(points);

    std::cout &lt;&lt; <span class="st">"Delaunay Triangulation: "</span>
              &lt;&lt; tris.size() &lt;&lt; <span class="st">" triangles\\n"</span>;
    <span class="kw">for</span> (<span class="kw">auto</span>& t : tris) {
        std::cout &lt;&lt; <span class="st">"  ("</span> &lt;&lt; t.v0 &lt;&lt; <span class="st">", "</span>
                  &lt;&lt; t.v1 &lt;&lt; <span class="st">", "</span> &lt;&lt; t.v2 &lt;&lt; <span class="st">")  ->  ("</span>
                  &lt;&lt; points[t.v0].x &lt;&lt; <span class="st">","</span> &lt;&lt; points[t.v0].y &lt;&lt; <span class="st">") ("</span>
                  &lt;&lt; points[t.v1].x &lt;&lt; <span class="st">","</span> &lt;&lt; points[t.v1].y &lt;&lt; <span class="st">") ("</span>
                  &lt;&lt; points[t.v2].x &lt;&lt; <span class="st">","</span> &lt;&lt; points[t.v2].y &lt;&lt; <span class="st">")\\n"</span>;
    }
    <span class="kw">return</span> <span class="num">0</span>;
}`,

  openglTemplate: `<span class="kw">from</span> OpenGL.GL <span class="kw">import</span> *
<span class="kw">from</span> OpenGL.GLU <span class="kw">import</span> *
<span class="kw">from</span> OpenGL.GLUT <span class="kw">import</span> *

<span class="kw">def</span> <span class="fn">init</span>():
    <span class="fn">glClearColor</span>(<span class="num">0</span>,<span class="num">0</span>,<span class="num">0</span>,<span class="num">1</span>)
    <span class="fn">glEnable</span>(GL_DEPTH_TEST)
    <span class="fn">glMatrixMode</span>(GL_PROJECTION)
    <span class="fn">gluPerspective</span>(<span class="num">45</span>,<span class="num">1.0</span>,<span class="num">0.1</span>,<span class="num">50.0</span>)
    <span class="fn">glMatrixMode</span>(GL_MODELVIEW)

<span class="kw">def</span> <span class="fn">display</span>():
    <span class="fn">glClear</span>(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    <span class="fn">glLoadIdentity</span>()
    <span class="fn">gluLookAt</span>(<span class="num">0</span>,<span class="num">0</span>,<span class="num">5</span>, <span class="num">0</span>,<span class="num">0</span>,<span class="num">0</span>, <span class="num">0</span>,<span class="num">1</span>,<span class="num">0</span>)
    <span class="fn">glBegin</span>(GL_TRIANGLES)
    <span class="fn">glColor3f</span>(<span class="num">1</span>,<span class="num">0</span>,<span class="num">0</span>); <span class="fn">glVertex3f</span>(-<span class="num">1</span>,-<span class="num">1</span>,<span class="num">0</span>)
    <span class="fn">glColor3f</span>(<span class="num">0</span>,<span class="num">1</span>,<span class="num">0</span>); <span class="fn">glVertex3f</span>(<span class="num">1</span>,-<span class="num">1</span>,<span class="num">0</span>)
    <span class="fn">glColor3f</span>(<span class="num">0</span>,<span class="num">0</span>,<span class="num">1</span>); <span class="fn">glVertex3f</span>(<span class="num">0</span>,<span class="num">1</span>,<span class="num">0</span>)
    <span class="fn">glEnd</span>()
    <span class="fn">glutSwapBuffers</span>()

<span class="kw">def</span> <span class="fn">reshape</span>(w,h):
    <span class="fn">glViewport</span>(<span class="num">0</span>,<span class="num">0</span>,w,h)
    <span class="fn">glMatrixMode</span>(GL_PROJECTION); <span class="fn">glLoadIdentity</span>()
    <span class="fn">gluPerspective</span>(<span class="num">45</span>,w/h,<span class="num">0.1</span>,<span class="num">50.0</span>)
    <span class="fn">glMatrixMode</span>(GL_MODELVIEW)

<span class="fn">glutInit</span>()
<span class="fn">glutInitDisplayMode</span>(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
<span class="fn">glutInitWindowSize</span>(<span class="num">800</span>,<span class="num">600</span>)
<span class="fn">glutCreateWindow</span>(b<span class="st">"OpenGL Demo"</span>)
<span class="fn">init</span>()
<span class="fn">glutDisplayFunc</span>(display)
<span class="fn">glutReshapeFunc</span>(reshape)
<span class="fn">glutMainLoop</span>()`,

  openglTransform: `<span class="fn">glPushMatrix</span>()
<span class="fn">glTranslatef</span>(<span class="num">1.0</span>, <span class="num">0.0</span>, <span class="num">0.0</span>)   <span class="cm"># Translate</span>
<span class="fn">glRotatef</span>(<span class="num">45</span>, <span class="num">0</span>, <span class="num">0</span>, <span class="num">1</span>)       <span class="cm"># Rotate 45 deg Z</span>
<span class="fn">glScalef</span>(<span class="num">0.5</span>, <span class="num">0.5</span>, <span class="num">0.5</span>)      <span class="cm"># Scale 50%</span>
<span class="fn">glutSolidTeapot</span>(<span class="num">0.5</span>)
<span class="fn">glPopMatrix</span>()`,

  openglShapes: `<span class="cm"># Point</span>
<span class="fn">glBegin</span>(GL_POINTS); <span class="fn">glVertex3f</span>(<span class="num">0</span>,<span class="num">0</span>,<span class="num">0</span>); <span class="fn">glEnd</span>()

<span class="cm"># Line</span>
<span class="fn">glBegin</span>(GL_LINES)
<span class="fn">glVertex3f</span>(<span class="num">0</span>,<span class="num">0</span>,<span class="num">0</span>); <span class="fn">glVertex3f</span>(<span class="num">1</span>,<span class="num">1</span>,<span class="num">0</span>)
<span class="fn">glEnd</span>()

<span class="cm"># Quad</span>
<span class="fn">glBegin</span>(GL_QUADS)
<span class="fn">glVertex3f</span>(-<span class="num">1</span>,-<span class="num">1</span>,<span class="num">0</span>); <span class="fn">glVertex3f</span>(<span class="num">1</span>,-<span class="num">1</span>,<span class="num">0</span>)
<span class="fn">glVertex3f</span>(<span class="num">1</span>,<span class="num">1</span>,<span class="num">0</span>); <span class="fn">glVertex3f</span>(-<span class="num">1</span>,<span class="num">1</span>,<span class="num">0</span>)
<span class="fn">glEnd</span>()

<span class="cm"># Circle</span>
<span class="kw">import</span> math
<span class="fn">glBegin</span>(GL_LINE_LOOP)
<span class="kw">for</span> i <span class="kw">in</span> <span class="fn">range</span>(<span class="num">100</span>):
    a = <span class="num">2</span>*math.pi*i/<span class="num">100</span>
    <span class="fn">glVertex3f</span>(math.<span class="fn">cos</span>(a), math.<span class="fn">sin</span>(a), <span class="num">0</span>)
<span class="fn">glEnd</span>()`,
};


/**
 * Build all section HTML. Called on every language switch.
 * Returns an HTML string to set as innerHTML of #content.
 */
function buildSections() {
  return [
    buildS1(), buildS2(), buildS3(), buildS4(), buildS5(),
    buildS6(), buildS7(), buildS8(), buildS9(), buildS10(),
  ].join('');
}

/* ---------- helpers ---------- */
function sec(id, titleKey, body) {
  return `<section id="${id}"><h2>${t(titleKey)}</h2>${body}</section>`;
}
function note(content, cls = '') {
  return `<div class="note ${cls}">${content}</div>`;
}
/**
 * Render a matrix with proper bracket notation.
 *   mat([['a','b'],['c','d']])             → bracketed 2×2
 *   mat([['a','b'],['c','d']], 'M =')      → "M =" prefix
 *   mat([['a','b']], 'M =', '=', [['e'],['f']])  → "M = [ab] = [e;f]"
 */
function mat(rows, label, eqSign, resultRows) {
  const toTable = (r) => '<table>' + r.map(row =>
    '<tr>' + row.map(c => `<td>${c}</td>`).join('') + '</tr>'
  ).join('') + '</table>';

  let html = '<div class="matrix-wrap">';
  if (label) html += `<span class="mat-label">${label}</span>`;
  html += `<span class="mat">${toTable(rows)}</span>`;
  if (eqSign && resultRows) {
    html += `<span class="mat-eq">${eqSign}</span>`;
    html += `<span class="mat">${toTable(resultRows)}</span>`;
  }
  html += '</div>';
  return html;
}

/** Shorthand for inline formula display (non-matrix) */
function matInline(text) {
  return `<div class="matrix-wrap"><span class="mat-result">${text}</span></div>`;
}

/** Render a full matrix equation:  [A] · [B] = [C]  with optional suffix text */
function matEq(aRows, bRows, cRows, suffix) {
  const toTable = (r) => '<table>' + r.map(row =>
    '<tr>' + row.map(c => `<td>${c}</td>`).join('') + '</tr>'
  ).join('') + '</table>';

  let html = '<div class="matrix-wrap">';
  html += `<span class="mat">${toTable(aRows)}</span>`;
  html += '<span class="mat-eq">·</span>';
  html += `<span class="mat">${toTable(bRows)}</span>`;
  html += '<span class="mat-eq">=</span>';
  html += `<span class="mat">${toTable(cRows)}</span>`;
  if (suffix) html += `<span class="mat-label" style="margin-left:8px">${suffix}</span>`;
  html += '</div>';
  return html;
}
function code(content) {
  return `<pre>${content}</pre>`;
}
function tbl(headers, rows) {
  const ths = headers.map(h => `<th>${h}</th>`).join('');
  const trs = rows.map(r => '<tr>' + r.map(c => `<td>${c}</td>`).join('') + '</tr>').join('');
  return `<table><tr>${ths}</tr>${trs}</table>`;
}
function steps(items) {
  return '<ol class="steps">' + items.map(i => `<li>${i}</li>`).join('') + '</ol>';
}
function pipeline(items) {
  return '<div class="pipeline">' + items.map((item, i) =>
    (i > 0 ? '<span class="pipe-arrow">→</span>' : '') +
    `<span class="pipe-item">${item}</span>`
  ).join('') + '</div>';
}
function twocol(left, right) {
  return `<div class="two-col"><div class="col-box">${left}</div><div class="col-box">${right}</div></div>`;
}

/* ---------- section builders ---------- */

function buildS1() {
  return sec('s1', 's1_title', `
    ${note(t('s1_def'))}
    <h3>${t('s1_areas')}</h3>
    <ul>
      <li>Hardware devices (GPU, display, input)</li>
      <li>Rendering techniques</li>
      <li>Modelling objects &amp; 3D Simulation</li>
      <li>Image representation &amp; processing</li>
      <li>VR &amp; AR applications</li>
      <li>Visualization of data</li>
    </ul>
    <h3>${t('s1_apps')}</h3>
    <p>Video games, VFX, CAD/CAM, Medical imaging, VR/AR, Data visualization</p>
    <h3>Graphic Hardware</h3>
    <ul>
      <li><strong>GPU:</strong> ${t('s1_gpu')}</li>
      <li><strong>Display:</strong> Monitor, Plotter, VR headset, LCD</li>
      <li><strong>Input:</strong> Camera, 3D scanner, Lidar, glove, gamepad, mouse</li>
    </ul>
  `);
}

function buildS2() {
  return sec('s2', 's2_title', `
    <h3>3 Basic Elements</h3>
    ${twocol(
      `<h4>Scalars</h4><p>${t('s2_scalars')}</p>`,
      `<h4>Vectors</h4><p>${t('s2_vectors')}</p>`
    )}
    ${note(t('s2_points'))}
    <h3>Vector Operations</h3>
    <ul>
      <li><strong>${t('s2_add')}</strong> U + V (head-to-tail)</li>
      <li><strong>${t('s2_smul')}</strong> s(U+V) = sU + sV</li>
      <li><strong>${t('s2_inv')}</strong> -V (${t('s2_inv_desc')})</li>
      <li><strong>Norm:</strong> ||V|| = ${t('s2_norm')}. Unit vector: V/||V||</li>
    </ul>
    <h3>${t('s2_dot')}</h3>
    <div class="formula">U · V = |U||V|cos(θ) = u₁v₁ + u₂v₂ + u₃v₃</div>
    <ul>
      <li>${t('s2_dot_orth')}</li>
      <li>${t('s2_dot_use')}</li>
    </ul>
    <h3>${t('s2_cross')}</h3>
    ${matInline('U × V = ( u₂v₃ − u₃v₂ , &nbsp; u₃v₁ − u₁v₃ , &nbsp; u₁v₂ − u₂v₁ )')}
    <ul>
      <li>${t('s2_cross_perp')}</li>
      <li>|U × V| = ${t('s2_cross_area')}</li>
      <li>${t('s2_cross_norm')}</li>
    </ul>
    <h3>Linear Independence &amp; Basis</h3>
    ${note(t('s2_lindep'))}
    <h3>${t('s2_tests')}</h3>
    <ul>
      <li>${t('s2_test1')}</li>
      <li>${t('s2_test2')}</li>
      <li>Center of mass = (P1+P2+P3)/3</li>
    </ul>
  `);
}

function buildS3() {
  return sec('s3', 's3_title', `
    ${note(t('s3_idea'))}
    <h3>Scaling</h3>
    ${mat([['S<sub>x</sub>','0'],['0','S<sub>y</sub>']], 'Scale(S<sub>x</sub>, S<sub>y</sub>) =')}
    <p>${t('s3_scale_desc')}</p>
    ${matEq([['2','0'],['0','1']], [['x'],['y']], [['2x'],['y']])}
    <h3>Rotation</h3>
    ${mat([['cos θ','−sin θ'],['sin θ','cos θ']], 'R(θ) =')}
    <p>${t('s3_rot_ex')}</p>
    ${matEq([['0','−1'],['1','0']], [['2'],['3']], [['−3'],['2']], "⇒ P' = (−3, 2)")}
    <h3>Translation &amp; Homogeneous Coordinates</h3>
    <p>${t('s3_trans_desc')}</p>
    ${mat([['1','0','t<sub>x</sub>'],['0','1','t<sub>y</sub>'],['0','0','1']], 'T(t<sub>x</sub>, t<sub>y</sub>) =')}
    <p>${t('s3_homo_use')}</p>
    <h3>${t('s3_compose')}</h3>
    <p>${t('s3_compose_d')}</p>
    <h3>3D Transformations (4×4)</h3>
    <p>${t('s3_3d_desc')}</p>
    ${twocol(
      `<h4>Translation</h4>${mat([['1','0','0','t<sub>x</sub>'],['0','1','0','t<sub>y</sub>'],['0','0','1','t<sub>z</sub>'],['0','0','0','1']])}`,
      `<h4>Scale</h4>${mat([['S<sub>x</sub>','0','0','0'],['0','S<sub>y</sub>','0','0'],['0','0','S<sub>z</sub>','0'],['0','0','0','1']])}`
    )}
    <h4>${t('s3_rotz')}</h4>
    ${mat([['cos θ','−sin θ','0','0'],['sin θ','cos θ','0','0'],['0','0','1','0'],['0','0','0','1']], 'R<sub>z</sub>(θ) =')}
    <p><em>${t('s3_rotz_note')}</em></p>
  `);
}

function buildS4() {
  return sec('s4', 's4_title', `
    <h3>Digital Image</h3>
    <ul>
      <li>${t('s4_pixel')}</li>
      <li>${t('s4_values')}</li>
      <li>${t('s4_digit')}</li>
      <li><strong>Frame buffer:</strong> ${t('s4_fb')}</li>
    </ul>
    <h3>Representation</h3>
    <ul>
      <li><strong>External (Boundary):</strong> ${t('s4_ext')}</li>
      <li><strong>Internal (Pixels):</strong> ${t('s4_int')}</li>
    </ul>
    ${tbl(
      [t('s4_tech'), t('s4_desc')],
      [
        ['Chain Codes', t('s4_chain')],
        ['Polygonal Approx.', t('s4_poly')],
        ['Signatures', t('s4_sig')],
        ['Skeletons', t('s4_skel')],
      ]
    )}
    <h3>Processing Pipeline</h3>
    ${pipeline(['Acquisition','Enhancement','Restoration','Morphological','Segmentation','Recognition','Representation'])}
    <h3>${t('s4_levels')}</h3>
    <ul>
      <li><strong>Low:</strong> Image → Image (e.g. noise removal)</li>
      <li><strong>Mid:</strong> Image → Attributes (e.g. segmentation)</li>
      <li><strong>High:</strong> Attributes → Understanding (e.g. scene understanding)</li>
    </ul>
  `);
}

function buildS5() {
  return sec('s5', 's5_title', `
    <ul><li>${t('s5_approx')}</li></ul>
    <h3>Parametric Equations</h3>
    <div class="formula">x(t) = x₀ + t·dx, &nbsp; y(t) = y₀ + t·dy, &nbsp; 0 ≤ t ≤ 1</div>
    <h3>Linear Interpolation</h3>
    <div class="formula">P(t) = (1−t)·P₁ + t·P₂</div>
    <h3>Splines</h3>
    <p>${t('s5_spline')}</p>
    <h3>${t('s5_cont')}</h3>
    ${tbl(
      [t('s5_order'), t('s5_meaning')],
      [['<strong>C0</strong>', t('s5_c0')], ['<strong>C1</strong>', t('s5_c1')], ['<strong>C2</strong>', t('s5_c2')]]
    )}
    <h3>Bezier Curves</h3>
    <ul>
      <li>${t('s5_bez1')}</li><li>${t('s5_bez2')}</li>
      <li>${t('s5_bez3')}</li><li>${t('s5_bez4')}</li>
    </ul>
    <p><strong>Bezier Surface:</strong> ${t('s5_surf')}</p>
  `);
}

function buildS6() {
  return sec('s6', 's6_title', `
    <h3>Delaunay Triangulation</h3>
    ${note(t('s6_delaunay'), 'note-important')}
    <ul><li>${t('s6_maxmin')}</li></ul>
    <h4>Bowyer-Watson:</h4>
    ${steps([t('s6_bw1'), t('s6_bw2'), t('s6_bw3'), t('s6_bw4'), t('s6_bw5'), t('s6_bw6')])}
    <h3>Mesh Simplification</h3>
    <ul>
      <li><strong>Edge Collapse:</strong> ${t('s6_ec')}</li>
      <li><strong>Vertex Decimation:</strong> ${t('s6_vd')}</li>
      <li>${t('s6_qem')}</li>
    </ul>
    <h3>Hole Filling (Advancing Front)</h3>
    ${steps([t('s6_hf1'), t('s6_hf2'), t('s6_hf3'), t('s6_hf4')])}
  `);
}

function buildS7() {
  return sec('s7', 's7_title', `
    ${note(t('s7_def'))}
    <h3>OpenGL Features</h3>
    ${tbl(
      ['Feature', t('s7_desc')],
      [
        ['Texture Mapping', t('s7_tex')],
        ['Z-buffering', t('s7_zbuf') + ' <code>glEnable(GL_DEPTH_TEST)</code>'],
        ['Double Buffering', t('s7_dbl')],
        ['Lighting', t('s7_light')],
        ['Smooth Shading', t('s7_shade')],
        ['Alpha Blending', t('s7_alpha')],
        ['Transformation Matrices', t('s7_tmat')],
      ]
    )}
  `);
}

function buildS8() {
  return sec('s8', 's8_title', `
    <h3>${t('s8_m1')}</h3>
    ${code(CODE_SNIPPETS.scipy)}
    <h3>${t('s8_m2')}</h3>
    ${code(CODE_SNIPPETS.bowyerWatson)}
    <h3>${t('s8_m3')}</h3>
    ${code(CODE_SNIPPETS.bowyerWatsonCpp)}
  `);
}

function buildS9() {
  return sec('s9', 's9_title', `
    <h3>Template</h3>
    ${code(CODE_SNIPPETS.openglTemplate)}
    <h3>Transformations</h3>
    ${code(CODE_SNIPPETS.openglTransform)}
    <h3>${t('s9_funcs')}</h3>
    ${tbl(
      [t('s9_func'), t('s9_purpose')],
      [
        ['<code>glBegin/glEnd</code>', t('s9_begin')],
        ['<code>GL_POINTS, GL_LINES, GL_TRIANGLES, GL_QUADS</code>', 'Primitive types'],
        ['<code>glVertex3f(x,y,z)</code>', t('s9_vertex')],
        ['<code>glColor3f(r,g,b)</code>', t('s9_color')],
        ['<code>glTranslatef / glRotatef / glScalef</code>', t('s9_trs')],
        ['<code>glPushMatrix / glPopMatrix</code>', t('s9_pushpop')],
        ['<code>glEnable(GL_DEPTH_TEST)</code>', 'Z-buffer'],
        ['<code>gluLookAt(...)</code>', 'Camera'],
        ['<code>gluPerspective(...)</code>', t('s9_persp')],
        ['<code>glLoadIdentity()</code>', 'Reset matrix'],
      ]
    )}
    <h3>${t('s9_shapes')}</h3>
    ${code(CODE_SNIPPETS.openglShapes)}
  `);
}

function buildS10() {
  return sec('s10', 's10_title', `
    ${twocol(
      `<h4>${t('s10_side1')}</h4>
       <ol>
         <li>${t('s10_mat2d')}</li>
         <li>Homogeneous coords: Point w=1, Vector w=0</li>
         <li>Dot &amp; Cross product: ${t('s10_dotcross')}</li>
         <li>Bezier + Continuity: ${t('s10_bezcont')}</li>
         <li>${t('s10_delcond')} + Bowyer-Watson</li>
         <li>Hole filling: 3 angle rules</li>
         <li>Image processing pipeline</li>
       </ol>`,
      `<h4>${t('s10_side2')}</h4>
       <ol>
         <li>OpenGL template (init, display, reshape)</li>
         <li>glBegin/End, glVertex, glColor, glTranslate, glRotate, glScale</li>
         <li>Delaunay: circumcircle_contains + bowyer_watson</li>
         <li>${t('s10_calcex')}</li>
       </ol>`
    )}
    ${note(`<strong>${t('s10_tips')}</strong>
      <ul style="margin-bottom:0;">
        <li>${t('s10_t1')}</li><li>${t('s10_t2')}</li>
        <li>${t('s10_t3')}</li><li>${t('s10_t4')}</li>
      </ul>`, 'note-important')}
  `);
}
