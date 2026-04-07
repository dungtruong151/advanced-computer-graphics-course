"""
Python OpenGL Basic Demo - IT516 Midterm Review
Demonstrates: window setup, drawing primitives, transformations, animation, keyboard input.
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import sys

# ----- Global state -----
rotation_angle = 0.0
auto_rotate = True

# ============================================================
# 1. INITIALIZATION
# ============================================================
def init():
    """Set up OpenGL rendering state."""
    glClearColor(0.95, 0.95, 0.95, 1.0)    # Light gray background
    glEnable(GL_DEPTH_TEST)                  # Enable z-buffer
    glEnable(GL_BLEND)                       # Enable transparency
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(2.0)
    glPointSize(6.0)

# ============================================================
# 2. DRAWING PRIMITIVES
# ============================================================
def draw_axes():
    """Draw X (red), Y (green), Z (blue) axes."""
    glBegin(GL_LINES)
    # X axis - red
    glColor3f(0.9, 0.2, 0.2)
    glVertex3f(0, 0, 0)
    glVertex3f(3, 0, 0)
    # Y axis - green
    glColor3f(0.2, 0.7, 0.2)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 3, 0)
    # Z axis - blue
    glColor3f(0.2, 0.2, 0.9)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 3)
    glEnd()

def draw_triangle():
    """Draw a colored triangle using GL_TRIANGLES."""
    glBegin(GL_TRIANGLES)
    glColor3f(0.9, 0.2, 0.2)       # Red
    glVertex3f(-1.0, -0.7, 0.0)
    glColor3f(0.2, 0.8, 0.2)       # Green
    glVertex3f(1.0, -0.7, 0.0)
    glColor3f(0.2, 0.2, 0.9)       # Blue
    glVertex3f(0.0, 0.9, 0.0)
    glEnd()

def draw_quad():
    """Draw a semi-transparent quad using GL_QUADS."""
    glBegin(GL_QUADS)
    glColor4f(0.9, 0.6, 0.1, 0.6)  # Orange, 60% opacity
    glVertex3f(-0.6, -0.6, 0.0)
    glVertex3f(0.6, -0.6, 0.0)
    glVertex3f(0.6, 0.6, 0.0)
    glVertex3f(-0.6, 0.6, 0.0)
    glEnd()

def draw_circle(radius, segments=64):
    """Draw a circle approximated by line segments."""
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        glVertex3f(radius * math.cos(angle), radius * math.sin(angle), 0.0)
    glEnd()

def draw_points():
    """Draw some individual points."""
    glBegin(GL_POINTS)
    glColor3f(0.8, 0.1, 0.5)
    for i in range(8):
        angle = 2.0 * math.pi * i / 8
        glVertex3f(1.8 * math.cos(angle), 1.8 * math.sin(angle), 0.0)
    glEnd()

# ============================================================
# 3. DISPLAY CALLBACK
# ============================================================
def display():
    """Main rendering function - called every frame."""
    global rotation_angle

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Set camera
    gluLookAt(
        0, 0, 8,       # Eye position
        0, 0, 0,       # Look-at target
        0, 1, 0        # Up vector
    )

    # Draw axes (no rotation)
    draw_axes()

    # --- Object 1: Rotating triangle (center) ---
    glPushMatrix()
    glRotatef(rotation_angle, 0, 0, 1)      # Rotate around Z
    draw_triangle()
    glPopMatrix()

    # --- Object 2: Translated + scaled quad (right) ---
    glPushMatrix()
    glTranslatef(3.0, 0.0, 0.0)             # Move right
    glScalef(0.7, 0.7, 0.7)                 # Scale down
    glRotatef(-rotation_angle * 0.5, 0, 1, 0)  # Slow Y rotation
    draw_quad()
    glPopMatrix()

    # --- Object 3: Circle (left) ---
    glPushMatrix()
    glTranslatef(-3.0, 0.0, 0.0)
    glRotatef(rotation_angle * 0.3, 0, 0, 1)
    draw_circle(1.0)
    glPopMatrix()

    # --- Object 4: Points ring ---
    glPushMatrix()
    glRotatef(rotation_angle * 0.2, 0, 0, 1)
    draw_points()
    glPopMatrix()

    # Draw info text
    draw_text(10, 580, "IT516 - Python OpenGL Demo")
    draw_text(10, 558, "[Space] Toggle rotation  [R] Reset  [Esc] Quit")
    draw_text(10, 536, f"Angle: {rotation_angle:.1f} deg")

    glutSwapBuffers()

# ============================================================
# 4. TEXT RENDERING
# ============================================================
def draw_text(x, y, text):
    """Draw 2D text overlay on screen."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    w = glutGet(GLUT_WINDOW_WIDTH)
    h = glutGet(GLUT_WINDOW_HEIGHT)
    glOrtho(0, w, 0, h, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.2, 0.2, 0.2)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ============================================================
# 5. RESHAPE CALLBACK
# ============================================================
def reshape(w, h):
    """Handle window resize."""
    if h == 0:
        h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, w / h, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

# ============================================================
# 6. KEYBOARD CALLBACK
# ============================================================
def keyboard(key, x, y):
    """Handle keyboard input."""
    global auto_rotate, rotation_angle
    if key == b'\x1b':          # Escape
        sys.exit(0)
    elif key == b' ':           # Space - toggle rotation
        auto_rotate = not auto_rotate
    elif key == b'r' or key == b'R':   # Reset
        rotation_angle = 0.0
        auto_rotate = True

# ============================================================
# 7. TIMER CALLBACK (animation)
# ============================================================
def timer(value):
    """Update rotation angle for animation."""
    global rotation_angle
    if auto_rotate:
        rotation_angle += 1.0
        if rotation_angle >= 360.0:
            rotation_angle -= 360.0
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)     # ~60 FPS

# ============================================================
# 8. MAIN
# ============================================================
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"IT516 - Python OpenGL Demo")

    init()

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutTimerFunc(16, timer, 0)

    print("=== IT516 Python OpenGL Demo ===")
    print("Controls:")
    print("  Space  - Toggle auto-rotation")
    print("  R      - Reset angle")
    print("  Esc    - Quit")

    glutMainLoop()

if __name__ == "__main__":
    main()
