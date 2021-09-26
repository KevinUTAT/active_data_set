from PySide2.QtCore import (QFile, QObject, QRectF, 
                            Qt, Slot)
from PySide2.QtWidgets import QMainWindow, QMessageBox
from ADS_config import (label_table, modification_list, IMG_FOLDER, 
                        IMG_EXT, LEBEL_FOLDER, DEFAULT_CLS)

# provide the main user interface of the program
class InterfaceWindow(QMainWindow):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent, flags)

    
    def closeEvent(self, event):
        # print(self.exit_prompt())
        if len(modification_list) == 0:
            event.accept()
        elif self.exit_prompt() == QMessageBox.Ok:
            event.accept()
        else:
            event.ignore()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reload_view()


    def set_reload_ref(self, reload_ref):
        self.reload_view = reload_ref

    
    def exit_prompt(self):
        error_window = QMessageBox()
        error_window.setIcon(QMessageBox.Warning)
        error_window.setText("You have unsaved modifications, are you sure to exit?")
        error_window.setWindowTitle("Exit")
        error_window.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return error_window.exec_()