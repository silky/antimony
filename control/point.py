from PySide import QtCore, QtGui

import base

class PointControl(base.NodeControl):

    @classmethod
    def new(cls, canvas, x, y, scale):
        """ Construct a new point at the given location
            Location should be specified in units.
        """
        p = Point(get_name('p'), x, y)
        cls(canvas, p)

    def __init__(self, canvas, target):
        super(PointControl, self).__init__(canvas, target)
        self.setFixedSize(30, 30)

        self.dragging = False
        self.hovering = False
        self.make_mask()
        self.sync()
        self.show()
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.delete()
        elif event.button() == QtCore.Qt.LeftButton:
            self.mouse_pos = self.mapToParent(event.pos())
            self.dragging = True

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.open_editor()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False

    def mouseMoveEvent(self, event):
        p = self.mapToParent(event.pos())
        if self.dragging:
            delta = p - self.mouse_pos
            scale = self.parentWidget().scale
            self.drag(delta.x() / scale, -delta.y() / scale)
        elif not self.hovering:
            self.hovering = True
            self.update()
        self.mouse_pos = p

    def leaveEvent(self, event):
        self.hovering = False
        self.update()

    def drag(self, dx, dy):
        """ Drag this node by attempting to change its x and y coordinates
            dx and dy should be floating-point values.
        """
        if self.node._x.simple():
            self.node._x.set_expr(str(float(self.node._x.get_expr()) + dx))
        if self.node._y.simple():
            self.node._y.set_expr(str(float(self.node._y.get_expr()) + dy))


    def sync(self):
        """ Move this control to the appropriate position.
            Use self.position (cached) if eval fails.
        """
        try:    x = self.node.x
        except: x = self.position.x()

        try:    y = self.node.y
        except: y = self.position.y()

        self.move(self.canvas.mm_to_pixel(x=x) - self.width()/2,
                  self.canvas.mm_to_pixel(y=y) - self.height()/2)

        self.position = QtCore.QPointF(x, y)

        if self.editor:     self.editor.sync()


    def paintEvent(self, paintEvent):
        """ On paint event, paint oneself.
        """
        self.paint(QtGui.QPainter(self))

    def paint(self, qp, mask=False):
        """ Paint either the point or a mask for the point.
        """
        width, height = self.width(), self.height()
        light = (200, 200, 200)
        dark  = (100, 100, 100)

        if mask:
            qp.setBrush(QtGui.QBrush(QtCore.Qt.color1))
            qp.setPen(QtGui.QPen(QtCore.Qt.color1, 2))
        else:
            qp.setBrush(QtGui.QBrush(QtGui.QColor(*light)))
            qp.setPen(QtGui.QPen(QtGui.QColor(*dark), 2))

        if mask:                                d = 22
        elif self.hovering or self.dragging:    d = 20
        else:                                   d = 14

        qp.drawEllipse((width - d) / 2, (height - d) / 2, d, d)

    def make_mask(self):
        """ Render a mask and set it to this widget's mask.
        """
        painter = QtGui.QPainter()
        bitmap = QtGui.QBitmap(self.size())
        bitmap.clear()

        painter.begin(bitmap)
        self.paint(painter, True)
        painter.end()

        self.setMask(bitmap)

################################################################################

class ChildPointControl(PointControl):
    """ Represents a point that is part of another shape
        (so it deletes its parent along with itself)
    """
    def __init__(self, canvas, target, parent):
        super(ChildPointControl, self).__init__(canvas, target)
        self.parent = parent

    def mousePressEvent(self, event):
        """ Delete the parent as well on a right-click event.
        """
        if event.button() == QtCore.Qt.RightButton:
            self.parent.delete(self)
        super(ChildPointControl, self).mousePressEvent(event)

from node.base import get_name
from node.point import Point