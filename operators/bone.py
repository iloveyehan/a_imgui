import bpy
from typing import List, Optional, Dict, Set
from pathlib import Path
from ..utils.armature import finde_common_bones, pose_to_reset



from ..common.class_loader.auto_load import ClassAutoloader
vrc_bone_ops=ClassAutoloader(Path(__file__))
def reg_vrc_bone_ops():
    vrc_bone_ops.init()
    vrc_bone_ops.register()
def unreg_vrc_bone_ops():
    vrc_bone_ops.unregister()
class DeleteUnusedBonesOperator(bpy.types.Operator):
    """删除没有权重的骨骼及其子骨骼，保留有直接子骨骼权重的主骨骼"""
    bl_idname = "kourin.delete_unused_bones"
    bl_label = "Delete Unused Bones"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        obj=bpy.context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def get_bone_hierarchy(self, bone):
        """递归获取骨骼及其所有子骨骼"""
        bones = [bone]
        for child in bone.children:
            bones.extend(self.get_bone_hierarchy(child))
        return bones

    def has_vertex_weights(self, armature, bone_name):
        """检查骨骼是否绑定到任何顶点"""
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                for modifier in obj.modifiers:
                    if modifier.type == 'ARMATURE' and modifier.object == armature:
                        if obj.vertex_groups.find(bone_name) >= 0:
                            return True
        return False

    def should_keep_bone(self, armature, bone):
        """判断骨骼是否需要保留"""
        # 如果骨骼自身有权重
        if self.has_vertex_weights(armature, bone.name):
            return True
        
        # 如果直接子骨骼中有任何一个有权重
        for child in bone.children:
            if self.has_vertex_weights(armature, child.name):
                return True
        
        return False

    def execute(self, context):
        armature = context.object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected!")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='EDIT')
        bones_to_delete = []

        # 第一遍收集所有可能删除的骨骼
        for bone in armature.data.edit_bones:
            # 检查是否需要保留该骨骼
            if not self.should_keep_bone(armature, bone):
                bones_to_delete.append(bone.name)
        for bone_name in bones_to_delete:
            if bone_name in armature.data.edit_bones:  # 检查骨骼是否存在
                armature.data.edit_bones.remove(armature.data.edit_bones[bone_name])  # 删除骨骼

        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, "未使用的骨骼已删除！保留有直接子节点权重的父级骨骼。")
        return {'FINISHED'}

class SetBoneDisplayOperator(bpy.types.Operator):
    """将激活骨架视图显示为棍形，其他骨骼显示为八面锥"""
    bl_idname = "kourin.set_bone_display"
    bl_label = "设置骨骼显示方式"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        # 获取当前激活的骨架对象
        active_armature = context.active_object
        if not active_armature or active_armature.type != 'ARMATURE':
            self.report({'WARNING'}, "请选择一个骨架对象")
            return {'CANCELLED'}
        # 遍历场景中的所有骨架对象
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                # 如果是激活的骨架，设置显示为棍形
                if obj == active_armature:
                    obj.data.display_type = 'STICK'
                # 其他骨架设置为八面锥
                else:
                    obj.data.display_type = 'OCTAHEDRAL'
        self.report({'INFO'}, "骨骼显示方式已设置")
        return {'FINISHED'}
class KourinSetViewportDisplayRandomOperator(bpy.types.Operator):
    """将激活骨架视图显示为棍形，其他骨骼显示为八面锥"""
    bl_idname = "kourin.set_viewport_display_random"
    bl_label = "设置物体显示方式为随机"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.color_type = 'RANDOM'
        # context.space_data.shading.color_type = 'RANDOM'
        return {'FINISHED'}
    
class KourinShowBoneNameOperator(bpy.types.Operator):
    """显示骨骼名称"""
    bl_idname = "kourin.show_bone_name"
    bl_label = "设置物体显示方式为随机"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj=bpy.context.active_object
        if obj.type=='ARMATURE':
            for b in context.selected_objects:
                if b.type=='ARMATURE':
                    b.data.show_names = not obj.data.show_names
        return {'FINISHED'}

class KourinPoseToReset(bpy.types.Operator):
    bl_idname = 'kourin.pose_to_reset'
    bl_label = '应用pose模式的调整'
    bl_description = '应用pose模式的调整,设置为默认姿势'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'ARMATURE'
    def execute(self, context):
        armature=bpy.context.object
        mode=bpy.context.mode
        pose_to_reset(armature)
        bpy.ops.object.mode_set(mode=mode)
        self.report({'INFO'}, "应用完成")
        return {'FINISHED'}
