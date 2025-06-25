import copy
import ctypes
from ctypes import wintypes
# from OpenGL import GL as gl
import OpenImageIO as oiio

import numpy as np
# import gpu
import gpu
import typing
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

import sys
from pathlib import Path

from .operators.color_picker import Imgui_Color_Picker_Imgui

from .operators.base_ops import BaseDrawCall

from .operators.vertex_group import reg_vrc_vg_ops, unreg_vrc_vg_ops
current_folder=Path(__file__).parent.absolute()
sys.path.append(str(current_folder))
# from .imgui_setup.hook_ime import hook_ime,restore_wndproc
from .imgui_setup.shapekey import shapkey_widget
from .imgui_setup.vertex_group import vertex_group_widget
from .imgui_setup.selectable_input import selectable_input
from .widget import get_wheeL_tri, color_bar, colorpicker, color_palette,picker_switch_button
from .utils.utils import get_brush_color_based_on_mode,get_prefs,im_pow
from mathutils import Vector
from .pref import Imgui_Color_Picker_Preferences
import time
import bpy
import sys
from imgui_bundle import imgui
from imgui_bundle import ImVec2, ImVec4
from .imgui_setup.imgui_global import GlobalImgui
from .imgui_setup.mirror_reminder import open_mirror_tip, open_tip
from .render import Renderer as BlenderImguiRenderer

bl_info = {
    "name": "a_imgui",
    "author": "cupcko",
    "version": (1, 0,2),
    "blender": (4, 0, 0),
    "location": "3D View,Image Editor",
    "description": "123",
    "category": "3D View"
}


