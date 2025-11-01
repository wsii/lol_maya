import sys
import os

from pathlib import Path
from typing import Callable, Optional

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *


def selet_mesh():
    # 获取当前具有焦点的面板
    # current_panel = cmds.getPanel(withFocus=True)
    # 获取所有模型编辑器面板
    model_panels = cmds.getPanel(type='modelPanel')

    if model_panels:
        for panel in model_panels:
            # 设置每个模型编辑器面板的显示外观为平滑着色
            cmds.modelEditor(panel, e=True, displayAppearance='smoothShaded')
            print(f"已将面板 {panel} 的显示外观设置为平滑着色。")
    else:
        print("未找到模型编辑器面板。")

    # 选中所有多边形网格节点
    poly_meshes = cmds.ls(type='mesh')

    if poly_meshes:
        # 获取多边形网格的父变换节点
        transform_nodes = cmds.listRelatives(poly_meshes, parent=True)
        cmds.select(transform_nodes)
        cmds.viewFit(poly_meshes, all=False)

    else:
        print("场景中没有多边形模型。")

# 全部转换为 FBX
def export_all_to_Fbx(input_folder):
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

# 将导入的转换为 FBX
def export_to_Fbx(input_path):
    # 定义导入和导出的路径

    # 获取导入后网格
    selet_mesh()

    # 定义导出 .fbx 文件的路径
    output_path = os.path.splitext(input_path)[0] + '.fbx'
    
    # 导出为 .fbx
    try:
        cmds.file(output_path, force=True, options="v=0", type="FBX export", exportSelected=True)
        print(f'Successfully exported {output_path}')
    except Exception as e:
        print(f'Failed to export {output_path}: {str(e)}')


# 导入选择的SCB
def import_scb_files(input_path):
    # 新建场景，清空当前场景
    cmds.file(new=True, force=True)
    
    # 导入 .scb 文件
    if input_path.endswith('.sco'):
        try:
            cmds.file(input_path, i=True, type="League of Legends: SCO")
            print(f'Successfully imported {input_path}')
        except Exception as e:
            print(f'Failed to import {input_path}: {str(e)}')

        # 获取导入后的对象
        new_objects = cmds.ls(dag=True)

        # 确保导入有对象，如果没有则跳过
        if new_objects:
            cmds.select(new_objects)
        else:
            print(f'No new objects were imported from {input_path}.')
    
    if input_path.endswith('.scb'):
        try:
            cmds.file(input_path, i=True, type="League of Legends: SCB")
            print(f'Successfully imported {input_path}')
        except Exception as e:
            print(f'Failed to import {input_path}: {str(e)}')
            return

        # 获取导入后的对象
        new_objects = cmds.ls(dag=True)

        # 确保导入有对象，如果没有则跳过
        if new_objects:
            cmds.select(new_objects)
        else:
            print(f'No new objects were imported from {input_path}.')
            return
    
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
                    # normalMode=0 表示反转法线
                    cmds.polyNormal(faces, normalMode=0) 
                    
                    print(f"Reversed normals for {obj}")
                else:
                    print(f"No faces found on {obj}")
            else:
                print(f"{obj} is not a polygon mesh.")
    else:
        print("No objects selected.")

    # 导入后选中网格
    selet_mesh()

class SCBFileSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_directory = ""
        self.initUI()

    def initUI(self):
        # 创建垂直布局
        layout = QVBoxLayout()

        # 创建选择目录按钮
        self.select_dir_button = QPushButton('选择目录')
        self.select_dir_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_dir_button)

        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 创建导出按钮和导出全部勾选框的水平布局
        export_layout = QHBoxLayout()

        self.export_button = QPushButton('导出')
        self.export_button.clicked.connect(self.export_files)
        export_layout.addWidget(self.export_button)

        self.export_all_checkbox = QCheckBox('导出全部')
        export_layout.addWidget(self.export_all_checkbox)

        layout.addLayout(export_layout)

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
            self.selected_directory = directory
            # 清空列表
            self.list_widget.clear()
            # 获取目录下的 .scb 文件
            scb_files = [f for f in os.listdir(directory) if f.endswith('.scb') or f.endswith('.sco')]
            for file in scb_files:
                self.list_widget.addItem(file)

    def on_item_clicked(self, item):
        # 输出点击的列表项对应的文件完整路径
        file_name = item.text()
        file_path = os.path.join(self.selected_directory, file_name)
        # 导入选中的scb文件
        import_scb_files(file_path)
        # 获取当前活动的透视视图
        # panel = cmds.getPanel(withFocus=True)
        # if cmds.getPanel(typeOf=panel) == 'modelPanel':
        #     # 将视图显示模式设置为边面显示
        #     cmds.modelEditor(panel, e=True, displayAppearance='edgesFaces')



    def export_files(self):
        if self.export_all_checkbox.isChecked():
            # 导出全部文件的逻辑，这里只是简单打印路径
            export_all_to_Fbx(self.selected_directory)
            scb_files = [f for f in os.listdir(self.selected_directory) if f.endswith('.scb')]
            for file in scb_files:
                file_path = os.path.join(self.selected_directory, file)
                print(f"导出文件: {file_path}")
        else:
            # 导出选中文件的逻辑，这里只是简单打印路径
            selected_items = self.list_widget.selectedItems()

            for item in selected_items:
                file_name = item.text()
                file_path = os.path.join(self.selected_directory, file_name)
                export_to_Fbx(file_path)
                print(f"导出文件: {file_path}")
    

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