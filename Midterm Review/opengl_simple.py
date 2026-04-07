"""Minimal Python OpenGL - IT516"""
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math, sys

angle = 0.0

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    gluLookAt(0,0,5, 0,0,0, 0,1,0)

    # Axes
    glBegin(GL_LINES)
    glColor3f(1,0,0); glVertex3f(0,0,0); glVertex3f(2,0,0)  # X
    glColor3f(0,1,0); glVertex3f(0,0,0); glVertex3f(0,2,0)  # Y
    glColor3f(0,0,1); glVertex3f(0,0,0); glVertex3f(0,0,2)  # Z
    glEnd()

    # Rotating triangle
    glPushMatrix()
    glRotatef(angle, 0, 0, 1)
    glBegin(GL_TRIANGLES)
    glColor3f(1,0,0); glVertex3f(-1,-0.7, 0)
    glColor3f(0,1,0); glVertex3f( 1,-0.7, 0)
    glColor3f(0,0,1); glVertex3f( 0, 0.9, 0)
    glEnd()
    glPopMatrix()

    # Translated quad
    glPushMatrix()
    glTranslatef(2.5, 0, 0)
    glScalef(0.5, 0.5, 0.5)
    glBegin(GL_QUADS)
    glColor3f(1,0.6,0)
    glVertex3f(-1,-1,0); glVertex3f(1,-1,0)
    glVertex3f(1,1,0);   glVertex3f(-1,1,0)
    glEnd()
    glPopMatrix()

    # Circle
    glPushMatrix()
    glTranslatef(-2.5, 0, 0)
    glColor3f(0.2,0.2,0.2)
    glBegin(GL_LINE_LOOP)
    for i in range(64):
        a = 2*math.pi*i/64
        glVertex3f(math.cos(a), math.sin(a), 0)
    glEnd()
    glPopMatrix()

    glutSwapBuffers()

def timer(v):
    global angle
    angle += 1
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45, w/max(h,1), 0.1, 50)
    glMatrixMode(GL_MODELVIEW)

glutInit(sys.argv)
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(800, 600)
glutCreateWindow(b"IT516 OpenGL Demo")
glClearColor(0.95, 0.95, 0.95, 1)
glEnable(GL_DEPTH_TEST)
glutDisplayFunc(display)
glutReshapeFunc(reshape)
glutTimerFunc(16, timer, 0)
glutMainLoop()