class Kourin_merge_armatures(bpy.types.Operator):
    """Merge two selected Armature objects into one, preserving bone hierarchy and weights"""
    bl_idname = "kourin.merge_armatures"
    bl_label = "Merge Armatures"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # 确保恰好两个骨架被选中，且有一个活动对象
        if context.active_object is None:
            return False
        armatures = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
        return (len(armatures) == 2 and context.active_object.type == 'ARMATURE')
    
    def execute(self, context):
        active_arm = context.active_object
        # 找到第二个被选中的骨架对象
        others = [obj for obj in context.selected_objects if obj != active_arm and obj.type == 'ARMATURE']
        if len(others) != 1:
            self.report({'WARNING'}, "需要选中恰好两个骨架对象")
            return {'CANCELLED'}
        other_arm = others[0]
  
        # 步骤 1：查找重名骨骼并记录其子骨骼
        dupes = []
        child_map = {}
        for bone in other_arm.data.bones:
            if bone.name in active_arm.data.bones.keys():
                dupes.append(bone.name)
                # child_map[bone.name] = [ch.name for ch in bone.children]
                child_map[bone.name] = [(ch.name, ch.use_connect) for ch in bone.children]
        
        # 步骤 2：进入编辑模式删除重名骨骼
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = other_arm
        other_arm.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        for name in dupes:
            if name in other_arm.data.edit_bones:
                bone = other_arm.data.edit_bones[name]
                other_arm.data.edit_bones.remove(bone)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # （可选）应用骨架的变换以避免网格移动
        # bpy.ops.object.select_all(action='DESELECT')
        # active_arm.select_set(True)
        # context.view_layer.objects.active = active_arm
        # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        # other_arm.select_set(True)
        # context.view_layer.objects.active = other_arm
        # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        # 步骤 3：将两个骨架合并（活动骨架为活跃对象）
        bpy.ops.object.select_all(action='DESELECT')
        active_arm.select_set(True)
        other_arm.select_set(True)
        context.view_layer.objects.active = active_arm
        bpy.ops.object.join()  # 对象模式下执行合并:contentReference[oaicite:7]{index=7}
        
        # 步骤 4：在合并后的骨架中重新设置子骨骼的父级
        bpy.ops.object.mode_set(mode='EDIT')
        for name in dupes:
            if name not in active_arm.data.edit_bones:
                continue
            parent_bone = active_arm.data.edit_bones[name]
            # for child_name in child_map.get(name, []):
            #     if not child_name:
            #         continue
            #     if child_name in active_arm.data.edit_bones:
            #         child = active_arm.data.edit_bones[child_name]
            #         if child.parent is None or child.parent.name != parent_bone.name:
            #             child.parent = parent_bone
            # 修改后：
            for child_name, is_connected in child_map.get(name, []):
                if not child_name:
                    continue
                if child_name in active_arm.data.edit_bones:
                    child = active_arm.data.edit_bones[child_name]
                    child.parent = parent_bone
                    child.use_connect = is_connected
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 步骤 5：更新网格对象的骨骼修改器和父级
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                # 更新指向旧骨架的 Armature Modifier 为新骨架
                for mod in obj.modifiers:
                    # if mod.type == 'ARMATURE' and mod.object == other_arm:
                    if mod.type == 'ARMATURE':
                        mod.object = active_arm
                # 重新设置父级为新骨架，保持世界变换不变
                # if obj.parent == other_arm:
                orig_matrix = obj.matrix_world.copy()
                parent_type = obj.parent_type
                parent_bone = obj.parent_bone
                obj.parent = active_arm
                obj.parent_type = parent_type
                obj.parent_bone = parent_bone
                obj.matrix_world = orig_matrix
        return {'FINISHED'}
class Kourin_rename_armatures(bpy.types.Operator):
    """把两个骨架的相同部位的骨骼统一命名,以激活的为准"""
    bl_idname = "kourin.rename_armatures"
    bl_label = "Merge Armatures"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # 确保恰好两个骨架被选中，且有一个活动对象
        if context.active_object is None:
            return False
        armatures = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
        return (len(armatures) == 2 and context.active_object.type == 'ARMATURE')
    
    def execute(self, context):
        finde_common_bones()
        return {'FINISHED'}