class Imgui_Window_Imgui(bpy.types.Operator, BaseDrawCall):
    bl_idname = "imgui.window"
    bl_label = "color picker"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        return 1

    def draw(self, context: bpy.types.Context):
        if context.area!=self.area:
            # print(context.area,self.area)
            pass
            return
        if context.region!=self.region:
            # print(context.region,self.region)
            # print('region不匹配')
            # return
            pass
        # print('draw',time.time())
        self.cover = False
        self.cover_style_editor = False
        _main_window,_main_x=imgui.begin("VRC窗口", self.main_window[0], )


        imgui.set_next_item_open(True, cond=imgui.Cond_.once)
        if imgui.collapsing_header("预处理"):
        # if imgui.tree_node("预处理"):
            if GlobalImgui.get().image_btn.new("##btn_set_viewport_display_random", 
                                self.btn_set_viewport_display_random,tp='设置每个物体不同颜色'):pass
            imgui.same_line()
            if GlobalImgui.get().image_btn.new("##btn_clean_skeleton", 
                                self.btn_clean_skeleton,tp='清理选中的骨骼,\n移除没有权重的骨骼'):pass
            imgui.same_line()
            if GlobalImgui.get().image_btn.new("##btn_make_skeleton", 
                                self.btn_make_skeleton,tp='设置激活骨骼为棍型\n其他骨骼为八面锥'):pass
            imgui.same_line()
            if GlobalImgui.get().image_btn.new("##btn_show_bonename", 
                                self.btn_show_bonename,tp='把当前POSE设置为默认POSE\n需要选中骨骼'):pass
            if GlobalImgui.get().text_btn.new('应用##btn_pose_to_reset',tp='把当前POSE设置为默认POSE\n注意:需要选中骨骼'):
                pass
            open_tip('应用##btn_pose_to_reset','需要选择骨骼')
            imgui.same_line()
            if GlobalImgui.get().text_btn.new('改名##btn_rename_armature',tp='把骨骼命名统一\n以激活骨架为准\n注意:可能有错误,需要检查'):
                pass
            open_tip('改名##btn_rename_armature','需要选择两个骨架')
            imgui.same_line()
            if GlobalImgui.get().text_btn.new('合并##btn_merge_armature',tp='合并骨架\n注意:以激活骨架为主'):
                pass
            open_tip('合并##btn_merge_armature','需要选择两个骨架')

        vertex_group_widget(self)
        shapkey_widget(self)

        imgui.show_demo_window()
        if imgui.button("打开新窗口"):
            GlobalImgui.get().show_new_window[0] = True  # 点击按钮后设置为 True
        if imgui.button("打开镜像提醒"):
            GlobalImgui.get().show_mirror_reminder_window = True
            GlobalImgui.get().mirror_reminder_window_open_time = time.time()  # 记录当前时间
        
        self.track_any_cover()
        # 如果变量为 True，就绘制新窗口
        # print('opened',GlobalImgui.get().show_new_window,hasattr(GlobalImgui.get(),'show_new_window'))
        
        if hasattr(GlobalImgui.get(),'show_new_window') and GlobalImgui.get().show_new_window[0]:
            opened, _x=imgui.begin("新窗口", GlobalImgui.get().show_new_window[0],imgui.WindowFlags_.no_nav|imgui.WindowFlags_.no_focus_on_appearing)
            # print('新窗口',GlobalImgui.get().show_new_window,hasattr(GlobalImgui.get(),'show_new_window')) 
            imgui.text("这是一个新窗口！")
            imgui.text(f"item_spacing:{imgui.get_style().item_spacing}")
            imgui.text(f"item_inner_spacing:{imgui.get_style().item_inner_spacing}")
            imgui.text(f"window_padding:{imgui.get_style().window_padding}")
            _,GlobalImgui.get().title_bg_color=imgui.color_edit4("窗口标题##title_bg_color", GlobalImgui.get().title_bg_color)
            _,GlobalImgui.get().title_bg_active_color=imgui.color_edit4("窗口标题激活##title_bg_active_color", GlobalImgui.get().title_bg_active_color)
            _,GlobalImgui.get().title_bg_collapsed_color=imgui.color_edit4("窗口折叠##title_bg_collapsed_color", GlobalImgui.get().title_bg_collapsed_color)
            _,GlobalImgui.get().window_bg_color=imgui.color_edit4("窗口背景##window_bg_color", GlobalImgui.get().window_bg_color)
            _,GlobalImgui.get().frame_bg_color=imgui.color_edit4("frame##frame_bg_color", GlobalImgui.get().frame_bg_color)
            _,GlobalImgui.get().button_color=imgui.color_edit4("按钮##button_color", GlobalImgui.get().button_color)
            _,GlobalImgui.get().button_active_color=imgui.color_edit4("按钮激活##button_active_color", GlobalImgui.get().button_active_color)
            _,GlobalImgui.get().button_hovered_color=imgui.color_edit4("按钮悬浮##button_hovered_color", GlobalImgui.get().button_hovered_color)
            _,GlobalImgui.get().header_color=imgui.color_edit4("子标题##header_color", GlobalImgui.get().header_color)
            _,GlobalImgui.get().child_bg=imgui.color_edit4("子集##child_bg", GlobalImgui.get().child_bg)
            if imgui.button("关闭"):
                GlobalImgui.get().show_new_window[0] = False  # 手动关闭按钮
            # 你也可以检测窗口自带的关闭按钮：
            self.track_any_cover_style_editor()
            imgui.end()
            # print(GlobalImgui.get().show_new_window[0],opened,_x)
            if (not opened) or (not _x):
                GlobalImgui.get().show_new_window[0] =False
        open_mirror_tip('镜像没开')
        imgui.end()

        if not _main_x:
            # 关闭键
            print('not _main_x:')
            self.show_window_imgui = False

    def invoke(self, context, event):
        if len(GlobalImgui.get().imgui_vrc_instance):
            GlobalImgui.get().imgui_vrc_instance[0].should_close=True
            GlobalImgui.get().imgui_vrc_instance.clear()
        GlobalImgui.get().imgui_vrc_instance.append(self)
        print(GlobalImgui.get().imgui_vrc_instance)
        self.should_close=False
        self.cover = False
        
        self.cover_style_editor = False
        self.show_mirror_reminder_window = False
        self.mirror_reminder_window_open_time = None  # 记录窗口打开时间

        self.show_window_imgui = True
        self.area=context.area
        self.region=context.region
        self.region_capture=None
        self.init_imgui(context)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
    def refresh(self):
        for area in bpy.context.screen.areas:
            if area.type in ['VIEW_3D','IMAGE_EDITOR']:
                area.tag_redraw()
    def modal(self, context, event):
        if self.should_close:
            self.call_shutdown_imgui()
            self.refresh()
            return {'FINISHED'}
        # print(self)
        if not self.show_window_imgui or not GlobalImgui.get().debug:
            print('not debug')
            self.call_shutdown_imgui()
            self.refresh()
            return {'FINISHED'}
        # print('modal imgui handle',self.imgui_handle)
        if context.area:
            context.area.tag_redraw()

        gx, gy = event.mouse_x, event.mouse_y

        # —— 动态查找当前鼠标在 screen 哪个 region 上 —— 
        region = None
        for area in context.window.screen.areas:
            for r in area.regions:
                # r.x, r.y 是 region 在窗口中的左下角坐标
                if (gx >= r.x and gx <= r.x + r.width
                and gy >= r.y and gy <= r.y + r.height):
                    region = r
                    break
            if region:
                break

        # 找不到就透传，让 Blender 处理
        if region is None:
            # print('no region')
            return {'PASS_THROUGH'}
        
        if region:
            region.tag_redraw()
            # if self.region_capture==None:
            if self.region==None:
                print('没有region',self.region,region)
                self.region=region
                # self.region_capture=region
        else:
            print('else no region')
        # —— 计算区域内坐标 —— 
        mx = gx - region.x
        my = gy - region.y
        self.mpos=(mx,my)

        # —— 越界检测（可选） —— 
        if mx < 0 or mx > region.width or my < 0 or my > region.height:
            print('越界检测')
            return {'PASS_THROUGH'}

        # if event.type in {"ESC"}:
        #     print("ESC", self.area, bpy.context.area)
        #     self.call_shutdown_imgui()
        #     self.refresh() 
        #     return {'FINISHED'}
        if event.type == 'MIDDLEMOUSE':
            return {'PASS_THROUGH'}
        # 修改右键点击处理（关键修改）
        if event.type=='TAB':
            return {'PASS_THROUGH'}
        if event.type == 'RIGHTMOUSE':
            if  self.cover and event.value == 'PRESS':
                # 发送右键释放事件到ImGui
                io = imgui.get_io()
                io.add_mouse_button_event(1, True)  # 无论点击哪里都发送释放事件
  
                return {'RUNNING_MODAL'}
            else:
                io = imgui.get_io()
                io.add_mouse_button_event(1, False)
                print('non right mouse and cover')
                return {'PASS_THROUGH'}
        #撤销事件
        if (event.shift == False) and (event.ctrl == True):
            if (event.type == "Z")and event.value == 'RELEASE':
       
                try:
                    bpy.ops.ed.undo()
                except Exception as error:
                    print(error)
                print('undo')
                return {"RUNNING_MODAL"}

        self.poll_mouse(context, event)
        
        self.poll_events(context, event)
        # print([x for x in gc.get_objects() if isinstance(x, Imgui_Window_Imgui)])
        # print(self.cover ,self.cover_style_editor)
        return {"RUNNING_MODAL" if self.cover or self.cover_style_editor else "PASS_THROUGH"}  # 焦点决策

    def cancel(self, context):
        print("Operator 被 Blender 取消，执行清理")
        self.call_shutdown_imgui()
        self.refresh()
        return {'CANCELED'}
