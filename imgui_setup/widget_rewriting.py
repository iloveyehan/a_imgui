import time
import bpy
from imgui_bundle import imgui
from functools import partial
from .mirror_reminder import open_mirror_tip, open_tip
class ImageButton:
    def __init__(self):
        # 默认参数
        self.btn_dict = {
            'image_size': imgui.ImVec2(30.0, 30.0),
            'uv0': imgui.ImVec2(0, 0),
            'uv1': imgui.ImVec2(1, 1),
            'bg_col': imgui.ImVec4(0.1, 0.1, 0.1, 0.0),  # 黑色背景
            'tint_col': imgui.ImVec4(1.0, 1.0, 1.0, 1.0),  # 白色图像
            'tp':''
        }

    def new(self, btn,texture_id, **kwargs):
        """
        自定义的 image_button 函数
        :param texture_id: 图像的纹理 ID
        :param kwargs: 可选参数，用于覆盖默认的 btn_dict
        :return: 是否点击了按钮
        """
        # 合并默认参数和传入的参数
        params = {**self.btn_dict, **kwargs}
        # 调用 imgui.image_button

        clicked = imgui.image_button(
            btn,
            texture_id,
            params['image_size'],
            params['uv0'],
            params['uv1'],
            params['bg_col'],
            params['tint_col']
        )
        if not params['tp']=='':
            if imgui.is_item_hovered():
                imgui.set_tooltip(params['tp']
                )
        # 添加自定义逻辑
        if clicked:
            self.button_handler(btn)
        return clicked
    def button_handler(self,btn):
        name = btn.replace('#', '')
        # print(f'dianjiele {name}')
        # 动态找到处理函数或从映射里取
        func = getattr(self, f"{name}", None)
    
        # 如果函数存在，则执行
        if func and callable(func):
            bpy.ops.ed.undo_push(message="Add an undo step *function may be moved*")
            try:
                func()
            except:
                print('出现错误,可能上下文不对')
        else:
            print(f"未找到处理函数: {name}")
    def btn_set_viewport_display_random(self):
        bpy.ops.kourin.set_viewport_display_random()
    def btn_clean_skeleton(self):
        obj = bpy.context.active_object
        if not obj or obj.type != 'ARMATURE':
            print("请选择一个骨骼对象")
            return
        bpy.ops.kourin.delete_unused_bones()
    def btn_make_skeleton(self):
        
        bpy.ops.kourin.set_bone_display()
    def btn_show_bonename(self):
        bpy.ops.kourin.show_bone_name()

    def btn_add_sk(self):
        bpy.ops.object.shape_key_add(from_mix=False)
    def btn_rm_sk(self):
        bpy.ops.object.shape_key_remove(all=False)
    def btn_mv_sk_up(self):
        bpy.ops.object.shape_key_move(type='UP')
    def btn_mv_sk_down(self):
        bpy.ops.object.shape_key_move(type='DOWN')
    def btn_clear_all_sk_value(self):
        bpy.ops.object.shape_key_clear()
    def btn_solo_active_sk(self):
        bpy.context.object.show_only_shape_key = not bpy.context.object.show_only_shape_key
    def btn_sk_edit_mode(self):
        bpy.context.object.use_shape_key_edit_mode = not bpy.context.object.use_shape_key_edit_mode
