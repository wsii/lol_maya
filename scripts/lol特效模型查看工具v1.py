import sys
import os

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

class SCBFileSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 创建垂直布局
        layout = QVBoxLayout()

        # 创建选择目录按钮
        self.select_dir_button = QPushButton('选择目录')
        self.select_dir_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_dir_button)

        # 创建导出按钮
        self.export_button = QPushButton('导出')
        self.export_button.clicked.connect(self.export_files)
        layout.addWidget(self.export_button)

        # 创建列表控件
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        # 设置布局
        self.setLayout(layout)
        self.setWindowTitle('SCB 文件选择器')
        self.setGeometry(300, 300, 400, 300)

    def select_directory(self):
        # 打开目录选择对话框
        directory = QFileDialog.getExistingDirectory(self, '选择目录')
        if directory:
            # 清空列表
            self.list_widget.clear()
            # 获取目录下的 .scb 文件
            scb_files = [f for f in os.listdir(directory) if f.endswith('.scb')]
            for file in scb_files:
                self.list_widget.addItem(file)

    def on_item_clicked(self, item):
        # 输出点击的列表项对应的文件完整路径
        file_name = item.text()
        file_path = os.path.join(self.selected_directory, file_name)
        print(file_path)
    

def run():
    global custom_wnd
    try:
        custom_wnd.close()
        custom_wnd.deleteLater()
    except:
        pass
    custom_wnd = SCBFileSelector()
    # 窗口置顶
    custom_wnd.setWindowFlags(Qt.WindowStaysOnTopHint)
    custom_wnd.show()

if __name__ == '__main__':
    run()