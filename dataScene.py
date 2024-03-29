import sys
from os import listdir, system, execl
import os.path
import copy
import PySide2
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QPushButton, 
                            QLineEdit, QPlainTextEdit, QComboBox, 
                            QCheckBox, QAction, QFileDialog, 
                            QMessageBox, QInputDialog, QListWidget, 
                            QListView, QGraphicsScene, QGraphicsView, 
                            QProgressDialog)
from PySide2.QtCore import QFile, QObject, QRectF, Qt
from PySide2.QtGui import (QIcon, QPixmap, QImage)

from PIL import Image
from bbox import BBox
from ADS_config import (label_table, modification_list, IMG_FOLDER, 
                        IMG_EXT, LEBEL_FOLDER, DEFAULT_CLS)
import ADS_config


# A DataScene handles the displaying of a single data (a image and a lable file)
class DataScene(object):

    def __init__(self, viewerScene, viewerView, targetList, \
        ui_form, data_name='', current_data_dir='', cls_map={}):
        self.viewerScene = viewerScene
        self.viewerView = viewerView
        self.targetList = targetList
        self.ui_form = ui_form
        self.data_name = data_name
        self.current_data_dir = current_data_dir

        self.last_cls = ADS_config.DEFAULT_CLS

        self.cls_map = cls_map

        self.img_dir = self.current_data_dir + IMG_FOLDER \
            + '/' + data_name + '.' + IMG_EXT
        self.label_dir = self.current_data_dir + LEBEL_FOLDER \
            + '/' + data_name + '.' + 'txt'

    def show(self, highlight=-1):
        # load viwer and the target list
        self.viewerScene.clear()
        self.img = QPixmap(self.img_dir)
        w, h = self.img.size().toTuple()
        self.backgroundSize = [w, h]
        self.viewerScene.addPixmap(self.img)

        # reinitialize the target list
        self.targetList.clear()
        # self.rmTargetButton.setEnabled(False)
        self.targetList_modified = False

        for i, one_box in enumerate(label_table[self.data_name]):
            if highlight == i:
                one_box.drew_in_scene(self.viewerScene, self, i, \
                    highlight=True)
            else:
                one_box.drew_in_scene(self.viewerScene, self, i)
            
            if len(self.cls_map) >= (one_box.cls + 1):
                cls_label = f"{str(one_box.cls)}\t{self.cls_map[one_box.cls]}"
                newItem = QtWidgets.QListWidgetItem(cls_label)
            else:
                newItem = QtWidgets.QListWidgetItem(str(one_box.cls))
            self.targetList.addItem(newItem)

        self.viewerView.fitInView(QRectF(0, 0, w, h), Qt.KeepAspectRatio)
        self.viewerScene.update()



    def update_viewer(self, highlight=-1):
        # Same as load_viewer but without loading the target list
        self.viewerScene.clear()
        img = QPixmap(self.img_dir)
        w, h = img.size().toTuple()
        self.viewerScene.addPixmap(img)
        for i, one_box in enumerate(label_table[self.data_name]):
            if highlight == i:
                one_box.drew_in_scene(self.viewerScene, self, i, \
                    highlight=True)
            else:
                one_box.drew_in_scene(self.viewerScene, self, i)
        self.viewerView.fitInView(QRectF(0, 0, w, h), Qt.KeepAspectRatio)
        self.viewerScene.update()


    def edit_target_class(self, target_idx=-1):
        # findout which target is selected first
        if target_idx < 0:
            target_idx = self.targetList.currentRow()
        
        # if yaml is provided (ex: in task)
        if len(self.cls_map) > 0:
            class_list = []
            for cls_idx, cls_name in self.cls_map.items():
                class_list.append(f"{cls_idx}-{cls_name}")
            # show a dialog
            dialog = QInputDialog()
            label_text = "Input the correct class number.\n"\
                "Please note your input will not be checked for legality"
            item, okPressed = \
                QInputDialog.getItem(dialog, \
                "Edit class", \
                label_text, \
                class_list, False)
            # print(text, okPressed)
            if okPressed and item:
                cur_bbox = label_table[self.data_name][target_idx]
                old_bbox = BBox(cur_bbox.xywh, cur_bbox.imgSizeWH, cur_bbox.cls)
                class_idx = item.split('-')[0] 
                label_table[self.data_name][target_idx].cls = int(class_idx)
                self.last_cls = int(class_idx)
                # log the change
                new_data = label_table[self.data_name][target_idx].to_label_str()
                # print(new_data)
                mod = [self.data_name, target_idx, new_data, old_bbox]
                modification_list.append(mod)
                self.ui_form.check_undoable()
                self.show()
        else:
            dialog = QInputDialog()
            label_text = "Input the correct class number.\n"\
                "Please note your input will not be checked for legality"
            text, okPressed = \
                QInputDialog.getText(dialog, \
                "Edit class", \
                label_text, \
                QLineEdit.Normal)

            if okPressed and text != '':
                cur_bbox = label_table[self.data_name][target_idx]
                old_bbox = BBox(cur_bbox.xywh, cur_bbox.imgSizeWH, cur_bbox.cls)
                label_table[self.data_name][target_idx].cls = int(text)
                self.last_cls = int(text)
                # log the change
                new_data = label_table[self.data_name][target_idx].to_label_str()
                # print(new_data)
                mod = [self.data_name, target_idx, new_data, old_bbox]
                modification_list.append(mod)
                self.ui_form.check_undoable()
                self.show()


    def record_target_pos(self, target_idx):
        # record edit made localy in scene
        new_line = label_table[self.data_name][target_idx].to_label_str()
        old_bbox = label_table[self.data_name][target_idx].restore_pt
        mod = [self.data_name, target_idx, new_line, old_bbox]
        modification_list.append(mod)
        self.ui_form.check_undoable()


    def record_new_target(self, new_bbox):
        # add new bbox to label atbel
        label_table[self.data_name].append(new_bbox)
        new_bbox.target_idx = len(label_table[self.data_name]) - 1
        # add to mod list
        new_line = new_bbox.to_label_str()
        mod = [self.data_name, new_bbox.target_idx, new_line, None]
        modification_list.append(mod)
        self.ui_form.check_undoable()
        # update dscene
        self.show()



