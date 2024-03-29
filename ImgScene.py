import sys
from os import listdir, system, execl
import os.path
import PySide2
import copy
from PySide2.QtWidgets import (QGraphicsScene)
from PySide2.QtGui import (QBrush, QPen, QFont)
from PySide2.QtCore import QLineF, QPointF, Qt
from bbox import BBox


class ImgScene(QGraphicsScene):

    def __init__(self, parent):
        super().__init__(parent)
        
        # internal flags for mouse event sync
        self.mouseDown = False
        self.targetCreated = False
        self.mouseEventHandled = False
        self.newBboxes = []


    def set_dataScene(self, dscene_ref):
        self.dscene = dscene_ref


    # To correctly capture a click and drag event
    # we need to intercept the floowing three events

    def mousePressEvent(self, event):
        self.mouseEventHandled = False
        super().mousePressEvent(event)
        if (event.button() == Qt.LeftButton) \
            and (not self.mouseEventHandled):
            self.mouseDown = True
        self.mouseEventHandled = False

        # print(type(self.height()))
        # print(self.height())


    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        x = event.scenePos().x()
        y = event.scenePos().y()
        # at the begaining of a click & drag: create a new bbox
        if self.mouseDown and (not self.targetCreated):
            # if started outside the img, don't create nothing
            if (0 > x) or (0 > y) or (x > self.dscene.backgroundSize[0]) \
                or (y > self.dscene.backgroundSize[1]):
                self.mouseDown = False
                return
            newBbox = BBox([x, y, 0, 0],
                        self.dscene.backgroundSize,
                        self.dscene.last_cls)
            newBbox.drew_in_scene(self, self.dscene, -1)
            newBbox.br.mouseMoveEvent(event, \
                passed_by_scene=True)
            self.newBboxes.append(newBbox)
            self.targetCreated = True
        # a new bbox is already created for this click & drag action
        # pass the mouse event to the botton right ancker so a bbox 
        # can be dragged out
        elif self.mouseDown:
            self.newBboxes[-1].br.mouseMoveEvent(event, \
                passed_by_scene=True)


    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # if a new bbox was dragged out, save it 
        if self.mouseDown and self.targetCreated:
            self.mouseDown = False
            self.targetCreated = False
            self.newBboxes[-1].update(verify=True)
            self.dscene.record_new_target(self.newBboxes[-1])
        else:
            self.mouseDown = False