class TranslationHelper():
    def __init__(self, name: str, data: dict, lang='zh_CN'      ):
        self.name = name
        self.translations_dict = dict()

        for src, src_trans in data.items():
            key = ("Operator", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans
            key = ("*", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans

    def register(self):
        try:
            bpy.app.translations.register(self.name, self.translations_dict)
        except(ValueError):
            pass

    def unregister(self):
        bpy.app.translations.unregister(self.name)

_addon_properties = {
bpy.types.Scene: {
        # "ari_edge_smooth_settings": bpy.props.PointerProperty(type=AriEdgeSmoothSettings),
        # 'ari_transfer_position_settings':bpy.props.PointerProperty(type=AriTransferPositionSettings),
        
},
}
def add_properties(property_dict: dict[typing.Any, dict[str, typing.Any]]):
    for cls, properties in property_dict.items():
        for name, prop in properties.items():
            setattr(cls, name, prop)


# support removing properties in a declarative way
def remove_properties(property_dict: dict[typing.Any, dict[str, typing.Any]]):
    for cls, properties in property_dict.items():
        for name in properties.keys():
            if hasattr(cls, name):
                delattr(cls, name)

from . import zh_CN
Colorpickerzh_CN = TranslationHelper('Colorpickerzh_CN', zh_CN.data)
Colorpickerzh_HANS = TranslationHelper('Colorpickerzh_HANS', zh_CN.data, lang='zh_HANS')

from .utils.utils import register_keymaps,unregister_keymaps
from .msgbus_handlers import reg_msgbus_handler,unreg_msgbus_handler
from .operators.bone import reg_vrc_bone_ops,unreg_vrc_bone_ops
from .keymap import keys
def register():
    import bpy
# 获取所有已安装的插件
    addons = bpy.context.preferences.addons
    # 遍历并打印插件名称
    for addon in addons:
        print(addon.module)
    GlobalImgui.get().debug=True
    if bpy.app.version < (4, 0, 0):
        Colorpickerzh_CN.register()
    else:
        Colorpickerzh_CN.register()
        Colorpickerzh_HANS.register()
    reg_msgbus_handler()
    reg_vrc_bone_ops()
    reg_vrc_vg_ops()
    bpy.utils.register_class(Imgui_Color_Picker_Imgui)
    bpy.utils.register_class(Imgui_Window_Imgui)
    bpy.utils.register_class(Imgui_Color_Picker_Preferences)
    global keymaps
    keymaps = register_keymaps(keys['IMGUI_COLOR_PICKER'])
    add_properties(_addon_properties)

def unregister():
    remove_properties(_addon_properties)
    # GlobalImgui.get().debug=Falser
    wm = bpy.context.window_manager
    if 'IMGUI_OT_window' in wm.operators:
        print('IMGUI_OT_window')
        wm.operators['IMGUI_OT_window'].cancel(bpy.context)
    if bpy.app.version < (4, 0, 0):
        Colorpickerzh_CN.unregister()
    else:
        Colorpickerzh_CN.unregister()
        Colorpickerzh_HANS.unregister()
    bpy.utils.unregister_class(Imgui_Color_Picker_Imgui)
    bpy.utils.unregister_class(Imgui_Window_Imgui)
    bpy.utils.unregister_class(Imgui_Color_Picker_Preferences)
    unreg_vrc_bone_ops()
    unreg_vrc_vg_ops()
    unreg_msgbus_handler()
    global keymaps
    if keymaps:
        unregister_keymaps(keymaps)