class TextButton:
    def __init__(self):
        # 默认参数
        self.btn_dict = {
            # 'size': imgui.ImVec2(20.0, 20.0),
            'tp':'',
        }

    def new(self, btn, **kwargs):
        """
        自定义的 image_button 函数
        :param texture_id: 图像的纹理 ID
        :param kwargs: 可选参数，用于覆盖默认的 btn_dict
        :return: 是否点击了按钮
        """
        # 合并默认参数和传入的参数
        params = {**self.btn_dict, **kwargs}
        # 调用 imgui.image_button

        clicked = imgui.button(
            btn,
            # params['size'],
        )
        if not params['tp']=='':
            if imgui.is_item_hovered():
                imgui.set_tooltip(params['tp']
                )
        # 添加自定义逻辑
        if clicked:
            self.button_handler(btn)
        return clicked
    def button_handler(self,btn):
        
        print('处理函数:',btn)
        # print(f'dianjiele {name}')
        # 动态找到处理函数或从映射里取
        func = getattr(self, f"{btn.split('##')[-1]}", None)

        # 如果函数存在，则执行
        if func and callable(func):
            bpy.ops.ed.undo_push(message="Add an undo step *function may be moved*")
            bpy.app.timers.register(partial(func, btn))  
        else:
            print(f"未找到处理函数: {btn}")
    def btn_vg_mirror(self,btn):
        bpy.ops.kourin.vg_mirror_weight()
        pass
    def btn_vg_left(self,btn):
        print(111)
        from .imgui_global import GlobalImgui
        if not (GlobalImgui.get().vg_middle or GlobalImgui.get().vg_mul):
            print('return' , GlobalImgui.get().vg_middle, GlobalImgui.get().vg_mul)
            return None
        GlobalImgui.get().vg_left=True
        GlobalImgui.get().vg_right=not GlobalImgui.get().vg_left
        print('当前btn_vg_left',not GlobalImgui.get().vg_left,GlobalImgui.get().vg_right)
    def btn_vg_right(self,btn):
        from .imgui_global import GlobalImgui
        if not (GlobalImgui.get().vg_middle or GlobalImgui.get().vg_mul):
            return None
        GlobalImgui.get().vg_right=True
        GlobalImgui.get().vg_left=not GlobalImgui.get().vg_right
        print('当前btn_vg_r',not GlobalImgui.get().vg_right,GlobalImgui.get().vg_left)
    def btn_vg_select(self,btn):
        from .imgui_global import GlobalImgui
        if not GlobalImgui.get().vg_mul:
            return None
        GlobalImgui.get().vg_select=not GlobalImgui.get().vg_select
    def btn_vg_middle(self,btn):
        from .imgui_global import GlobalImgui
        if GlobalImgui.get().vg_middle:
            if GlobalImgui.get().vg_left:
                GlobalImgui.get().last_side='vg_left'
            if GlobalImgui.get().vg_right:
                GlobalImgui.get().last_side='vg_right'
            if not GlobalImgui.get().vg_mul:
                GlobalImgui.get().vg_left=False
                GlobalImgui.get().vg_right=False
        else:
            if not (GlobalImgui.get().vg_left and GlobalImgui.get().vg_right):
                if len(GlobalImgui.get().last_side):
                    if GlobalImgui.get().last_side=='vg_left':
                        GlobalImgui.get().vg_left=True
                    elif GlobalImgui.get().last_side=='vg_right':
                        GlobalImgui.get().vg_right=True
                    else:
                        GlobalImgui.get().vg_left=True
                else:
                    GlobalImgui.get().vg_left=True
                
        GlobalImgui.get().vg_middle=not GlobalImgui.get().vg_middle
    def btn_vg_mul(self,btn):
        from .imgui_global import GlobalImgui
        if GlobalImgui.get().vg_mul:
            GlobalImgui.get().vg_select=False
        if GlobalImgui.get().vg_mul:
            if GlobalImgui.get().vg_left:
                GlobalImgui.get().last_side='vg_left'
            if GlobalImgui.get().vg_right:
                GlobalImgui.get().last_side='vg_right'
            if not GlobalImgui.get().vg_middle:
                GlobalImgui.get().vg_left=False
                GlobalImgui.get().vg_right=False
        else:
            if not (GlobalImgui.get().vg_left and GlobalImgui.get().vg_right):
                if len(GlobalImgui.get().last_side):
                    if GlobalImgui.get().last_side=='vg_left':
                        GlobalImgui.get().vg_left=True
                    elif GlobalImgui.get().last_side=='vg_right':
                        GlobalImgui.get().vg_right=True
                    else:
                        GlobalImgui.get().vg_left=True
                else:
                    GlobalImgui.get().vg_left=True

        GlobalImgui.get().vg_mul=not GlobalImgui.get().vg_mul
    
    def btn_pose_to_reset(self,btn):
        from .imgui_global import GlobalImgui
        # bpy.app.timers.register(partial(on_shape_key_index_change,self))
        if bpy.context.active_object.type!="ARMATURE":
            setattr(GlobalImgui.get(), f"{btn}", True)
            setattr(GlobalImgui.get(), f"{btn}_time", time.time())
            return None
        bpy.ops.kourin.pose_to_reset()
    def btn_merge_armature(self,btn):
        from .imgui_global import GlobalImgui
        # bpy.app.timers.register(partial(on_shape_key_index_change,self))
        if not armature_poll():
            setattr(GlobalImgui.get(), f"{btn}", True)
            setattr(GlobalImgui.get(), f"{btn}_time", time.time())
            return None
        # bpy.app.timers.register(partial(on_shape_key_index_change,self))
        bpy.ops.kourin.merge_armatures()
        # bpy.ops.kourin.merge_armatures()
    def btn_rename_armature(self,btn):
        from .imgui_global import GlobalImgui
        # bpy.app.timers.register(partial(on_shape_key_index_change,self))
        if not armature_poll():
            setattr(GlobalImgui.get(), f"{btn}", True)
            setattr(GlobalImgui.get(), f"{btn}_time", time.time())
            print('return')
            return None
        # bpy.app.timers.register(partial(on_shape_key_index_change,self))
        bpy.ops.kourin.rename_armatures()
        # bpy.ops.kourin.merge_armatures()
def armature_poll():
    if bpy.context.active_object is None:
        return False
    armatures = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
    return (len(armatures) == 2 and bpy.context.active_object.type == 'ARMATURE')