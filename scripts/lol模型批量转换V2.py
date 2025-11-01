import os
import maya.cmds as cmds

from pathlib import Path

from typing import Callable, Optional

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *



def trans2Fbx(input_folder):
    # 定义导入和导出的路径

    # 确保导出文件夹存在
    if not os.path.exists(input_folder):
        # os.makedirs(input_folder)
        pass

    # 获取所有 .scb 文件
    scb_files = [f for f in os.listdir(input_folder) if f.endswith('.scb')]

    # 处理每个 .scb 文件
    for scb_file in scb_files:
        input_path = os.path.join(input_folder, scb_file)

        # 新建场景，清空当前场景
        cmds.file(new=True, force=True)
        
        # 导入 .scb 文件
        try:
            cmds.file(input_path, i=True, type="League of Legends: SCB")
            print(f'Successfully imported {scb_file}')
        except Exception as e:
            print(f'Failed to import {scb_file}: {str(e)}')
            continue

        # 获取导入后的对象
        new_objects = cmds.ls(dag=True)

        # 确保导入有对象，如果没有则跳过
        if new_objects:
            cmds.select(new_objects)
        else:
            print(f'No new objects were imported from {scb_file}.')
            continue
        
                # 获取当前选中的对象
        selected_objects = cmds.ls(selection=True)

        if selected_objects:
            for obj in selected_objects:
                # 确保对象是一个多边形网格
                shape_nodes = cmds.listRelatives(obj, shapes=True, type='mesh')
                if shape_nodes:
                    # 获取对象的所有面
                    faces = cmds.ls(f'{obj}.f[*]', flatten=True)
                    
                    # 反转法线
                    if faces:
                        cmds.polyNormal(faces, normalMode=0)  # normalMode=0 表示反转法线
                        print(f"Reversed normals for {obj}")
                    else:
                        print(f"No faces found on {obj}")
                else:
                    print(f"{obj} is not a polygon mesh.")
        else:
            print("No objects selected.")


        # 定义导出 .fbx 文件的路径
        fbx_file = os.path.splitext(scb_file)[0] + '.fbx'
        output_path = os.path.join(input_folder, fbx_file)
        
        # 导出为 .fbx
        try:
            cmds.file(output_path, force=True, options="v=0", type="FBX export", exportSelected=True)
            print(f'Successfully exported {fbx_file}')
        except Exception as e:
            print(f'Failed to export {fbx_file}: {str(e)}')


class FileChooser(QWidget):
    """
    A custom widget used for selecting a file path using a FileDialog and an input field
    """

    def __init__(
        self,
        label_text: str,
        hint: str,
        parent: Optional[QWidget] = None,
        placeholder: str = "",
        dialog_caption: str = "Select a file",
        dialog_filter: str = "All files (*.*)",
        button_text: str = "...",
        dir_selector: bool = False,
        on_changed: Callable[[int], None] = None,
    ) -> None:
        super().__init__(parent=parent)

        self._dialog_caption = dialog_caption
        self._dialog_filter = dialog_filter
        self._dir_selector = dir_selector

        layout = QHBoxLayout()
        layout.setMargin(0)

        fc_label = QLabel(label_text)
        fc_label.setMinimumHeight(32)
        fc_label.setToolTip(hint)

        self.fc_text_field = QLineEdit()
        self.fc_text_field.setAlignment(Qt.AlignLeft)
        self.fc_text_field.setPlaceholderText(placeholder)
        self.fc_text_field.textChanged.connect(on_changed)
        self.fc_text_field.setToolTip(hint)

        fc_btn = QPushButton(button_text)
        fc_btn.setToolTip(hint)

        layout.addWidget(fc_label)
        layout.addWidget(self.fc_text_field)
        layout.addWidget(fc_btn)

        fc_btn.clicked.connect(
            self.open_dialog,
        )

        self.setLayout(layout)

    def get_file_path(self) -> str:
        """
        Gets the file path from the text field

        @rtype: str
        @returns: The file path contained in the text field
        """

        path = str(self.fc_text_field.text())
        if path and Path(path.strip()).exists():
            return path
        return None

    def open_dialog(self) -> None:
        """Opens a file dialog, when a path is chosen, the text field gets filled with its value"""

        if self._dir_selector:
            file_name, _ = QFileDialog.getExistingDirectory(
                self,
                self._dialog_caption,
                "",
                QFileDialog.Option.ShowDirsOnly,
            )
            if file_name:
                self.fc_text_field.setText(file_name)
        else:
            file_name, _ = QFileDialog.getOpenFileName(
                self, self._dialog_caption, "", self._dialog_filter
            )
            if file_name:
                self.fc_text_field.setText(file_name)

