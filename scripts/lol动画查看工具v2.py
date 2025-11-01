import sys
import os

from pathlib import Path
from typing import Callable, Optional

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

# 选中模型
def selet_mesh():
    # 选中所有多边形网格节点
    poly_meshes = cmds.ls(type='mesh')
    if poly_meshes:
        # 获取多边形网格的父变换节点
        transform_nodes = cmds.listRelatives(poly_meshes, parent=True)
        cmds.select(transform_nodes)
    else:
        print("场景中没有多边形模型。")

    #     # 获取当前具有焦点的面板
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

# 选中所有骨骼和模型
def select_all_bones_and_models():
    # 获取所有骨骼
    all_joints = cmds.ls(type='joint')
    # 获取所有多边形网格（模型常见类型）
    all_meshes = cmds.ls(type='mesh')
    # 从网格获取对应的变换节点，因为通常在 Maya 中选中的是变换节点
    all_mesh_transforms = []
    for mesh in all_meshes:
        transform = cmds.listRelatives(mesh, parent=True)
        if transform:
            all_mesh_transforms.append(transform[0])
    # 合并骨骼和模型变换节点列表
    all_objects = all_joints + all_mesh_transforms
    if all_objects:
        # 选中所有对象
        cmds.select(all_objects)
        print("已选中所有骨骼和模型。")
    else:
        print("场景中没有骨骼和模型。")

# 清理所有骨骼动画
def clear_all_joint_animations():

    # 将时间滑块移动到第0帧
    cmds.currentTime(0)

    # 获取场景中所有的骨骼
    all_joints = cmds.ls(type='joint')

    if all_joints:
        for joint in all_joints:
            # 获取该骨骼上的所有动画曲线
            anim_curves = cmds.listConnections(joint, type='animCurve')
            if anim_curves:
                for curve in anim_curves:
                    # 删除动画曲线上的所有关键帧
                    cmds.cutKey(curve)
                print(f"已清理骨骼 {joint} 上的动画")
            else:
                print(f"骨骼 {joint} 上没有动画")
    else:
        print("场景中没有骨骼。")

# 根据指定骨骼上的帧数设置时间滑块的范围
def set_time_range_by_bone():

    bone_name = "Root"

    # 设为60fps
    cmds.currentUnit(time='ntscf')

    if cmds.objExists(bone_name):
        # 获取指定骨骼上的所有关键帧
        keyframes = cmds.keyframe(bone_name, query=True)
        if keyframes:
            # 找到关键帧的最小值和最大值
            min_frame = int(min(keyframes))
            max_frame = int(max(keyframes))

            # 设置时间滑块的范围
            cmds.playbackOptions(minTime=min_frame, maxTime=max_frame)
            cmds.playbackOptions(animationStartTime=min_frame, animationEndTime=max_frame)

            print(f"时间滑块范围已设置为: {min_frame} - {max_frame}")
        else:
            print(f"{bone_name} 骨骼上没有关键帧动画。")
    else:
        # 获取指定骨骼上的所有关键帧
        bone_name = "root"
        keyframes = cmds.keyframe(bone_name, query=True)
        if keyframes:
            # 找到关键帧的最小值和最大值
            min_frame = int(min(keyframes))
            max_frame = int(max(keyframes))

            # 设置时间滑块的范围
            cmds.playbackOptions(minTime=min_frame, maxTime=max_frame)
            cmds.playbackOptions(animationStartTime=min_frame, animationEndTime=max_frame)

            print(f"时间滑块范围已设置为: {min_frame} - {max_frame}")
        else:
            print(f"{bone_name} 骨骼上没有关键帧动画。")
        # print(f"未找到名为 {bone_name} 的骨骼。")

# 全部转换为 FBX
def export_all_to_Fbx(input_folder):
    # 定义导入和导出的路径

    # 确保导出文件夹存在
    if not os.path.exists(input_folder):
        # os.makedirs(input_folder)
        pass

    # 获取所有 .anm 文件
    anm_files = [f for f in os.listdir(input_folder) if f.endswith('.anm')]

    # 处理每个 .anm 文件
    for anm_file in anm_files:
        input_path = os.path.join(input_folder, anm_file)
        export_to_Fbx(input_path)

# 将导入的转换为 FBX
def export_to_Fbx(input_path):
    # 1、导入动画
    import_anim_files(input_path)

    # 选中所有骨骼和网格体
    select_all_bones_and_models()

    # 定义导出 .fbx 文件的路径
    output_path = os.path.splitext(input_path)[0] + '.fbx'
    
    # 导出为 .fbx
    try:
        cmds.file(output_path, force=True, options="v=0", type="FBX export", exportSelected=True)
        print(f'Successfully exported {output_path}')
    except Exception as e:
        print(f'Failed to export {output_path}: {str(e)}')

