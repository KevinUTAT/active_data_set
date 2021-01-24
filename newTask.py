import sys
from os import listdir, system, execl
import os.path
import PySide2
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QPushButton, 
                            QLineEdit, QFileDialog)
from PySide2.QtCore import QFile, QObject, QRectF, Qt
from PySide2.QtGui import (QIcon, QPixmap, QImage, QCursor, QKeySequence)
import json


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


    def create_task(self):
        output = json.loads("{}")
        # data location
        output["Data Location"] = self.data_location
        # yaml location
        output["Yaml Location"] = self.yaml_location
        # finished data
        output["Finished Data"] = []

        with open(self.task_location, 'w') as outFile:
            outFile.write(json.dumps(output, indent=4))
        self.window.close()



if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    form = NewTask('newtaskwindow.ui')
    sys.exit(app.exec_())