class DirChooser(QWidget):
    """
    A custom widget used for selecting a file path using a FileDialog and an input field
    """

    def __init__(
        self,
        label_text: str,
        hint: str,
        parent: Optional[QWidget] = None,
        placeholder: str = "",
        dialog_caption: str = "Select a dir",

        button_text: str = "...",
        dir_selector: bool = True,
        on_changed: Callable[[int], None] = None,
    ) -> None:
        super().__init__(parent=parent)

        self._dialog_caption = dialog_caption
        self._dir_selector = dir_selector

        layout = QHBoxLayout()
        layout.setMargin(0)

        fc_label = QLabel(label_text)
        fc_label.setMinimumHeight(32)
        fc_label.setToolTip(hint)

        self.fc_text_field = QLineEdit()
        self.fc_text_field.setAlignment(Qt.AlignLeft)
        self.fc_text_field.setPlaceholderText(placeholder)
        self.fc_text_field.textChanged.connect(on_changed)
        self.fc_text_field.setToolTip(hint)

        fc_btn = QPushButton(button_text)
        fc_btn.setToolTip(hint)
        fc_btn.clicked.connect(
            self.open_dialog,
        )

        layout.addWidget(fc_label)
        layout.addWidget(self.fc_text_field)
        layout.addWidget(fc_btn)

        

        self.setLayout(layout)

    def get_file_path(self) -> str:
        """
        Gets the file path from the text field

        @rtype: str
        @returns: The file path contained in the text field
        """

        path = str(self.fc_text_field.text())
        if path and Path(path.strip()).exists():
            return path
        return None

    def open_dialog(self) -> None:
        """Opens a file dialog, when a path is chosen, the text field gets filled with its value"""

        if self._dir_selector:
            dir_name = QFileDialog.getExistingDirectory(
                self,
                self._dialog_caption,
                "",
                QFileDialog.Option.ShowDirsOnly,
            )
            if dir_name:
                print(dir_name)
                self.fc_text_field.setText(dir_name)


class TwoBtnWnd(QtWidgets.QWidget):
    def __init__(self):
        super(TwoBtnWnd, self).__init__(parent=None)

        self.setWindowTitle(u"批量转换SCB文件为FBX")
        self.resize(600, 80)

        self.define_ui()
        self.build_ui()
        self.build_connections()
        
    def define_ui(self):
        self.choose_dir = DirChooser("选择文件目录: ","选择文件目录", self,button_text=". . .")
        self.trans_btn = QtWidgets.QPushButton("转换", self)


    def build_ui(self):

        layload = QtWidgets.QVBoxLayout()
        layload.addWidget(self.choose_dir , 5)
        layload.addWidget(self.trans_btn, 1)

        main_lay = QtWidgets.QVBoxLayout()
        self.setLayout(main_lay)
        main_lay.addLayout(layload)

    def build_connections(self):
        self.trans_btn.clicked.connect(self.transfer)

        
    def transfer(self):
        trans2Fbx(self.choose_dir.get_file_path())

def run():
    global custom_wnd
    try:
        custom_wnd.close()
        custom_wnd.deleteLater()
    except:
        pass
    custom_wnd = TwoBtnWnd()
    # 窗口置顶
    custom_wnd.setWindowFlags(Qt.WindowStaysOnTopHint)
    custom_wnd.show()

if __name__ == '__main__':
    run()