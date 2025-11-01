from calendar import c
import os
import sys
# 检查是否在Maya环境中
in_maya = False
try:
    import maya.cmds as cmds
    import maya.OpenMayaUI as omui
    in_maya = True
    # 在Maya中使用PySide2需要特殊导入
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance
except ImportError:
    # 不在Maya中时使用标准PySide2导入
    from PySide2.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog,
        QSplitter, QFrame, QMessageBox
    )
    from PySide2.QtCore import Qt, Signal, QSettings
    from PySide2.QtGui import QIcon

class FolderBrowser(QMainWindow):
    def __init__(self):
        # 在Maya中需要特殊处理窗口父对象
        parent = None
        if in_maya:
            # 获取Maya主窗口作为父对象
            maya_main_window_ptr = omui.MQtUtil.mainWindow()
            if maya_main_window_ptr:
                parent = wrapInstance(int(maya_main_window_ptr), QWidget)
        
        super(FolderBrowser, self).__init__(parent)
            
        self.setWindowTitle('LOL文件夹浏览器')
        self.setGeometry(100, 100, 1000, 600)  # 减小窗口尺寸以适应Maya
        
        # 安全获取脚本路径 - 处理Maya环境中__file__未定义的情况
        try:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # 在Maya中__file__可能未定义，使用当前工作目录或默认路径
            if in_maya:
                # 尝试从Maya脚本路径获取
                import maya.mel as mel
                scripts_path = mel.eval('internalVar -userScriptDir')
                self.script_dir = os.path.join(scripts_path, '..', '..', 'scripts')
            else:
                self.script_dir = os.getcwd()
        
        # 项目根目录（向上两级）
        self.root_dir = os.path.abspath(os.path.join(self.script_dir, '..'))
        # 默认路径设为characters文件夹
        self.default_path = os.path.join(self.root_dir, 'characters')
        
        # 使用简单的文本文件保存设置，避免可能的兼容性问题
        self.settings_file = os.path.join(self.script_dir, 'folder_browser_settings.txt')
        self.last_path = self.load_settings() or self.default_path
        
        self.init_ui()
        # 延迟加载内容，避免启动时处理过重导致崩溃
        QtCore.QTimer.singleShot(100, self.load_first_column)
    
    def init_ui(self):
        # 主布局 - 统一初始化UI，不再区分环境
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部路径选择区域
        path_layout = QHBoxLayout()
        
        # 路径输入框
        self.path_line_edit = QLineEdit(self.last_path)
        self.path_line_edit.setReadOnly(True)
        path_layout.addWidget(self.path_line_edit, 1)
        
        # 浏览按钮
        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)
        
        # 设置默认路径按钮
        default_btn = QPushButton('设置默认路径')
        default_btn.clicked.connect(self.set_default_path)
        path_layout.addWidget(default_btn)
        
        main_layout.addLayout(path_layout)
        
        # 三段式布局（分割器）
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 第一列：主文件夹树
        self.tree1 = QTreeWidget()
        self.tree1.setHeaderLabel('角色文件夹')
        self.tree1.itemClicked.connect(self.on_first_tree_clicked)
        # 添加右键菜单
        self.tree1.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree1.customContextMenuRequested.connect(self.show_context_menu)
        self.splitter.addWidget(self.tree1)
        
        # 第二列：Skins文件夹内容
        self.tree2 = QTreeWidget()
        self.tree2.setHeaderLabel('皮肤文件夹')
        self.tree2.itemClicked.connect(self.on_second_tree_clicked)
        # 添加右键菜单
        self.tree2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree2.customContextMenuRequested.connect(self.show_context_menu)
        self.splitter.addWidget(self.tree2)
        
        # 第三列：选中项的内容
        self.tree3 = QTreeWidget()
        self.tree3.setHeaderLabel('详细内容')
        # 连接双击和单击事件
        self.tree3.itemDoubleClicked.connect(self.on_third_tree_item_double_clicked)
        self.tree3.itemClicked.connect(self.on_third_tree_item_clicked)
        # 添加右键菜单
        self.tree3.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree3.customContextMenuRequested.connect(self.show_context_menu)
        self.splitter.addWidget(self.tree3)
        
        # 设置分割器比例
        if in_maya:
            self.splitter.setSizes([250, 250, 490])
        else:
            self.splitter.setSizes([300, 300, 590])
        
        # 设置分割器手柄的样式
        self.splitter.setHandleWidth(3)
        
        main_layout.addWidget(self.splitter, 1)
        
        # 底部操作按钮区域
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)  # 增加水平间隔
        bottom_layout.addStretch(1)  # 左侧空白拉伸
        
        # 添加tex转dds/tga转换区域 - 勾选框在上，按钮在下
        tex_group_layout = QVBoxLayout()
        tex_group_layout.setSpacing(5)  # 设置内部垂直间距
        
        # 添加删除tex文件勾选框
        self.delete_tex_checkbox = QWidget() if in_maya else QWidget()
        if in_maya:
            from PySide2.QtWidgets import QCheckBox
        else:
            from PySide2.QtWidgets import QCheckBox
        self.delete_tex_checkbox = QCheckBox('删除tex文件')
        self.delete_tex_checkbox.setChecked(False)  # 默认不勾选
        tex_group_layout.addWidget(self.delete_tex_checkbox)
        
        # 添加转换按钮
        convert_btn = QPushButton('转换tex为tga')
        convert_btn.clicked.connect(self.convert_tex_to_tga)
        tex_group_layout.addWidget(convert_btn)
        
        bottom_layout.addLayout(tex_group_layout)
        
        # 添加批量转换scb到fbx区域 - 勾选框在上，按钮在下
        scb_group_layout = QVBoxLayout()
        scb_group_layout.setSpacing(5)  # 设置内部垂直间距
        
        # 添加删除scb文件勾选框
        self.delete_scb_checkbox = QWidget() if in_maya else QWidget()
        if in_maya:
            from PySide2.QtWidgets import QCheckBox
        else:
            from PySide2.QtWidgets import QCheckBox
        self.delete_scb_checkbox = QCheckBox('删除scb文件')
        self.delete_scb_checkbox.setChecked(False)  # 默认不勾选
        scb_group_layout.addWidget(self.delete_scb_checkbox)
        
        # 添加转换按钮
        convert_scb_btn = QPushButton('批量转换scb为fbx')
        convert_scb_btn.clicked.connect(self.convert_scb_to_fbx)
        scb_group_layout.addWidget(convert_scb_btn)
        
        bottom_layout.addLayout(scb_group_layout)
        
        # 添加批量转换anm到fbx区域 - 勾选框在上，按钮在下
        anm_group_layout = QVBoxLayout()
        anm_group_layout.setSpacing(5)  # 设置内部垂直间距
        
        # 添加删除anm文件勾选框
        self.delete_anm_checkbox = QWidget() if in_maya else QWidget()
        if in_maya:
            from PySide2.QtWidgets import QCheckBox
        else:
            from PySide2.QtWidgets import QCheckBox
        self.delete_anm_checkbox = QCheckBox('删除anm文件')
        self.delete_anm_checkbox.setChecked(False)  # 默认不勾选
        anm_group_layout.addWidget(self.delete_anm_checkbox)
        
        # 添加转换按钮
        convert_anm_btn = QPushButton('批量转换anm为fbx')
        convert_anm_btn.clicked.connect(self.convert_anm_to_fbx)
        anm_group_layout.addWidget(convert_anm_btn)
        
        bottom_layout.addLayout(anm_group_layout)
        
        # 添加统一转换区域 - 勾选框在上，按钮在下
        all_group_layout = QVBoxLayout()
        all_group_layout.setSpacing(5)  # 设置内部垂直间距
        
        # 添加删除源文件勾选框
        self.delete_all_checkbox = QWidget() if in_maya else QWidget()
        if in_maya:
            from PySide2.QtWidgets import QCheckBox
        else:
            from PySide2.QtWidgets import QCheckBox
        self.delete_all_checkbox = QCheckBox('删除所有源文件')
        self.delete_all_checkbox.setChecked(False)  # 默认不勾选
        all_group_layout.addWidget(self.delete_all_checkbox)
        
        # 添加统一转换按钮
        convert_all_btn = QPushButton('运行所有转换')
        convert_all_btn.clicked.connect(self.convert_all)
        all_group_layout.addWidget(convert_all_btn)
        
        # 将统一转换区域添加到底部布局最右侧
        bottom_layout.addStretch(1)  # 确保在最右侧
        bottom_layout.addLayout(all_group_layout)
        
        main_layout.addLayout(bottom_layout)
    
    def browse_folder(self):
        file_dialog = QFileDialog(self)
        folder = file_dialog.getExistingDirectory(self, "选择文件夹", self.last_path)
        if folder:
            self.last_path = folder
            self.path_line_edit.setText(folder)
            self.save_settings()
            # 延迟加载，避免UI卡顿
            QtCore.QTimer.singleShot(50, self.load_first_column)
    
    def load_settings(self):
        """从简单文本文件加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return f.readline().strip()
        except Exception:
            pass
        return None
        
    def save_settings(self):
        """保存设置到简单文本文件"""
        try:
            with open(self.settings_file, 'w') as f:
                f.write(self.last_path)
        except Exception:
            pass
    
    def set_default_path(self):
        # 保存当前路径为默认路径
        self.default_path = self.last_path
        self.save_settings()
        msg_box = QtWidgets.QMessageBox(self) if in_maya else QMessageBox(self)
        msg_box.information(self, "设置成功", f"默认路径已设置为：\n{self.default_path}")
    
    def load_first_column(self):
        """加载第一列：主文件夹列表"""
        self.tree1.clear()
        
        if not os.path.exists(self.last_path):
            msg_box = QMessageBox(self)
            msg_box.warning(self, "警告", f"路径不存在：{self.last_path}")
            return
        
        try:
            # 获取所有一级子文件夹 - 使用异常处理逐个处理项目，避免一个错误导致整体失败
            items = []
            try:
                items = os.listdir(self.last_path)
            except Exception:
                pass
            
            for item in items:
                try:
                    item_path = os.path.join(self.last_path, item)
                    if os.path.isdir(item_path):
                        # 创建树节点
                        tree_item = QTreeWidgetItem(self.tree1)
                        tree_item.setText(0, item)
                        tree_item.setData(0, Qt.UserRole, item_path)
                        
                        # 检查是否有skins文件夹 - 异步检查或简化处理
                        skins_path = os.path.join(item_path, 'skins')
                        if os.path.exists(skins_path) and os.path.isdir(skins_path):
                            tree_item.setToolTip(0, "包含skins文件夹")
                except Exception:
                    # 忽略单个项目的错误，继续处理其他项目
                    pass
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"加载文件夹失败：{str(e)}")
    
    def on_first_tree_clicked(self, item, column):
        """点击第一列项目时，更新第二列显示skins文件夹内容"""
        self.tree2.clear()
        self.tree3.clear()
        
        # 获取选中项目的路径
        folder_path = item.data(0, Qt.UserRole)
        
        if not folder_path:
            return
        
        # 检查skins文件夹
        skins_path = os.path.join(folder_path, 'skins')
        if os.path.exists(skins_path) and os.path.isdir(skins_path):
            try:
                # 加载skins文件夹内容
                skin_items = []
                try:
                    skin_items = os.listdir(skins_path)
                except Exception:
                    pass
                
                for skin_item in skin_items:
                    try:
                        skin_item_path = os.path.join(skins_path, skin_item)
                        if os.path.isdir(skin_item_path):
                            # 创建树节点
                            tree_item = QTreeWidgetItem(self.tree2)
                            tree_item.setText(0, skin_item)
                            tree_item.setData(0, Qt.UserRole, skin_item_path)
                    except Exception:
                        # 忽略单个项目的错误
                        pass
            except Exception as e:
                msg_box = QMessageBox(self)
                msg_box.critical(self, "错误", f"加载skins文件夹失败：{str(e)}")
        else:
            msg_box = QMessageBox(self)
            msg_box.information(self, "信息", f"未找到skins文件夹：{skins_path}")
    
    def on_second_tree_clicked(self, item, column):
        """点击第二列项目时，更新第三列显示选中项的详细内容"""
        self.tree3.clear()
        
        # 获取选中项目的路径
        folder_path = item.data(0, Qt.UserRole)
        self.tree3.setColumnCount(2)
        self.tree3.setHeaderLabels(['名称', '类型'])
        
        if not folder_path:
            return
        
        try:
            # 使用定时器延迟执行，避免阻塞UI
            QtCore.QTimer.singleShot(0, lambda: self._populate_tree(self.tree3, folder_path))
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"加载内容失败：{str(e)}")
    
    def on_third_tree_item_double_clicked(self, item, column):
        """双击第三列项目时，如果是.skn或.scb文件则导入Maya场景"""
        file_path = item.data(0, Qt.UserRole)
        if not file_path or not os.path.isfile(file_path):
            return
        
        # 检查文件扩展名
        _, ext = os.path.splitext(file_path)
        
        # 处理.skn文件
        if ext.lower() == '.skn':
            if in_maya:
                try:
                    # 导入Maya命令
                    import maya.cmds as cmds
                    
                    # 新建场景，清空当前场景
                    cmds.file(new=True, force=True)
                    # 设为60fps
                    cmds.currentUnit(time='ntscf')
                    
                    # 直接导入.skn文件 - 参考v2.py的实现
                    cmds.file(file_path, i=True, type="League of Legends: SKN")
                    
                    # 获取导入后的对象
                    new_objects = cmds.ls(dag=True)
                    
                    # 确保导入有对象，如果没有则跳过
                    if new_objects:
                        cmds.select(new_objects)
                    
                    # 获取当前选中的对象
                    selected_objects = cmds.ls(selection=True)
                    
                    if selected_objects:
                        for obj in selected_objects:
                            # 确保对象是一个多边形网格
                            shape_nodes = cmds.listRelatives(obj, shapes=True, type='mesh')
                            if shape_nodes:
                                # 获取对象的所有面
                                faces = cmds.ls(f'{obj}.f[*]', flatten=True)
                                
                                # 反转法线 - 参考v2.py的实现
                                if faces:
                                    # normalMode=0 表示反转法线
                                    cmds.polyNormal(faces, normalMode=0)
                    
                    # 导入后选中网格 - 参考selet_mesh函数实现
                    poly_meshes = cmds.ls(type='mesh')
                    if poly_meshes:
                        # 获取多边形网格的父变换节点
                        transform_nodes = cmds.listRelatives(poly_meshes, parent=True)
                        cmds.select(transform_nodes)
                    
                    # 设置平滑着色
                    model_panels = cmds.getPanel(type='modelPanel')
                    if model_panels:
                        for panel in model_panels:
                            cmds.modelEditor(panel, e=True, displayAppearance='smoothShaded')
                    
                    # 移除成功消息提示
                except Exception as e:
                    msg_box = QMessageBox(self)
                    msg_box.critical(self, "错误", f"导入.skn文件失败：{str(e)}")
            else:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "需要在Maya环境中运行才能导入.skn文件")
        # 处理.scb文件
        elif ext.lower() == '.scb':
            if in_maya:
                try:
                    # 导入Maya命令
                    import maya.cmds as cmds
                    
                    # 新建场景，清空当前场景
                    cmds.file(new=True, force=True)
                    
                    # 导入.scb文件
                    cmds.file(file_path, i=True, type="League of Legends: SCB")
                    
                    # 获取导入后的对象
                    new_objects = cmds.ls(dag=True)
                    
                    # 确保导入有对象，如果没有则跳过
                    if new_objects:
                        cmds.select(new_objects)
                    
                    # 设置平滑着色
                    model_panels = cmds.getPanel(type='modelPanel')
                    if model_panels:
                        for panel in model_panels:
                            cmds.modelEditor(panel, e=True, displayAppearance='smoothShaded')
                except Exception as e:
                    msg_box = QMessageBox(self)
                    msg_box.critical(self, "错误", f"导入.scb文件失败：{str(e)}")
            else:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "需要在Maya环境中运行才能导入.scb文件")
    
    def on_third_tree_item_clicked(self, item, column):
        """单击第三列项目时，如果是.anm文件则应用到已导入的骨骼上，如果是.scb文件则导入并反转法线"""
        file_path = item.data(0, Qt.UserRole)
        if not file_path or not os.path.isfile(file_path):
            return
        
        # 检查文件扩展名
        _, ext = os.path.splitext(file_path)
        
        # 处理.scb文件
        if ext.lower() == '.scb':
            if in_maya:
                try:
                    # 导入Maya命令
                    import maya.cmds as cmds
                    
                    # 新建场景，清空当前场景
                    cmds.file(new=True, force=True)
                    
                    # 导入.scb文件 - 添加returnNewNodes=True参数获取导入的节点
                    imported_nodes = cmds.file(file_path, i=True, type="League of Legends: SCB", returnNewNodes=True)
                    
                    # 确保导入有对象
                    if not imported_nodes or imported_nodes == [None]:
                        # 尝试使用其他方法获取场景中的对象
                        all_nodes = cmds.ls(assemblies=True)
                        if not all_nodes:
                            all_nodes = cmds.ls()
                        
                        if all_nodes:
                            imported_nodes = all_nodes
                        else:
                            msg_box = QMessageBox(self)
                            msg_box.warning(self, "警告", f"导入.scb文件后未找到任何对象：{os.path.basename(file_path)}")
                            return
                    
                    # 选中导入的对象
                    cmds.select(imported_nodes)
                    
                    # 获取所有多边形网格
                    poly_meshes = cmds.ls(type='mesh')
                    if poly_meshes:
                        # 获取多边形网格的父变换节点
                        transform_nodes = cmds.listRelatives(poly_meshes, parent=True, fullPath=True)
                        if transform_nodes:
                            # 反转法线 - 直接对网格进行操作
                            for mesh in poly_meshes:
                                # 获取网格的所有面
                                faces = cmds.ls(f'{mesh}.f[*]', flatten=True)
                                if faces:
                                    # 反转法线
                                    cmds.polyNormal(faces, normalMode=0)
                            
                            # 选中变换节点
                            cmds.select(transform_nodes)
                    
                    # 设置平滑着色
                    model_panels = cmds.getPanel(type='modelPanel')
                    if model_panels:
                        for panel in model_panels:
                            cmds.modelEditor(panel, e=True, displayAppearance='smoothShaded')
                    
                    # 确保有选中的对象，然后调整摄像机聚焦
                    selected_objects = cmds.ls(selection=True)
                    if selected_objects and model_panels:
                        # 先尝试对所有选中对象执行viewFit
                        cmds.viewFit(all=True, fitFactor=0.8)
                        # 再对每个面板单独执行，确保所有视图都更新
                        # for panel in model_panels:
                        #     # 使用forceFit参数强制更新视图
                        #     cmds.viewFit(panel, all=True, fitFactor=0.8, forceFit=True)
                    
                except Exception as e:
                    msg_box = QMessageBox(self)
                    msg_box.critical(self, "错误", f"导入.scb文件失败：{str(e)}")
            else:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "需要在Maya环境中运行才能导入.scb文件")
        # 处理.anm文件
        elif ext.lower() == '.anm':
            if in_maya:
                try:
                    # 导入Maya命令
                    import maya.cmds as cmds
                    
                    # 清除骨骼动画函数（来自lol动画查看工具）
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
                    
                    # 设置时间范围函数
                    def set_time_range_by_bone():
                        # 尝试使用Root骨骼
                        bone_name = "Root"
                        if cmds.objExists(bone_name):
                            keyframes = cmds.keyframe(bone_name, query=True)
                            if keyframes:
                                min_frame = int(min(keyframes))
                                max_frame = int(max(keyframes))
                                cmds.playbackOptions(minTime=min_frame, maxTime=max_frame)
                                cmds.playbackOptions(animationStartTime=min_frame, animationEndTime=max_frame)
                                return
                        
                        # 尝试使用root骨骼（小写）
                        bone_name = "root"
                        if cmds.objExists(bone_name):
                            keyframes = cmds.keyframe(bone_name, query=True)
                            if keyframes:
                                min_frame = int(min(keyframes))
                                max_frame = int(max(keyframes))
                                cmds.playbackOptions(minTime=min_frame, maxTime=max_frame)
                                cmds.playbackOptions(animationStartTime=min_frame, animationEndTime=max_frame)
                    
                    # 检查场景中是否有骨骼
                    all_joints = cmds.ls(type='joint')
                    if not all_joints:
                        msg_box = QMessageBox(self)
                        msg_box.warning(self, "警告", "场景中没有骨骼，请先导入.skn文件")
                        return
                    
                    # 清除现有动画
                    clear_all_joint_animations()
                    
                    # 导入.anm文件动画 - 使用正确的文件类型，关闭确认对话框
                    cmds.file(file_path, i=True, type="League of Legends: ANM", ignoreVersion=True, prompt=False)
                    
                    # 根据动画设置时间滑块范围
                    set_time_range_by_bone()
                    
                    # 移除成功消息提示
                    # 显示错误消息时仍然保留
                except Exception as e:
                    msg_box = QMessageBox(self)
                    msg_box.critical(self, "错误", f"应用.anm动画失败：{str(e)}")
            else:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "需要在Maya环境中运行才能应用.anm动画")
    
    def _populate_tree(self, tree_widget, path, parent_item=None):
        """递归填充树结构 - 简化版本，避免递归过深"""
        try:
            # 限制递归深度，避免性能问题
            current_depth = 0
            if parent_item:
                # 简单估计深度
                current_depth = self._get_item_depth(parent_item)
            
            if current_depth > 3:  # 限制最大深度
                return
                
            # 遍历当前路径下的所有项目
            items = []
            try:
                items = os.listdir(path)
            except Exception:
                return
                
            # 分别处理文件夹和文件，优先显示文件夹
            dirs = []
            files = []
            
            for item in items:
                try:
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        dirs.append((item, item_path))
                    else:
                        # 过滤掉.tex和.skl文件
                        _, ext = os.path.splitext(item)
                        if ext.lower() not in ['.tex', '.skl']:
                            files.append((item, item_path))
                except Exception:
                    continue
            
            # 先添加文件夹
            for item, item_path in dirs:
                try:
                    if parent_item:
                        tree_item = QTreeWidgetItem(parent_item)
                    else:
                        tree_item = QTreeWidgetItem(tree_widget)
                    tree_item.setText(0, item)
                    tree_item.setText(1, "文件夹")
                    # 只存储路径数据
                    tree_item.setData(0, Qt.UserRole, item_path)
                    # 只展开一层，避免递归过深
                    if current_depth < 1:
                        # 在所有环境中都使用异步加载，避免阻塞
                        QtCore.QTimer.singleShot(0, lambda path=item_path, parent=tree_item: self._populate_tree(tree_widget, path, parent))
                except Exception:
                    continue
            
            # 再添加文件
            for item, item_path in files:
                try:
                    if parent_item:
                        tree_item = QTreeWidgetItem(parent_item)
                    else:
                        tree_item = QTreeWidgetItem(tree_widget)
                    tree_item.setText(0, item)
                    # 获取文件扩展名
                    _, ext = os.path.splitext(item)
                    tree_item.setText(1, ext[1:].upper() if ext else "文件")
                    # 存储文件路径数据
                    tree_item.setData(0, Qt.UserRole, item_path)
                except Exception:
                    continue
                    
            # 自动调整列宽
            if not parent_item:
                tree_widget.resizeColumnToContents(0)
                tree_widget.resizeColumnToContents(1)
        except Exception:
                # 忽略所有错误
                pass
    
    def convert_tex_to_tga(self):
        """将当前选中的skin文件夹中的.tex文件转换为.tga文件，保留透明通道，并删除原始tex文件"""
        # 检查是否有选中的skin文件夹
        selected_items = self.tree2.selectedItems()
        if not selected_items:
            msg_box = QMessageBox(self)
            msg_box.warning(self, "警告", "请先在皮肤文件夹中选择一个文件夹")
            return
            
        skin_folder = selected_items[0].data(0, Qt.UserRole)
        if not skin_folder or not os.path.isdir(skin_folder):
            msg_box = QMessageBox(self)
            msg_box.warning(self, "警告", "无效的皮肤文件夹")
            return
            
        # 准备工具路径
        tex2dds_path = os.path.join(self.script_dir, 'tex2dds.exe')
        magick_path = os.path.join(self.script_dir, 'magick.exe')
        
        # 检查工具是否存在
        if not os.path.exists(tex2dds_path):
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"未找到tex2dds.exe工具:\n{tex2dds_path}")
            return
            
        if not os.path.exists(magick_path):
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"未找到magick.exe工具:\n{magick_path}")
            return
            
        # 查找所有.tex文件
        tex_files = []
        try:
            # 递归搜索所有.tex文件
            for root, _, files in os.walk(skin_folder):
                for file in files:
                    if file.lower().endswith('.tex'):
                        tex_files.append(os.path.join(root, file))
                        
            if not tex_files:
                msg_box = QMessageBox(self)
                msg_box.information(self, "信息", f"在{skin_folder}中未找到.tex文件")
                return
                
            # 创建进度窗口
            progress = QtWidgets.QProgressDialog("正在转换tex为tga...", "取消", 0, len(tex_files), self) if in_maya else QProgressDialog("正在转换tex为tga...", "取消", 0, len(tex_files), self)
            progress.setWindowTitle("转换进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(0)
            
            # 开始转换
            success_count = 0
            failed_count = 0
            deleted_tex_count = 0
            failed_files = []
            
            for i, tex_file in enumerate(tex_files):
                # 检查是否取消
                if progress.wasCanceled():
                    msg_box = QMessageBox(self)
                    msg_box.information(self, "信息", f"转换已取消\n成功: {success_count}\n失败: {failed_count}\n已删除tex: {deleted_tex_count}")
                    return
                    
                # 更新进度
                progress.setValue(i)
                progress.setLabelText(f"正在转换 {os.path.basename(tex_file)} ({i+1}/{len(tex_files)})")
                
                # 处理路径中的空格
                tex_file_quoted = f'"{tex_file}"'
                dds_file = os.path.splitext(tex_file)[0] + '.dds'
                dds_file_quoted = f'"{dds_file}"'
                tga_file = os.path.splitext(tex_file)[0] + '.tga'
                tga_file_quoted = f'"{tga_file}"'
                
                try:
                    # 第一步：tex转dds
                    tex2dds_cmd = f'{tex2dds_path} {tex_file_quoted} {dds_file_quoted}'
                    os.system(tex2dds_cmd)
                    
                    # 检查dds文件是否生成
                    if not os.path.exists(dds_file):
                        failed_files.append(f"{os.path.basename(tex_file)} (无法生成dds)")
                        failed_count += 1
                        continue
                        
                    # 第二步：dds转tga，使用参数保留透明通道
                    magick_cmd = f'{magick_path} {dds_file_quoted} -background transparent -flatten -colorspace sRGB {tga_file_quoted}'
                    os.system(magick_cmd)
                    
                    # 检查tga文件是否生成
                    if os.path.exists(tga_file):
                        success_count += 1
                        
                        # 根据勾选框决定是否删除原始tex文件
                        if hasattr(self, 'delete_tex_checkbox') and self.delete_tex_checkbox.isChecked():
                            try:
                                os.remove(tex_file)
                                deleted_tex_count += 1
                            except Exception as e:
                                # 记录删除失败但不影响转换成功计数
                                failed_files.append(f"{os.path.basename(tex_file)} (生成tga成功，但删除tex失败: {str(e)})")
                        
                        # 删除中间的dds文件
                        try:
                            os.remove(dds_file)
                        except:
                            pass
                    else:
                        failed_files.append(f"{os.path.basename(tex_file)} (无法生成tga)")
                        failed_count += 1
                        
                except Exception as e:
                    failed_files.append(f"{os.path.basename(tex_file)} ({str(e)})")
                    failed_count += 1
                    
                # 让UI有机会更新
                QtCore.QCoreApplication.processEvents()
            
            # 完成转换
            progress.setValue(len(tex_files))
            
            # 显示结果
            result_msg = f"转换完成！\n成功: {success_count}\n失败: {failed_count}\n已删除tex: {deleted_tex_count}"
            if failed_files:
                result_msg += "\n\n失败的文件:\n" + "\n".join(failed_files[:10])  # 只显示前10个失败的文件
                if len(failed_files) > 10:
                    result_msg += f"\n...等{len(failed_files) - 10}个文件"
                    
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("转换结果")
            if failed_count > 0:
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText(result_msg)
            else:
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setText(result_msg)
            msg_box.exec_()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"转换过程出错:\n{str(e)}")
            
    def _get_item_depth(self, item):
        """简单计算树节点的深度"""
        depth = 0
        current = item
        while current.parent():
            depth += 1
            current = current.parent()
        return depth
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取触发右键菜单的树控件
        tree_widget = self.sender()
        if not tree_widget:
            return
        
        # 获取右键点击的项目
        item = tree_widget.itemAt(position)
        if not item:
            return
        
        # 创建右键菜单
        menu = QtWidgets.QMenu(self) if in_maya else QMenu(self)
        
        # 添加"打开文件夹位置"菜单项
        open_folder_action = menu.addAction("打开文件夹位置")
        open_folder_action.triggered.connect(lambda: self.open_folder(item))
        
        # 显示菜单
        menu.exec_(tree_widget.mapToGlobal(position))
    
    def open_folder(self, item):
        """打开项目所在的文件夹位置"""
        path = item.data(0, Qt.UserRole)
        if not path:
            return
        
        try:
            # 确保路径存在
            if os.path.exists(path):
                # 获取文件夹路径（如果是文件，则获取其所在目录）
                if os.path.isfile(path):
                    folder_path = os.path.dirname(path)
                else:
                    folder_path = path
                
                # 在Windows系统中打开文件夹
                if os.name == 'nt':
                    # 使用explorer打开文件夹，如果是文件则选中文件
                    if os.path.isfile(path):
                        os.startfile(folder_path)
                    else:
                        os.startfile(folder_path)
                else:
                    # 跨平台处理
                    import subprocess
                    if os.path.isfile(path):
                        subprocess.Popen(['xdg-open', folder_path])
                    else:
                        subprocess.Popen(['xdg-open', folder_path])
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"无法打开文件夹：{str(e)}")
    
    def _clear_all_joint_animations(self):
        """清理所有骨骼动画"""
        # 将时间滑块移动到第0帧
        import maya.cmds as cmds
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
    
    def _set_time_range_by_bone(self):
        """根据指定骨骼上的帧数设置时间滑块的范围"""
        import maya.cmds as cmds
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
        else:
            # 尝试小写的root骨骼
            bone_name = "root"
            if cmds.objExists(bone_name):
                keyframes = cmds.keyframe(bone_name, query=True)
                if keyframes:
                    # 找到关键帧的最小值和最大值
                    min_frame = int(min(keyframes))
                    max_frame = int(max(keyframes))
                    
                    # 设置时间滑块的范围
                    cmds.playbackOptions(minTime=min_frame, maxTime=max_frame)
                    cmds.playbackOptions(animationStartTime=min_frame, animationEndTime=max_frame)
    
    def _select_all_bones_and_models(self):
        """选中所有骨骼和模型"""
        import maya.cmds as cmds
        # 获取所有骨骼
        all_joints = cmds.ls(type='joint')
        # 获取所有多边形网格（模型常见类型）
        all_meshes = cmds.ls(type='mesh')
        # 从网格获取对应的变换节点
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
    
    def _import_anim_files(self, input_path):
        """导入动画文件"""
        import maya.cmds as cmds
        # 导入前，先清理所有的骨骼动画
        self._clear_all_joint_animations()
        
        try:
            # 使用 file 命令导入 anm 文件
            cmds.file(input_path, i=True, type="League of Legends: ANM", ignoreVersion=True)
        except Exception as e:
            raise Exception(f"导入动画文件失败: {str(e)}")
        
        # 根据动画设置滑块时间范围
        self._set_time_range_by_bone()
    
    def convert_anm_to_fbx(self):
        """批量将anm动画转换为fbx，直接在同目录下输出"""
        if not in_maya:
            msg_box = QMessageBox(self)
            msg_box.warning(self, "警告", "需要在Maya环境中运行才能转换anm动画为fbx")
            return
        
        try:
            # 检查是否有选中的文件夹或文件
            selected_items = []
            # 先检查tree3中是否有选中的anm文件
            tree3_items = self.tree3.selectedItems()
            # 再检查tree2中是否有选中的文件夹
            tree2_items = self.tree2.selectedItems()
            # 最后检查tree1中是否有选中的文件夹
            tree1_items = self.tree1.selectedItems()
            
            if tree3_items:
                selected_items = tree3_items
            elif tree2_items:
                selected_items = tree2_items
            elif tree1_items:
                selected_items = tree1_items
            else:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "请先选择一个包含anm文件的文件夹或anm文件")
                return
            
            # 获取选中的路径
            selected_path = selected_items[0].data(0, Qt.UserRole)
            if not selected_path or not os.path.exists(selected_path):
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "无效的选择路径")
                return
            
            # 查找所有.anm文件
            anm_files = []
            animations_folder = os.path.dirname(selected_path) if os.path.isfile(selected_path) else selected_path
            
            # 如果选中的是文件，只处理该文件
            if os.path.isfile(selected_path) and selected_path.lower().endswith('.anm'):
                anm_files = [selected_path]
            else:  # 如果是文件夹，检查animations子文件夹或直接搜索
                # 首先检查是否存在animations文件夹
                potential_animations_folder = os.path.join(selected_path, "animations")
                if os.path.exists(potential_animations_folder) and os.path.isdir(potential_animations_folder):
                    animations_folder = potential_animations_folder
                
                # 递归搜索所有.anm文件
                for root, _, files in os.walk(animations_folder):
                    for file in files:
                        if file.lower().endswith('.anm'):
                            anm_files.append(os.path.join(root, file))
            if not anm_files:
                msg_box = QMessageBox(self)
                msg_box.information(self, "信息", f"在{animations_folder}中未找到.anm文件")
                return
            
            # 创建进度对话框
            progress = QtWidgets.QProgressDialog("正在转换anm文件...", "取消", 0, len(anm_files), self) if in_maya else QProgressDialog("正在转换anm文件...", "取消", 0, len(anm_files), self)
            progress.setWindowTitle("批量转换")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            success_count = 0
            failed_count = 0
            deleted_anm_count = 0
            failed_files = []
            
            # 导入Maya命令
            import maya.cmds as cmds
            
            # 检查当前场景中是否存在骨骼
            joints = cmds.ls(type='joint')
            if not joints:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "场景中不存在骨骼网格体，请先导入骨骼网格体后再进行转换")
                progress.close()
                return
            
            # 处理每个.anm文件
            for index, anm_file in enumerate(anm_files):
                # 检查是否取消了操作
                if progress.wasCanceled():
                    break
                
                # 更新进度条
                progress.setValue(index)
                progress.setLabelText(f"正在处理: {anm_file} ({index+1}/{len(anm_files)})")
                
                # 让UI有机会更新
                QtCore.QCoreApplication.processEvents()
                
                # 获取anm文件的完整路径
                anm_path = os.path.join(animations_folder, anm_file)
                fbx_path = os.path.splitext(anm_path)[0] + '.fbx'
                
                try:
                    # 导入动画
                    self._import_anim_files(anm_path)
                    
                    # 选中所有骨骼和模型
                    self._select_all_bones_and_models()
                    
                    # 导出为.fbx
                    cmds.file(fbx_path, force=True, options="v=0", type="FBX export", exportSelected=True)
                    
                    # 检查fbx文件是否生成成功
                    if os.path.exists(fbx_path):
                        success_count += 1
                        
                        # 根据勾选框决定是否删除原始anm文件
                        if hasattr(self, 'delete_anm_checkbox') and self.delete_anm_checkbox.isChecked():
                            try:
                                os.remove(anm_path)
                                deleted_anm_count += 1
                            except Exception as e:
                                # 记录删除失败但不影响转换成功计数
                                failed_files.append(f"{anm_file} (生成fbx成功，但删除anm失败: {str(e)})")
                    else:
                        failed_files.append(f"{anm_file} (无法生成fbx)")
                        failed_count += 1
                        
                except Exception as e:
                    failed_files.append(f"{anm_file} ({str(e)})")
                    failed_count += 1
            
            # 完成转换
            progress.setValue(len(anm_files))
            
            # 显示结果
            result_msg = f"转换完成！\n成功: {success_count}\n失败: {failed_count}\n已删除anm: {deleted_anm_count}"
            if failed_files:
                result_msg += "\n\n失败的文件:\n" + "\n".join(failed_files[:10])  # 只显示前10个失败的文件
                if len(failed_files) > 10:
                    result_msg += f"\n...等{len(failed_files) - 10}个文件"
                    
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("转换结果")
            if failed_count > 0:
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText(result_msg)
            else:
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setText(result_msg)
            msg_box.exec_()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"转换过程出错:\n{str(e)}")
      
    def convert_all(self):
        """运行所有转换功能：anm转fbx、particles文件夹内的scb转fbx、所有tex文件转tga"""
        try:
            # 检查是否在Maya环境中运行（对于scb和anm转换需要）
            if not in_maya:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "需要在Maya环境中运行才能执行所有转换功能")
                return
            
            # 保存各个删除勾选框的原始状态
            original_states = {}
            if hasattr(self, 'delete_tex_checkbox'):
                original_states['delete_tex'] = self.delete_tex_checkbox.isChecked()
            if hasattr(self, 'delete_scb_checkbox'):
                original_states['delete_scb'] = self.delete_scb_checkbox.isChecked()
            if hasattr(self, 'delete_anm_checkbox'):
                original_states['delete_anm'] = self.delete_anm_checkbox.isChecked()
            
            try:
                # 根据统一删除勾选框设置各个删除勾选框状态
                if hasattr(self, 'delete_all_checkbox') and self.delete_all_checkbox.isChecked():
                    if hasattr(self, 'delete_tex_checkbox'):
                        self.delete_tex_checkbox.setChecked(True)
                    if hasattr(self, 'delete_scb_checkbox'):
                        self.delete_scb_checkbox.setChecked(True)
                    if hasattr(self, 'delete_anm_checkbox'):
                        self.delete_anm_checkbox.setChecked(True)
            except Exception:
                pass
            
            # 检查是否有选中的文件夹/文件
            selected_items = []
            # 先检查tree3中是否有选中的文件
            tree3_items = self.tree3.selectedItems()
            # 再检查tree2中是否有选中的文件夹
            tree2_items = self.tree2.selectedItems()
            # 最后检查tree1中是否有选中的文件夹
            tree1_items = self.tree1.selectedItems()
            
            if tree3_items:
                selected_items = tree3_items
            elif tree2_items:
                selected_items = tree2_items
            elif tree1_items:
                selected_items = tree1_items
            else:
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "请先选择一个包含文件的文件夹")
                return
            
            # 获取选中的路径
            selected_path = selected_items[0].data(0, Qt.UserRole)
            if not selected_path or not os.path.exists(selected_path):
                msg_box = QMessageBox(self)
                msg_box.warning(self, "警告", "无效的选择路径")
                return
            
            # 保存原始路径
            original_path = self.last_path
            try:
                # 设置当前路径为选中路径的父目录（如果是文件）或直接使用选中路径（如果是文件夹）
                if os.path.isfile(selected_path):
                    self.last_path = os.path.dirname(selected_path)
                else:
                    self.last_path = selected_path
                
                # 1. 首先执行anm转fbx
                self.convert_anm_to_fbx()
                
                # 2. 然后执行particles文件夹内的scb转fbx
                if os.path.isfile(selected_path):
                    self.last_path = os.path.dirname(selected_path)
                else:
                    self.last_path = selected_path
                self.convert_scb_to_fbx()
                
                # 3. 最后执行tex转tga
                if os.path.isfile(selected_path):
                    self.last_path = os.path.dirname(selected_path)
                else:
                    self.last_path = selected_path
                self.convert_tex_to_tga()
                
                # 显示完成消息
                msg_box = QMessageBox(self)
                msg_box.information(self, "完成", "所有转换任务已完成！")
            finally:
                # 恢复删除勾选框的原始状态
                if hasattr(self, 'delete_tex_checkbox') and 'delete_tex' in original_states:
                    self.delete_tex_checkbox.setChecked(original_states['delete_tex'])
                if hasattr(self, 'delete_scb_checkbox') and 'delete_scb' in original_states:
                    self.delete_scb_checkbox.setChecked(original_states['delete_scb'])
                if hasattr(self, 'delete_anm_checkbox') and 'delete_anm' in original_states:
                    self.delete_anm_checkbox.setChecked(original_states['delete_anm'])
                    
                # 恢复原始路径
                self.last_path = original_path
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"运行所有转换时出错:\n{str(e)}")
          
    def convert_scb_to_fbx(self):
        """批量将scb文件转换为fbx文件，优先处理particles文件夹内的scb"""
        # 检查是否在Maya环境中
        if not in_maya:
            msg_box = QMessageBox(self)
            msg_box.warning(self, "警告", "需要在Maya环境中运行才能转换scb文件")
            return
        
        # 检查tree2中是否有选中的文件夹
        tree2_items = self.tree2.selectedItems()
        
        # 查找particles文件夹
        particles_folder = None
        if tree2_items:
            selected_path = tree2_items[0].data(0, Qt.UserRole)
            if selected_path and os.path.exists(selected_path) and os.path.isdir(selected_path):
                # 检查是否存在particles子文件夹
                particles_path = os.path.join(selected_path, 'particles')
                if os.path.exists(particles_path) and os.path.isdir(particles_path):
                    particles_folder = particles_path
        
        try:
            # 查找所有.scb文件
            scb_files = []
            
            # 如果找到particles文件夹，只处理其中的scb文件
            if particles_folder:
                for root, _, files in os.walk(particles_folder):
                    for file in files:
                        if file.lower().endswith('.scb'):
                            scb_files.append(os.path.join(root, file))
                
                # 如果particles文件夹中没有scb文件，跳过scb转换
                if not scb_files:
                    msg_box = QMessageBox(self)
                    msg_box.information(self, "信息", f"在particles文件夹中未找到.scb文件，跳过scb转换")
                    return
            else:
                # 没有particles文件夹或没有选中tree2，尝试获取其他选中项
                selected_items = []
                # 先检查tree3中是否有选中的scb文件
                tree3_items = self.tree3.selectedItems()
                # 再检查tree2中是否有选中的文件夹
                # 最后检查tree1中是否有选中的文件夹
                tree1_items = self.tree1.selectedItems()
                
                if tree3_items:
                    selected_items = tree3_items
                elif tree2_items:
                    selected_items = tree2_items
                elif tree1_items:
                    selected_items = tree1_items
                else:
                    msg_box = QMessageBox(self)
                    msg_box.warning(self, "警告", "请先选择一个包含scb文件的文件夹")
                    return
                
                # 获取选中的路径
                selected_path = selected_items[0].data(0, Qt.UserRole)
                if not selected_path or not os.path.exists(selected_path):
                    msg_box = QMessageBox(self)
                    msg_box.warning(self, "警告", "无效的选择路径")
                    return
                
                # 如果选中的是文件，只处理该文件
                if os.path.isfile(selected_path) and selected_path.lower().endswith('.scb'):
                    scb_files = [selected_path]
                else:  # 如果是文件夹，递归搜索所有.scb文件
                    for root, _, files in os.walk(selected_path):
                        for file in files:
                            if file.lower().endswith('.scb'):
                                scb_files.append(os.path.join(root, file))
            
            if not scb_files:
                msg_box = QMessageBox(self)
                msg_box.information(self, "信息", f"在{selected_path}中未找到.scb文件")
                return
            
            # 创建进度窗口
            progress = QtWidgets.QProgressDialog("正在转换scb为fbx...", "取消", 0, len(scb_files), self) if in_maya else QProgressDialog("正在转换scb为fbx...", "取消", 0, len(scb_files), self)
            progress.setWindowTitle("转换进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(0)
            
            # 导入Maya命令
            import maya.cmds as cmds
            
            # 开始转换
            success_count = 0
            failed_count = 0
            deleted_scb_count = 0
            failed_files = []
            
            for i, scb_file in enumerate(scb_files):
                # 检查是否取消
                if progress.wasCanceled():
                    msg_box = QMessageBox(self)
                    msg_box.information(self, "信息", f"转换已取消\n成功: {success_count}\n失败: {failed_count}\n已删除scb: {deleted_scb_count}")
                    return
                    
                # 更新进度
                progress.setValue(i)
                progress.setLabelText(f"正在转换 {os.path.basename(scb_file)} ({i+1}/{len(scb_files)})")
                
                try:
                    # 新建场景，清空当前场景
                    cmds.file(new=True, force=True)
                    
                    # 导入.scb文件
                    cmds.file(scb_file, i=True, type="League of Legends: SCB")
                    
                    # 获取导入后的对象
                    new_objects = cmds.ls(dag=True)
                    
                    # 确保导入有对象，如果没有则跳过
                    if not new_objects:
                        failed_files.append(f"{os.path.basename(scb_file)} (未导入任何对象)")
                        failed_count += 1
                        continue
                    
                    # 选中所有对象
                    cmds.select(new_objects)
                    
                    # 获取所有多边形网格
                    poly_meshes = cmds.ls(type='mesh')
                    if poly_meshes:
                        # 反转法线 - 直接对网格进行操作
                        for mesh in poly_meshes:
                            # 获取网格的所有面
                            faces = cmds.ls(f'{mesh}.f[*]', flatten=True)
                            if faces:
                                # 反转法线
                                cmds.polyNormal(faces, normalMode=0)
                        
                        # 确保选中变换节点
                        transform_nodes = cmds.listRelatives(poly_meshes, parent=True, fullPath=True)
                        if transform_nodes:
                            cmds.select(transform_nodes)
                    
                    # 定义导出.fbx文件的路径
                    fbx_file = os.path.splitext(scb_file)[0] + '.fbx'
                    
                    # 导出为.fbx
                    cmds.file(fbx_file, force=True, options="v=0", type="FBX export", exportSelected=True)
                    
                    success_count += 1
                    
                    # 根据勾选框决定是否删除原始scb文件
                    if hasattr(self, 'delete_scb_checkbox') and self.delete_scb_checkbox.isChecked():
                        try:
                            os.remove(scb_file)
                            deleted_scb_count += 1
                        except Exception as e:
                            # 记录删除失败但不影响转换成功计数
                            failed_files.append(f"{os.path.basename(scb_file)} (导出fbx成功，但删除scb失败: {str(e)})")
                    
                except Exception as e:
                    failed_files.append(f"{os.path.basename(scb_file)} ({str(e)})")
                    failed_count += 1
                    
                # 让UI有机会更新
                QtCore.QCoreApplication.processEvents()
            
            # 完成转换
            progress.setValue(len(scb_files))
            
            # 显示结果
            result_msg = f"转换完成！\n成功: {success_count}\n失败: {failed_count}\n已删除scb: {deleted_scb_count}"
            if failed_files:
                result_msg += "\n\n失败的文件:\n" + "\n".join(failed_files[:10])  # 只显示前10个失败的文件
                if len(failed_files) > 10:
                    result_msg += f"\n...等{len(failed_files) - 10}个文件"
                    
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("转换结果")
            if failed_count > 0:
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText(result_msg)
            else:
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setText(result_msg)
            msg_box.exec_()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.critical(self, "错误", f"转换过程出错:\n{str(e)}")

def show_folder_browser():
    """在Maya中显示文件夹浏览器的函数"""
    try:
        # 检查是否已经有窗口打开
        global folder_browser_window
        try:
            if folder_browser_window and folder_browser_window.isVisible():
                folder_browser_window.raise_()
                folder_browser_window.activateWindow()
                return
        except:
            pass
            
        # 创建新窗口
        folder_browser_window = FolderBrowser()
        folder_browser_window.show()
    except Exception as e:
        if in_maya:
            cmds.warning(f"创建文件夹浏览器失败: {str(e)}")
        else:
            print(f"创建文件夹浏览器失败: {str(e)}")

if __name__ == '__main__':
    # 在独立Python环境中运行
    if not in_maya:
        # 确保中文正常显示
        app = QApplication(sys.argv)
        window = FolderBrowser()
        window.show()
        sys.exit(app.exec_())
    else:
        # 在Maya中直接显示
        show_folder_browser()