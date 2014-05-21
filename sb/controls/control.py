from PySide import QtCore, QtGui
from sb.datum import Datum

class Control(QtGui.QGraphicsObject):

    center_changed = QtCore.Signal(QtCore.QPoint)

    def __init__(self, canvas, node=None):
        super(Control, self).__init__()

        self.setFlags(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        self.setAcceptHoverEvents(True)

        self._canvas = canvas
        self._canvas.scene.addItem(self)

        self._hover = False
        self._dragged = False

        canvas.zoomed.connect(self.prepareGeometryChange)
        canvas.rotated.connect(self.prepareGeometryChange)

        self._node = node
        if self._node is not None:
            # When the node changes, inform the scene that our bounding box
            # has changed, force a canvas redraw, and update the center
            # for any node viewers that may have been created.
            self._node.changed.connect(self.prepareGeometryChange)
            self._node.changed.connect(self._canvas.update)
            self._node.changed.connect(self.update_center)

            # Where there's a node, there could be a node viewer, so
            # call all of the node viewer functions when the view changes.
            canvas.rotated.connect(self.update_center)
            canvas.zoomed.connect(self.update_center)
            canvas.panned.connect(self.update_center)

            # Finally, when the node is destroyed, delete ourself.
            self._node.destroyed.connect(self.deleteLater)

    def delete_node(self):
        """ Schedules the node for deletion
            (which will also delete oneself).
        """
        self._node.deleteLater()

    @property
    def matrix(self):
        return self._canvas.matrix

    def transform_points(self, points):
        """ Transforms a list of QVector3Ds (in world coordinates), returning
            a list of QPointFs in scene coordinates.
        """
        m = self.matrix
        t = [m * p for p in points]
        return [QtCore.QPointF(p.x(), p.y()) for p in t]

    def itransform_points(self, points):
        """ Transforms a list of QPointFs in scene coordinates, returning
            a list of QVector3Ds in world coordinates.
        """
        m = self.matrix.inverted()[0]
        return [m * QtGui.QVector3D(t) for t in points]

    def bounding_box(self, points, padding=10):
        """ Returns a QRectF representing the bounding box (in scene coordinates)
            of the given set of points (which are in world coordinates).
        """
        pts = self.transform_points(points)
        xmin = min(p.x() for p in pts)
        ymin = min(p.y() for p in pts)
        xmax = max(p.x() for p in pts)
        ymax = max(p.y() for p in pts)
        return QtCore.QRectF(xmin - padding, ymin - padding,
                             xmax - xmin + 2*padding, ymax - ymin + 2*padding)

    def hoverEnterEvent(self, event):
        if not self._hover:
            self._hover = True
            self.update()

    def hoverLeaveEvent(self, event):
        if self._hover:
            self._hover = False
            self.update()

    def mouseDoubleClickEvent(self, event):
        v = NodeViewer(self)
        self.update_center()
        return v

    def mousePressEvent(self, event):
        """ Saves a mouse click position (in scene coordinates) to
            self._mouse_click_pos
        """
        self._dragged = False
        self._mouse_click_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """ On mouse release, call ungrabMouse (only matters after initial
            construction, when the control called grabMouse, but does no
            harm here).
        """
        if not self._dragged:
            self.setSelected(True)
        self.ungrabMouse()

    def mouseMoveEvent(self, event):
        """ On mouse move, call self.drag with the given drag
            (in world coordinates).
        """
        drag = event.pos() - self._mouse_click_pos
        d = self.itransform_points([drag])[0]
        self.drag(d)
        self._mouse_click_pos = event.pos()
        self._dragged = True


from sb.ui.viewer import NodeViewer
