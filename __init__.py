#
# Sekisuihouse Blender Tools
# Written by Nao Sakai
#
bl_info = {
    "name": "Sekisuihouse Blender Tools",
    "author": "Naoyuki Sakai",
    "version": (1, 1),
    "blender": (3, 34, 0),
    "location": "View3D > Sidebar",
    "description": "Provide several Sekisuihouse-specific tools",
    "warning": "",
    "doc_url": "",
    "category": "Sekisuihouse Tools",
}


import bpy
import os
import sys
import csv
from pathlib import Path
from bpy.props import *
from bpy.types import Panel, Operator


class SHToolsPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "SH Tools"
    bl_idname = "OBJECT_PT_hello"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SH Tools'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.initializer")
        
        row = layout.row()
        row.operator("object.plants_eliminator")
        row = layout.row()
        row.operator("object.convert_materials")
#        row = layout.row()
#        row.operator("object.test")
        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')



class Initializer(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.initializer"
    bl_label = "Initialize"
    bl_description = "Initialize data from CG3S"


    def execute(self, context):
#        print('hogehgo')
        msg = Initializer.initialize()
        return {'FINISHED'}
#        return (msg)


    def ChkInitialized():
        InitializeFlag = 0
        for i in bpy.data.materials:
            if i.name == 'InitializeFlag':
                InitializeFlag = 1
                break
        return(InitializeFlag)


    def initialize():
        if Initializer.ChkInitialized() == 0:
            # 全オブジェクトを選択する
            bpy.ops.object.select_all(action='SELECT')
            # 全オブジェクトのスケールを10倍する
            ratios=(10, 10, 10)
            bpy.ops.transform.resize(value=ratios, constraint_axis=(True,True,True))
            # 選択したオブジェクトの親子を解除 Clear and Keep Transformation
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # 全てのオブジェクトのトランスフォームを適用する
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            # $$$ で始まる Empty を削除する
            obj_list = []
            for i in bpy.data.objects:
                if '$$$' in i.name:
                    obj_list.append(i.name)
            for o_name in obj_list:
                delete_object_target(o_name)
            # メッシュオブジェクトの原点をジオメトリに変更する
            objs = [obj for obj in bpy.data.objects
                if obj.type == "MESH"]
            override = bpy.context.copy()
            override["selected_editable_objects"] = objs
            bpy.ops.object.origin_set(override, type='ORIGIN_GEOMETRY')
            # 最初のオブジェクトをアクティブにする　動いた
            for obj in bpy.data.objects:
                if obj.type == "MESH":
                    try:
                        bpy.context.view_layer.objects.active = obj
                    except RuntimeError:
                        continue
                    break
            # 編集モードに移行する
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            # 頂点を全選択した状態とする
            bpy.ops.mesh.select_all(action='SELECT') 
            # 大きさ0を融解（結合距離 0.0001）
            bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
            # 変更を反映するため再び頂点を全選択
            bpy.ops.mesh.select_all(action='SELECT') 
            # 孤立を削除（頂点、辺のみ）
            bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
            # 孤立を削除で全選択が解除されるので再び頂点を全選択
            bpy.ops.mesh.select_all() 
            # 重複頂点を削除（結合距離 0.0001、非選択部の結合無効）
            bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
            # 四角ポリゴンに変換
            bpy.ops.mesh.tris_convert_to_quads(face_threshold=1.5708, shape_threshold=1.5708)
            # オブジェクトモードに移行する
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            # Initialize 実行済みフラグとしてのマテリアルを作成する
            new_mat = bpy.data.materials.new("InitializeFlag") 
            # 3Dカーソルの位置を原点に移動
            bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
            msg = 'Succsessfuly Initialized'
        else:
            msg = 'Alerady Initialized'
        return(msg)



class plantsEliminator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.plants_eliminator"
    bl_label = "Delete Plants"
    bl_description = "Delete all planes of plants"
    
    def execute(self, context):
        plantsEliminator.delete_plants()
        return {'FINISHED'}
    
    def delete_plants():
        obj_list = []
        for i in bpy.data.objects:
            obj_list.append(i.name) 
        for o_name in obj_list:
            obj = bpy.data.objects[o_name]
            if '01 - De' in str(obj.active_material):
                for k in bpy.data.objects:    # data API を評価し
                    if k.name == o_name:      # オブジェクト名が o_name なら
                        delete_object_target(o_name) # 削除する
        return


class convertMaterials(bpy.types.Operator):
    bl_idname = "object.convert_materials"
    bl_label = "Convert Materials"
    bl_description = "Convert CG3S materials into Blender materials"

    convert_dic = {
        'SH_ow': ('convert_table_SHow.csv', 'SH_Outer_Wall_Materials.blend'),
        'G_ex': ('convert_table_Gex.csv', 'Generic_Exterior_Materials.blend')
    }

    def execute(self, context):
        convertMaterials.convert_materials(convertMaterials.convert_dic)
        return {'FINISHED'}


# 外装マテリアルblendファイルのフルパスを返すモジュール
    def ReturnExwAssetPath (source):
        ExwAssetFile = source
        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        defined_asset_libraries = filepaths.asset_libraries
        for defined_asset_library in defined_asset_libraries:
            library_name = defined_asset_library.name
            library_path = Path(defined_asset_library.path)
            blend_files = [fp for fp in library_path.glob("**/*.blend") if fp.is_file()]
            for blend_file in blend_files:
                blend_file_str = str(blend_file)
                if (ExwAssetFile in blend_file_str): 
                    ExwAssetPath = blend_file_str 
                    break
        return ExwAssetPath


# 指定したマテリアルをAppendするモジュール
    def AppendExwMaterial(source, material):
        ExwAssetPath = convertMaterials.ReturnExwAssetPath(source)
        bpy.ops.wm.append(
            filepath = ExwAssetPath,
            filename = material,
            directory = ExwAssetPath + "/Material/")


    def convert_materials(c_dic):
        dirPath = os.path.dirname(__file__)
        for c_mode in c_dic.keys():
            c_table_name = c_dic[c_mode][0]
            c_source = c_dic[c_mode][1]
            fh = open(dirPath + "/" + c_table_name, "r", encoding="utf-8", errors="", newline="" )
            convert_table = csv.reader(fh, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)

            for i in bpy.data.objects:           # オブジェクトを順に評価
                for j in i.material_slots:       # オブジェクトのマテリアルスロットの中を評価し
                    for k in convert_table:           # convertTableを順に評価し
                        if j.material.name == k[0]:  # マテリアル名がCG3Sマテリアルだったら
                            convertMaterials.AppendExwMaterial(c_source, k[1])
                            j.material = bpy.data.materials[k[1]] # マテリアルをBlender用に変更
                            i.name = k[2]        # オブジェクト名を対応した名前に変更
                    fh.seek(0)
            fh.close()


    def chk_materials(convert_table, cg3s_material, material_source_file, blender_material, object_name):
        for i in bpy.data.objects:           # オブジェクトを順に評価
            for j in i.material_slots:       # オブジェクトのマテリアルスロットの中を評価し
                for k in convert_table:           # convertTableを順に評価し
                    if j.material.name == cg3s_material:  # マテリアル名がCG3Sマテリアルだったら
                        convertMaterials.AppendExwMaterial(material_source_file, blender_material)
                        j.material = bpy.data.materials[blender_material] # マテリアルをBlender用に変更
                        i.name = object_name        # オブジェクト名を対応した名前に変更
                fh.seek(0)
        fh.close()







class test(bpy.types.Operator):
    bl_idname = "object.test"
    bl_label = "Test"
    bl_description = "Message Test"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
#        test.pathTest2()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=400)

    def draw(self, context):
        layout = self.layout
        msg = self.pathTest()
        layout.label(text=msg)

    def pathTest2(self):
        dirpath = os.path.dirname(__file__)
        sys.path += [dirpath]
        prefs = bpy.context.preferences.filepaths.font_directory
        return(dirpath)


    def pathTest(self):
        dirpath = os.path.dirname(__file__)
        TableName = "convertTable02.csv"
        fh = open(dirpath + "/" + TableName, "r", encoding="utf-8", errors="", newline="" )

        convertTable = csv.reader(fh, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)
        for i in convertTable:
            for k in i:
                for j in k:
                    ct = j
                    break
        return(ct)



def delete_object_target(arg_objectname=""):
    # 指定オブジェクトを取得する
    # (get関数は対象が存在しない場合 None が返る)
    targetob = bpy.data.objects.get(arg_objectname)
    # 指定オブジェクトが存在するか確認する
    if targetob != None:
       # オブジェクトが存在する場合は削除を行う
        bpy.data.objects.remove(targetob)
    return



def register():
    bpy.utils.register_class(SHToolsPanel)
    bpy.utils.register_class(Initializer)
    bpy.utils.register_class(plantsEliminator)
#    bpy.utils.register_class(test)
    bpy.utils.register_class(convertMaterials)
    

def unregister():
    bpy.utils.unregister_class(SHToolsPanel)
    bpy.utils.unregister_class(Initializer)
    bpy.utils.unregister_class(plantsEliminator)
#    bpy.utils.unregister_class(test)
    bpy.utils.unregister_class(convertMaterials)
    

if __name__ == "__main__":
    register()
