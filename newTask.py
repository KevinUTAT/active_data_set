import sys
from os import listdir, system, execl
import os.path
import os
import PySide2
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QPushButton, 
                            QLineEdit, QFileDialog, QLabel)
from PySide2.QtCore import QFile, QObject, QRectF, Qt
from PySide2.QtGui import (QIcon, QPixmap, QImage, QCursor, QKeySequence)
import json
from ADS_config import label_table, modification_list, IMG_FOLDER, IMG_EXT, LEBEL_FOLDER


class NewTask(QObject):

    def __init__(self, ui_file, parent=None):
        super(NewTask, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # Set location of tsak file
        self.window.findChild(QPushButton, 'buttonName').\
            clicked.connect(self.task_location_finder)

        # Set location of datas
        self.window.findChild(QPushButton, 'buttonData').\
            clicked.connect(self.data_location_finder)

        # Set location of yaml
        self.window.findChild(QPushButton, 'buttonYaml').\
            clicked.connect(self.yaml_location_finder)

        # create task
        self.window.findChild(QPushButton, 'buttonCreate').\
            clicked.connect(self.create_task)

        # error msg s
        self.task_error = self.window.findChild(QLabel, 'task_errmsg')
        self.task_error.setHidden(True)
        self.data_error = self.window.findChild(QLabel, 'data_errmsg')
        self.data_error.setHidden(True)
        self.yaml_error = self.window.findChild(QLabel, 'yaml_errmsg')
        self.yaml_error.setHidden(True)


    def show(self):
        self.window.show()


    def task_location_finder(self):
        (self.task_location, ext) = QFileDialog.getSaveFileName(\
            filter="JSON files (*.json)")
        self.window.findChild(QLineEdit, 'lineName').\
            setText(self.task_location)


    def data_location_finder(self):
        self.data_location = QFileDialog.getExistingDirectory()
        self.window.findChild(QLineEdit, 'lineData').\
            setText(self.data_location)


    def yaml_location_finder(self):
        (self.yaml_location, ext) = QFileDialog.getOpenFileName(\
            filter="YAML files (*.yaml)")
        self.window.findChild(QLineEdit, 'lineYaml').\
            setText(self.yaml_location)

    def get_infos(self):
        self.task_location = \
            self.window.findChild(QLineEdit, 'lineName').text()
        self.data_location = \
            self.window.findChild(QLineEdit, 'lineData').text()
        self.yaml_location = \
            self.window.findChild(QLineEdit, 'lineYaml').text()


    def create_task(self):
        self.get_infos()
        output = json.loads("{}")
        # data location
        if self.valid_data_location() == "":
            output["Data Location"] = self.data_location
        else:
            self.data_error.setText(self.valid_data_location())
            self.data_error.setHidden(False)
            return
        # yaml location
        if os.path.exists(self.yaml_location):
            self.yaml_error.setHidden(True)
            output["Yaml Location"] = self.yaml_location
        else:
            self.yaml_error.setText("Can't find yaml file")
            self.yaml_error.setHidden(False)
            return
        # finished data
        output["Finished Data"] = []

        # output json file
        if not os.path.exists(self.task_location):
            self.task_error.setHidden(True)
            with open(self.task_location, 'w') as outFile:
                outFile.write(json.dumps(output, indent=4))
            self.window.close()
        else:
            self.task_error.setText("Task already exist")
            self.task_error.setHidden(False)


    def valid_data_location(self):
        if not os.path.exists(self.data_location):
            return "Path Not Exist"
        if not os.path.exists(self.data_location + IMG_FOLDER):
            return "No Image Folder found"
        # its ok if no lable folder found, we create an empty one
        if not os.path.exists(self.data_location + LEBEL_FOLDER):
            os.mkdir(self.data_location + LEBEL_FOLDER)
        self.data_error.setHidden(True)
        return ""




if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    form = NewTask('newtaskwindow.ui')
    sys.exit(app.exec_())