# 导入 .skn 文件
def import_skn_files(input_path):
    # 新建场景，清空当前场景
    cmds.file(new=True, force=True)
    # 设为60fps
    cmds.currentUnit(time='ntscf')
    # 导入 .skn 文件
    try:
        cmds.file(input_path, i=True, type="League of Legends: SKN")
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

# 导入选择的anm
def import_anim_files(input_path):

    # 导入前，先清理所有的骨骼动画
    clear_all_joint_animations()

    try:
        # 使用 file 命令导入 anm 文件
        cmds.file(input_path, i=True, type="League of Legends: ANM", ignoreVersion=True)
        print(f"成功导入 {input_path}")
    except Exception as e:
        print(f"导入文件时出错: {e}")

    # 根据动画设置滑块时间范围
    set_time_range_by_bone()

class AnimFileSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.file_path = ""
        self.file_directory = ""
        self.anim_file_directory = ""
        self._dialog_caption = "选择SKN文件"
        self._dialog_filter = "All files (*.skn)"

        self.initUI()

    def initUI(self):
        # 创建垂直布局
        layout = QVBoxLayout()

        layoutH = QHBoxLayout()
        layoutH.setMargin(0)

        fc_label = QLabel("选择skn文件")
        fc_label.setMinimumHeight(32)
        fc_label.setToolTip("选择skn文件")

        # 路径文本框
        self.fc_text_field = QLineEdit()
        self.fc_text_field.setAlignment(Qt.AlignLeft)
        self.fc_text_field.setPlaceholderText(self._dialog_caption)
        # self.fc_text_field.textChanged.connect(on_selected_changed)

        # 创建选择文件按钮
        button_text = "选择文件"
        fc_btn = QPushButton(button_text)
        # fc_btn.setToolTip(hint)
        fc_btn.clicked.connect(
            self.select_file_dialog,
        )

        layoutH.addWidget(fc_label)
        layoutH.addWidget(self.fc_text_field)
        layoutH.addWidget(fc_btn)

        layout.addLayout(layoutH)

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
        self.setWindowTitle('anm 文件选择器')
        self.setGeometry(300, 300, 400, 600)


    def get_file_dir(self) -> str:
        """
        Gets the file path from the text field

        @rtype: str
        @returns: The file path contained in the text field
        """

        path = str(self.fc_text_field.text())
        if path and Path(path.strip()).exists():
            return path
        return None

    def select_file_dialog(self) -> None:
        """Opens a file dialog, when a path is chosen, the text field gets filled with its value"""

        file_path, _ = QFileDialog.getOpenFileName(
            self, self._dialog_caption, "", self._dialog_filter
        )
        if file_path:
            self.file_path = file_path
            self.fc_text_field.setText(file_path)
            self.file_directory = os.path.dirname(file_path)
            import_skn_files(file_path)
        
        if self.file_directory:

            self.anim_file_directory = self.file_directory + "/animations/"
            if not os.path.exists(self.anim_file_directory):
                # 如果目录不存在，则创建它
                self.anim_file_directory = self.file_directory
            # 清空列表
            self.list_widget.clear()
            # 获取目录下的 .anm 文件
            anim_files = [f for f in os.listdir(self.anim_file_directory) if f.endswith('.anm')]
            for file in anim_files:
                self.list_widget.addItem(file)


    def on_item_clicked(self, item):

        # 输出点击的列表项对应的文件完整路径
        file_name = item.text()
        file_path = os.path.join(self.anim_file_directory, file_name)

        # 导入选中的anim文件
        import_anim_files(file_path)


    def export_files(self):
        if self.export_all_checkbox.isChecked():
            # 导出全部文件的逻辑，这里只是简单打印路径
            export_all_to_Fbx(self.anim_file_directory)
            anm_files = [f for f in os.listdir(self.anim_file_directory) if f.endswith('.anm')]
            for file in anm_files:
                file_path = os.path.join(self.file_directory, file)
                print(f"导出文件: {file_path}")
        else:
            # 导出选中文件的逻辑，这里只是简单打印路径
            selected_items = self.list_widget.selectedItems()

            for item in selected_items:
                file_name = item.text()
                file_path = os.path.join(self.anim_file_directory, file_name)
                export_to_Fbx(file_path)
                print(f"导出文件: {file_path}")
    

def run():
    global custom_wnd
    try:
        custom_wnd.close()
        custom_wnd.deleteLater()
    except:
        pass
    custom_wnd = AnimFileSelector()
    # 窗口置顶
    custom_wnd.setWindowFlags(Qt.WindowStaysOnTopHint)
    custom_wnd.show()

if __name__ == '__main__':
    run()