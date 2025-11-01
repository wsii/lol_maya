import os
import maya.cmds as cmds

# 定义导入和导出的路径
input_folder = r'D:\BaiduNetdiskDownload\贴图集\LOL山海特效贴图\particles'  # 修改为你的 .scb 文件所在路径
output_folder = r'D:\BaiduNetdiskDownload\贴图集\LOL山海特效贴图\particles'  # 修改为你的 .fbx 导出路径


# 确保导出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

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
    
    # 定义导出 .fbx 文件的路径
    fbx_file = os.path.splitext(scb_file)[0] + '.fbx'
    output_path = os.path.join(output_folder, fbx_file)
    
    # 导出为 .fbx
    try:
        cmds.file(output_path, force=True, options="v=0", type="FBX export", exportSelected=True)
        print(f'Successfully exported {fbx_file}')
    except Exception as e:
        print(f'Failed to export {fbx_file}: {str(e)}')
