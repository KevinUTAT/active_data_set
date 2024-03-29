import sys
from os import listdir, system, execl
import os.path
import PySide2

# # this following is hard coded env switch only for pyinstaller
# # The python script will run with or with or without it
# plugin_path = "dep/platforms"
# os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QPushButton, 
                            QLineEdit, QPlainTextEdit, QComboBox, 
                            QCheckBox, QAction, QFileDialog, 
                            QMessageBox, QInputDialog, QListWidget, 
                            QListView, QGraphicsScene, QGraphicsView, 
                            QProgressDialog, QShortcut)
from PySide2.QtCore import QFile, QObject, QRectF, Qt, Slot
from PySide2.QtGui import (QIcon, QPixmap, QImage, QCursor, 
                            QKeySequence, QBrush,  QColor)
from PIL import Image
import shutil
import yaml
from bbox import BBox
from dataScene import DataScene
from ADS_config import (label_table, modification_list, IMG_FOLDER, 
                        IMG_EXT, LEBEL_FOLDER, DEFAULT_CLS)
import ADS_config
from ImgScene import ImgScene
import train_val_spliter
import rename
from newTask import NewTask
from task import Task
from interfacewindow import InterfaceWindow
import label_health
# import detect


class Form(QObject):
    
    def __init__(self, ui_file, parent=None):
        super(Form, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        
        loader = QUiLoader()
        loader.registerCustomWidget(InterfaceWindow)
        self.window = loader.load(ui_file)
        ui_file.close()
        self.window.set_reload_ref(self.reload_viewer)

        

        # system flags
        self.current_data_dir = "."

        # new task window
        self.in_task = False # indicating its currently performing a Task
        self.newTaskWin = NewTask(ui_file='newtaskwindow.ui')

        # Menu actions ==================================================
        # Load ADS action
        self.window.findChild(QAction, 'loadAOAction').\
            triggered.connect(self.load_adc)
        
        # Load from video
        self.window.findChild(QAction, 'actionFrom_Video').\
            triggered.connect(self.get_active_from_video)
        self.window.findChild(QAction, 'actionFrom_Video').\
            setEnabled(False)

        # load save target mod action
        self.window.findChild(QAction, 'actionTarget_Modifications').\
            triggered.connect(self.save_mods)

        # show change history
        self.window.findChild(QAction, 'actionView_history').\
            triggered.connect(self.show_mods)
        
        # save active data to ..
        self.window.findChild(QAction, 'actionActive_data_to').\
            triggered.connect(self.save_active_to)

        # Tools -----------
        # data spliter
        self.window.findChild(QAction, 'actionData_spliter').\
            triggered.connect(self.run_spliter)
        # renamer
        self.window.findChild(QAction, 'actionRename').\
            triggered.connect(self.run_rename)

        # check labels
        self.window.findChild(QAction, 'actionCheck_Labels').\
            triggered.connect(self.check_labels_integrity)

        # set defult class
        self.window.findChild(QAction, 'actionset_defult_class').\
            triggered.connect(self.set_defult_class)

        # For task ------------------------------------------------------

        self.window.findChild(QAction, 'actionNewTask').\
            triggered.connect(self.new_task)

        self.window.findChild(QAction, 'actionOpenTask').\
            triggered.connect(self.open_task)

        # Data list =====================================================
        self.dataList = \
            self.window.findChild(QListWidget, 'dataList')
        self.dataList.setViewMode(QListView.IconMode)
        self.dataList.setIconSize(PySide2.QtCore.QSize(128, 72))
        self.dataList.itemSelectionChanged.connect(self.load_viewer)
        self.dataList.itemDoubleClicked.connect(self.double_click_data)

        # Data Viewer ===================================================
        self.viewerScene = ImgScene(self)
        self.viewerView = self.window.findChild(QGraphicsView, 'dataViewer')
        self.viewerView.setScene(self.viewerScene)
        self.viewerView.setCursor(QCursor(PySide2.QtCore.Qt.CrossCursor))

        # Targets list ==================================================
        self.targetList = \
            self.window.findChild(QListWidget, 'targetList')
        self.targetList.itemClicked.connect(self.hightlight_target)
        # self.current_dataScene = DataScene(self.viewerScene, \
        #     self.viewerView, self.targetList)
        # self.targetList.itemDoubleClicked.connect(\
        #     self.current_dataScene.edit_target_class)

        # editing buttons ===============================================
        self.rmTargetButton = \
            self.window.findChild(QPushButton, 'rmTargetButton')
        self.undoButton = \
            self.window.findChild(QPushButton, 'undoButton')
        self.editButton = \
            self.window.findChild(QPushButton, 'editButton')
        self.deleteButton = \
            self.window.findChild(QPushButton, 'deleteButton')

        self.editButton_connected = False # make sure only connect once

        self.rmTargetButton.setEnabled(False)
        self.undoButton.setEnabled(False)
        self.rmTargetButton.clicked.connect(\
            lambda state=0, x=-1:\
            self.remove_target(x))
        self.targetList_modified = False
        self.undoButton.clicked.connect(self.undo_mod)
        self.deleteButton.clicked.connect(self.remove_img)

        # shortcuts ====================================================
        QShortcut(QKeySequence("Ctrl+R"), self.window).activated.\
            connect(lambda state=0, x=-1: self.remove_target(x))

        self.window.show()


    # Load active data set from a window
    def load_adc(self):
        self.class_map = {}
        self.adc_folder_dir = QFileDialog.getExistingDirectory()
        self.load_dataset(self.adc_folder_dir)


    # load from existing self.adc_folder_dir
    def load_dataset(self, ds_dir):
        self.class_map = {}
        self.adc_folder_dir = ds_dir
        if (not os.path.exists(self.adc_folder_dir + IMG_FOLDER)) \
            or (not os.path.exists(self.adc_folder_dir + LEBEL_FOLDER)):
            self.error_msg("Cannot find proper data in " + self.adc_folder_dir \
                + '\n' + "A proper data folder should have subfolders: " \
                + IMG_FOLDER + " and " + LEBEL_FOLDER)
            self.adc_folder_dir = ""
            return
        name_list = []
        for imgName in os.listdir(self.adc_folder_dir + IMG_FOLDER):
            dataName = imgName.split('.')[0] # remove extension
            name_list.append(dataName)
        self.current_data_dir = self.adc_folder_dir
        label_table.clear()
        modification_list.clear()
        self.load_dataList(name_list)
        

    def load_dataList(self, nameList ,showThumbnail=True, progressBar=True):
        self.dataList.clear()
        if progressBar:
            progress = QProgressDialog("Loading data...", "Abort", \
                0, len(nameList), self.window)
            progress.setWindowModality(Qt.WindowModal)
        for i, dataName in enumerate(nameList):
            newItem = QtWidgets.QListWidgetItem(dataName)
            # Mark finished data
            if self.in_task and (dataName in self.current_task.finished_data):
                newItem.setBackground(QBrush(QColor("#b3b3b3")))
            
            if showThumbnail:
                # boring img down sizing and img format converting
                img = Image.open(self.current_data_dir + IMG_FOLDER \
                    + '/' + dataName + '.' + IMG_EXT)
                w, h = img.size
                img = img.resize((128, int(128*h/w)))
                img = img.convert("RGBA")
                qimg = QImage(img.tobytes('raw', 'RGBA'), img.size[0], \
                    img.size[1], QImage.Format_RGBA8888)
                thumbnail = QIcon()
                thumbnail.addPixmap(QtGui.QPixmap.fromImage(qimg))
                newItem.setIcon(thumbnail)

            # pre load all the labels
            label_dir = self.current_data_dir + LEBEL_FOLDER \
                + '/' + dataName + '.txt'
            if os.path.exists(label_dir):
                with open(label_dir, 'r') as label_file:
                    bboxs = []
                    for line in label_file:
                        bbox_l = line.split()
                        class_num = int(bbox_l[0])
                        centerX = int(float(bbox_l[1]) * w)
                        centerY = int(float(bbox_l[2]) * h)
                        width = int(float(bbox_l[3]) * w)
                        height = int(float(bbox_l[4]) * h)
                        new_bbox = BBox([centerX, centerY, width, height],\
                                [w, h], class_num)
                        bboxs.append(new_bbox)

                    label_table[dataName] = bboxs
            else:
                # self.error_msg("Cannot find label: " + \
                #     label_dir)
                # if the label do not exist, create an empty bbox list
                bboxs = []
                label_table[dataName] = bboxs
            
            self.dataList.addItem(newItem)
            if progressBar:
                progress.setValue(i)
                if progress.wasCanceled():
                    break
        if progressBar:
                progress.setValue(len(nameList))


    def load_viewer(self, highlight=-1):
        # self.viewerScene.clear()
        data_name = str(self.dataList.currentItem().text())
        # mark as finished
        if self.in_task:
            self.dataList.currentItem().\
                setBackground(QBrush(QColor("#b3b3b3")))
            self.current_task.finish_data(data_name)
        # img_dir = self.current_data_dir + IMG_FOLDER \
        #     + '/' + data_name + '.' + IMG_EXT
        # img = QPixmap(img_dir)
        # w, h = img.size().toTuple()
        # self.viewerScene.addPixmap(img)

        # # reinitialize the target list
        # self.targetList.clear()
        self.rmTargetButton.setEnabled(False)
        # self.targetList_modified = False

        # for i, one_box in enumerate(label_table[data_name]):
        #     if highlight == i:
        #         one_box.drew_in_scene(self.viewerScene, highlight=True)
        #     else:
        #         one_box.drew_in_scene(self.viewerScene)
            
        #     newItem = QtWidgets.QListWidgetItem(str(one_box.cls))
        #     self.targetList.addItem(newItem)
        # self.viewerView.fitInView(QRectF(0, 0, w, h), Qt.KeepAspectRatio)
        # self.viewerScene.update()

        self.current_dataScene = DataScene(self.viewerScene, \
            self.viewerView, self.targetList, self, data_name, \
            self.current_data_dir, self.class_map)
        self.viewerScene.set_dataScene(self.current_dataScene)
        # setup edit trigger (double click or edit button)
        if not self.editButton_connected:
            self.targetList.itemDoubleClicked.connect(\
                lambda state=0, x=-1:\
                self.current_dataScene.edit_target_class(x))
            self.editButton.clicked.connect(\
                lambda state=0, x=-1:\
                self.current_dataScene.edit_target_class(x))
            self.editButton_connected = True
        else:
            self.targetList.itemDoubleClicked.disconnect()
            self.editButton.clicked.disconnect()
            self.targetList.itemDoubleClicked.connect(\
                self.current_dataScene.edit_target_class)
            self.editButton.clicked.connect(\
                self.current_dataScene.edit_target_class)
            self.editButton_connected = True
        self.current_dataScene.show(highlight=highlight)


    def reload_viewer(self, highlight=-1):
        # # Same as load_viewer but without loading the target list
        if hasattr(self, "current_dataScene"):
            self.current_dataScene.update_viewer(highlight=highlight)


    def hightlight_target(self):
        target_idx = self.targetList.currentRow()
        # print(target_idx)
        self.reload_viewer(target_idx)

        self.rmTargetButton.setEnabled(True)


    def remove_target(self, target2rm_idx=-1):
        if target2rm_idx < 0:
            target2rm_idx = self.targetList.currentRow()
        data_name = str(self.dataList.currentItem().text())
        # delete one bbox from label_table[data_name]
        new_bboxs = []
        for i, one_box in enumerate(label_table[data_name]):
            if i != target2rm_idx:
                new_bboxs.append(one_box)
            else:
                del_box = one_box
        label_table[data_name] = new_bboxs

        # record modification
        mod = [data_name, target2rm_idx, '', del_box]
        modification_list.append(mod)

        self.undoButton.setEnabled(True)
        self.load_viewer()


    def remove_img(self, dataname=None):
        # remove a imgage-label pair and mark it for deletion
        old_item_n_label = []
        if not dataname:
            dataname = self.current_dataScene.data_name
            data_idx = self.dataList.currentRow()
            data_item = self.dataList.item(data_idx)
        else:
            data_idx, data_item = self.find_data_by_name(dataname)
        # remove data item form datalist
        self.info_msg("The image and label of: \n"\
            + dataname + "\nwill be mark for deletion\n"\
            + "Deletion will not happen until action: \n"\
            + "Save -> Target modifications")

        if self.dataList.isItemSelected(data_item):
             # focus on a different data 
            if data_idx < (self.dataList.count()-1):
                self.dataList.setCurrentRow(data_idx + 1)
            else:
                self.dataList.setCurrentRow(data_idx - 1)

        old_item_n_label.append((data_idx, data_item))
        self.dataList.takeItem(data_idx)

        # remove from labeltable
        old_item_n_label.append(label_table[dataname])
        del label_table[dataname]

        # mark for deletion
        mod = [dataname, -1, '', old_item_n_label]
        modification_list.append(mod)
        self.undoButton.setEnabled(True)


    def undo_mod(self):
        if len(modification_list) == 0:
            self.undoButton.setEnabled(False)
            return
        last_mod = modification_list[-1]
        data_name = last_mod[0]
        tar_idx = last_mod[1]
        # to undo a data deletion:
        # 1. resore itme in datalist
        # 2. resore label_table
        # 3. (sometimes) update the target and scene
        update = False
        if tar_idx == -1:
            old_idx = last_mod[3][0][0]
            old_item = last_mod[3][0][1]
            old_label = last_mod[3][1]
            self.dataList.insertItem(old_idx, old_item)
            label_table[data_name] = old_label
        else:
            # insert old bbox back if deleted
            # else just restore old bbox
            if last_mod[2] == '':
                label_table[data_name].insert(tar_idx, last_mod[3])
            # to undo a new target:
            # 1. remove from lable table
            # 2. update
            elif last_mod[3] is None:
                del label_table[data_name][tar_idx]
            else:
                label_table[data_name][tar_idx] = last_mod[3]
                update = True
        # then remove this modification form mod list
        del modification_list[-1]

        if len(modification_list) == 0:
            self.undoButton.setEnabled(False)
        self.load_viewer()
        if update:
            label_table[data_name][tar_idx].update()
        

    def save_mods(self):
        for mod in modification_list:
            label_dir = self.current_data_dir + LEBEL_FOLDER \
                    + '/' + mod[0] + '.txt'
            img_dir = self.current_data_dir + IMG_FOLDER \
                    + '/' + mod[0] + '.' + IMG_EXT
            # if the label file don't exist, create an empty file
            if not os.path.exists(label_dir):
                with open(label_dir, 'w'):
                    pass
            # remove a img
            if mod[1] == -1:
                os.remove(img_dir)
                os.remove(label_dir)
            else:
                with open(label_dir, 'r') as label_file:
                    lines = label_file.readlines()
                # do some check on the label file
                if len(lines) > 0:
                    # the last line should end with \n
                    if lines[-1][-1] != '\n':
                        lines[-1] = lines[-1] + '\n'
                    # if its an empty file, its fine
                # remove a target (a line)
                if mod[2] == '':
                    del lines[mod[1]]
                # new target
                elif mod[3] is None:
                    lines.append(mod[2] + '\n')
                else:
                    if len(lines) > mod[1]:
                        lines[mod[1]] = mod[2] + '\n'
                    else:
                        print("ERROR: modify line DNE:")
                        print(mod)
                        print(lines)
                        assert(False)

                with open(label_dir, 'w') as label_file:
                    label_file.writelines(lines)
        modification_list.clear()
        # save the prograss as well
        if self.in_task:
            self.current_task.save_current()


    def show_mods(self):
        table = []
        for mod in modification_list:
            line = ""
            if mod[1] == -1:
                line += "RT: "
            else:
                if mod[2] == '':
                    line += "RI: "
                # new target
                elif mod[3] is None:
                    line += "NT: "
                else:
                    line += "MT: "
            line += str(mod) + '\n'
            table.append(line)
        # add many spaces to make the window wider
        self.info_msg_box(\
            f"Total of {len(table)} modifications:"\
            "                                     "\
            "                                     "\
            "                                     "\
            "                                     ", \
            title="Unsaved Modification", \
            detail_list=table)


    def save_active_to(self):
        dest = QFileDialog.getExistingDirectory()
        if (not os.path.exists(dest + IMG_FOLDER)) \
            or (not os.path.exists(dest + LEBEL_FOLDER)):
            self.error_msg("Cannot find proper data in " + dest \
                + '\n' + "A proper data folder should have subfolders: " \
                + IMG_FOLDER + " and " + LEBEL_FOLDER)
            return
        dest_img_folder = dest + IMG_FOLDER
        dest_label_folder = dest + LEBEL_FOLDER
        for img in os.listdir(self.current_data_dir + IMG_FOLDER):

            source_img = self.current_data_dir + IMG_FOLDER \
                + '/' + img
            dest_img = dest_img_folder + '/' + img

            source_label = self.current_data_dir + LEBEL_FOLDER \
                + '/' + img.split('.')[0] + ".txt"
            dest_label = dest_label_folder + \
                '/' +img.split('.')[0] + ".txt"

            # do some check first:
            # 1. data with the same name not already there
            # 2. label exist for img
            if os.path.exists(dest_img):
                self.error_msg("Image " + dest_img + \
                    " already exist, it will not be moved")
                continue
            if os.path.exists(dest_label):
                self.error_msg("Label " + dest_label + \
                    " already exist, it will not be moved")
                continue
            if not os.path.exists(source_label):
                self.error_msg("The label " + source_label \
                    + " do not exist, data will not be moved")
                continue
            shutil.move(source_img, dest_img)
            shutil.move(source_label, dest_label)


    # Deprecated. Need an outside module to work
    def get_active_from_video(self):
        (source_vid, ext) = QFileDialog.getOpenFileName(\
                filter="Video files (*.mp4 *.avi)")
        # show a dialog
        dialog = QInputDialog()
        label_text = "Input active threshold"
        text, okPressed = \
            QInputDialog.getText(dialog, \
            "Active Threshold", \
            label_text, \
            QLineEdit.Normal)
        if okPressed and text != '':
            active_thr = float(text)
        else:
            active_thr = 0.0
        progress = 0
        progress_bar = QProgressDialog("Detecting Video...", "Abort", \
                0, 100, self.window)
        progress_bar.setWindowModality(Qt.WindowModal)
        progress_bar.setValue(progress)
        detect.run_detect_video(source_vid, progress_bar, active_thr)


    def new_task(self):
        self.newTaskWin.show()

            
    def open_task(self):
        (task_dir, ext) = QFileDialog.getOpenFileName(\
                filter="Task JSON files (*.json)")
        self.start_task(task_dir)


    def start_task(self, task_dir):
        self.current_task = Task(task_dir)
        self.in_task = True
        self.load_dataset(self.current_task.data_location)
        self.load_ymal(self.current_task.yaml_location)


    def load_ymal(self, yaml_location):
        with open(yaml_location, 'r') as yaml_file:
            yaml_doc = yaml.full_load(yaml_file)
        # a mapping of class names
        self.class_map = {}
        for i, name in enumerate(yaml_doc['names']):
            self.class_map[i] = name
        
        
    @Slot(QtWidgets.QListWidgetItem)
    def double_click_data(self, item):
        if self.in_task:
            # make the data unfinished
            self.current_task.mark_as_unfinished(item.text())
            # remove the visual highlight
            item.setBackground(QBrush(QColor("#ffffff")))


    # Tools ++++++++++++++++++++++++++++++++++++++++++++++++++
    def run_spliter(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("The spliter will divide datas "\
             "into training set and validation set")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.addButton(QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Ok)
        ret = msgBox.exec()
        if ret == QMessageBox.Ok:
            train_val_spliter.train_val_split(data_dir=self.adc_folder_dir)
        else:
            return


    def run_rename(self):
        data_folder_dir = QFileDialog.getExistingDirectory()
        if (not os.path.exists(data_folder_dir + IMG_FOLDER)) \
            or (not os.path.exists(data_folder_dir + LEBEL_FOLDER)):
            self.error_msg("Cannot find proper data in " + data_folder_dir \
                + '\n' + "A proper data folder should have subfolders: " \
                + IMG_FOLDER + " and " + LEBEL_FOLDER)
            return
        rename.back_ward_rename(data_folder_dir)


    def check_labels_integrity(self):
        # check for line error
        line_err_list = label_health.check_for_missing_newline(\
            self.adc_folder_dir)
        if len(line_err_list) > 0:
            self.info_msg_box("Error found in labels: missing newline", \
                title="Line error", detail_list=line_err_list)
        # check for out-of-range
        oor_err_list, label_list = label_health.check_out_of_range(\
            self.adc_folder_dir)
        if len(oor_err_list) > 0:
            self.info_msg_box("Error found in labels: out-of-range", \
                title="OOR error", detail_list=oor_err_list)
            # mark error labels red
            for label in label_list:
                self.dataList.findItems(label.split('.')[0], Qt.MatchFlags(0))[0].\
                    setBackground(QBrush(QColor("#ff9999")))



    def set_defult_class(self):
        # if yaml is provided (ex: in task)
        if hasattr(self, 'class_map'):
            class_list = []
            for cls_idx, cls_name in self.class_map.items():
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
                class_idx = int(item.split('-')[0])
                self.current_dataScene.last_cls = class_idx
                ADS_config.DEFAULT_CLS = class_idx
                
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
                self.current_dataScene.last_cls = int(text)
                ADS_config.DEFAULT_CLS = int(text)


    # helpers ++++++++++++++++++++++++++++++++++++++++++++++++
    def find_data_by_name(self, dataname):
        # return the row number and Qlistitem
        for item_idx in range(self.dataList.count()):
            cur_item = self.dataList.item(item_idx)
            if cur_item.text() == dataname:
                return item_idx, cur_item
        return None


    def check_undoable(self):
        if len(modification_list) == 0:
            self.undoButton.setEnabled(False)
        else:
            self.undoButton.setEnabled(True)


    def error_msg(self, error_msg):
        error_window = QMessageBox()
        error_window.setIcon(QMessageBox.Critical)
        error_window.setText(error_msg)
        error_window.setWindowTitle("Error")
        error_window.setStandardButtons(QMessageBox.Ok)
        error_window.exec_()


    def warn_msg(self, warn_msg):
        error_window = QMessageBox()
        error_window.setIcon(QMessageBox.Warning)
        error_window.setText(warn_msg)
        error_window.setWindowTitle("Warning")
        error_window.setStandardButtons(QMessageBox.Ok)
        error_window.exec_()


    def info_msg(self, info_msg, title='Information'):
        error_window = QMessageBox()
        error_window.setIcon(QMessageBox.Information)
        error_window.setText(info_msg)
        error_window.setWindowTitle(title)
        error_window.setStandardButtons(QMessageBox.Ok)
        error_window.exec_()


    # infomation popup with a textbox display an array of detail
    def info_msg_box(self, info_msg, title='Information', detail_list=[]):
        details = ""
        if len(detail_list) > 0:
            for detail in detail_list:
                details += str(detail) + '\n'
        error_window = QMessageBox()
        error_window.setIcon(QMessageBox.Information)
        error_window.setText(info_msg)
        error_window.setWindowTitle(title)
        error_window.setDetailedText(details)
        error_window.setStandardButtons(QMessageBox.Ok)
        error_window.exec_()




    # def load_bbox(self):

        


if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    form = Form('mainwindow.ui')
    sys.exit(app.exec_())