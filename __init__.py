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
color_hsv = [0, 0, 0]
color_rgb = [0, 0, 0]
colors = []
color_palette_size = 40
color_palette_dict = {}
# colorbar 颜色拾取处理,拖动bar的最后一个色彩存入colors[0]
color_tmp = []

values = [0.0, 0.60, 0.35, 0.9, 0.70, 0.20, 0.0]
Color_Picker_Imgui_color = (114, 144, 154, 200)
Color_Picker_Imgui_alpha_preview = True
Color_Picker_Imgui_alpha_half_preview = False
Color_Picker_Imgui_drag_and_drop = True
Color_Picker_Imgui_options_menu = True
Color_Picker_Imgui_hdr = False
bl_info = {
    "name": "a_imgui",
    "author": "cupcko",
    "version": (1, 0,2),
    "blender": (4, 0, 0),
    "location": "3D View,Image Editor",
    "description": "123",
    "category": "3D View"
}
# print(dir(imgui.Key))
buf = ["MyItem"]

# 状态对象
class StringEditState:
    def __init__(self):
        self.text = "Click to edit"
        self.editing = False
        self.last_click_time = 0.0

state = StringEditState()


def inbox(x, y, w, h, mpos):
    if (x < mpos[0] < x + w) and (y - h < mpos[1] < y):
        return True
    return False


def imgui_handler_remove(handle):
    GlobalImgui.get().handler_remove(handle)


class BaseDrawCall:
    # 定义键盘按键映射，键是字符串表示，值是 ImGui 中定义的键码
    key_map = {
        'TAB': imgui.Key.tab,
        'LEFT_ARROW': imgui.Key.left_arrow,
        'RIGHT_ARROW': imgui.Key.right_arrow,
        'UP_ARROW': imgui.Key.up_arrow,
        'DOWN_ARROW': imgui.Key.down_arrow,
        'HOME': imgui.Key.home,
        'END': imgui.Key.end,
        'INSERT': imgui.Key.insert,
        'DEL': imgui.Key.delete,
        'BACK_SPACE': imgui.Key.backspace,
        'SPACE': imgui.Key.space,
        'RET': imgui.Key.enter,
        'NUMPAD_ENTER': imgui.Key.enter,
        'ESC': imgui.Key.escape,
        'PAGE_UP': imgui.Key.page_up,
        'PAGE_DOWN': imgui.Key.page_down,
        'A': imgui.Key.a,
        'C': imgui.Key.c,
        'V': imgui.Key.v,
        'X': imgui.Key.x,
        'Y': imgui.Key.y,
        'Z': imgui.Key.z,
        'LEFT_CTRL': imgui.Key.left_ctrl,
        'RIGHT_CTRL': imgui.Key.right_ctrl,
        'LEFT_ALT': imgui.Key.left_alt,
        'RIGHT_ALT': imgui.Key.right_alt,
        'LEFT_SHIFT': imgui.Key.left_shift,
        'RIGHT_SHIFT': imgui.Key.right_shift,
        'OSKEY': imgui.Key.comma,
    }

    def __init__(self):
        self.c = .0
        self.mpos = (0, 0)  # 初始化鼠标位置
    def init_imgui(self, context):
        self.main_window=[True,True]
        self._key_state = {}

        self.clipboard=''
        self._next_texture_id = 2#1或者0是fonts
        self.btn_set_viewport_display_random=self.load_icon_texture("material.png")
        self.btn_clean_skeleton=self.load_icon_texture("brush_data.png")
        self.btn_make_skeleton=self.load_icon_texture("armature_data.png")
        self.btn_show_bonename=self.load_icon_texture("group_bone.png")
        self.btn_pose_to_reset=self.load_icon_texture("group_bone.png")
        self.btn_add_sk=self.load_icon_texture("add.png")
        self.btn_rm_sk=self.load_icon_texture("remove.png")
        self.btn_sk_special=self.load_icon_texture("downarrow_hlt.png")
        self.btn_mv_sk_up=self.load_icon_texture("tria_up.png")
        self.btn_mv_sk_down=self.load_icon_texture("tria_down.png")
        self.btn_clear_all_sk_value=self.load_icon_texture("panel_close.png")
        self.btn_solo_active_sk=self.load_icon_texture("solo_off.png")
        self.btn_sk_edit_mode=self.load_icon_texture("editmode_hlt.png")
        
        #hook ime
        # hook_ime()
        if self.area.type=='VIEW_3D':
            self.imgui_handle = GlobalImgui.get().handler_add(self.draw, bpy.types.SpaceView3D, self)
        elif self.area.type=='IMAGE_EDITOR':
            self.imgui_handle = GlobalImgui.get().handler_add(self.draw, bpy.types.SpaceImageEditor, self)
        print('imgui handle',self.imgui_handle)       
    def draw(self, context):
        pass
    def load_icon(self,path):
        image=bpy.data.images.load(path)
        image.gl_load()
        BlenderImguiRenderer._texture_cache[image.bindcode] = gpu.texture.from_image(image)
        return image.bindcode
    
    # --- load_png_to_gpu_texture 函数定义 (复制粘贴上述完整函数代码) ---
    def load_png_to_gpu_texture(self, filepath: str) -> gpu.types.GPUTexture:
        """
        使用OpenImageIO和NumPy将本地PNG图像加载为gpu.types.GPUTexture。

        此函数不使用PIL或bpy.data.images.load()。

        Args:
            filepath (str): 本地PNG图像文件的完整路径。

        Returns:
            gpu.types.GPUTexture: 加载的GPU纹理对象。
            如果加载失败，则返回None。
        """
        if oiio is None:
            print("OpenImageIO模块未加载，无法执行图像导入。")
            return None

        img_input = oiio.ImageInput.open(filepath)
        if not img_input:
            print(f"错误：无法打开图像文件或文件格式不受支持 - {filepath}")
            return None

        try:
            # 获取图像规格
            spec = img_input.spec()
            width = spec.width
            height = spec.height
            nchannels = spec.nchannels
            oiio_format = spec.format

            print(f"图像规格：{width}x{height}, 通道数：{nchannels}, OIIO格式：{oiio_format}")

            pixels_np = img_input.read_image(format=oiio.TypeDesc("uint8"))
            if pixels_np is None:
                print(f"错误：无法读取图像像素数据或文件格式不受支持 - {filepath}")
                return None
                # print(f"错误：无法读取图像像素数据 - {filepath}")
                # return None
                # 确保读取到的NumPy数组形状与预期一致
            if pixels_np.shape != (height, width, nchannels):
                print(f"警告：读取到的图像数据形状不匹配预期。预期：({height}, {width}, {nchannels})，实际：{pixels_np.shape}")
                nchannels = pixels_np.shape[2] if len(pixels_np.shape) == 3 else 1
            # 通道处理
            if nchannels == 3:
                print("检测到3通道RGB图像，添加一个完全不透明的Alpha通道。")
                rgba_pixels = np.zeros((height, width, 4), dtype=np.uint8)
                rgba_pixels[:, :, :3] = pixels_np[:, :, :3]
                rgba_pixels[:, :, 3] = 255
                final_pixels_np = rgba_pixels
                target_channels = 4
                gpu_format_str = 'RGBA8'
            elif nchannels == 4:
                print("图像已包含Alpha通道。")
                final_pixels_np = pixels_np
                target_channels = 4
                gpu_format_str = 'RGBA8'
            elif nchannels == 1:
                print("检测到1通道灰度图像，转换为RGBA。")
                rgba_pixels = np.zeros((height, width, 4), dtype=np.uint8)
                rgba_pixels[:, :, 0] = pixels_np[:, :, 0]
                rgba_pixels[:, :, 1] = pixels_np[:, :, 0]
                rgba_pixels[:, :, 2] = pixels_np[:, :, 0]
                rgba_pixels[:, :, 3] = 255
                final_pixels_np = rgba_pixels
                target_channels = 4
                gpu_format_str = 'RGBA8'
            else:
                print(f"警告：不支持的通道数 ({nchannels})。尝试使用原始数据。")
                final_pixels_np = pixels_np
                target_channels = nchannels
                if nchannels == 1:
                    gpu_format_str = 'R8'
                elif nchannels == 2:
                    gpu_format_str = 'RG8'
                else:
                    gpu_format_str = 'RGBA8'

            # 扁平化数据
            float_pixels = final_pixels_np.astype(np.float32) / 255.0
            flattened_pixels = float_pixels.ravel()
            # flattened_pixels = final_pixels_np.ravel()

            # 创建 GPU Buffer
            gpu_buffer = gpu.types.Buffer('FLOAT', (width * height * target_channels,), flattened_pixels)

            # 创建 GPU 纹理
            gpu_texture = gpu.types.GPUTexture(size=(width, height), format=gpu_format_str, data=gpu_buffer)
            print(f"成功创建GPUTexture：尺寸 {width}x{height}, 格式 {gpu_format_str}")

            return gpu_texture

        except Exception as e:
            print(f"在加载PNG到GPU纹理时发生错误：{e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            img_input.close()

    def load_icon_texture(self,path):
        print('载入图像路径:',Path(__file__))
        tex=self.load_png_to_gpu_texture(str(Path(__file__).parent/'icons'/path))
        # bindcode = tex.gl_load()
        texture_id = self._next_texture_id
        self._next_texture_id += 1
        # 你这边的缓存机制
        # texture_id = gl.glGenTextures(1)
        BlenderImguiRenderer._texture_cache[texture_id] = tex
        return texture_id


    def call_shutdown_imgui(self):

        if hasattr(self, 'color_palette'):
            bpy.context.scene['color_picker_col']=self.color_palette
        imgui_handler_remove(self.imgui_handle)

    def track_any_cover(self):

        self.cover = (
            imgui.is_any_item_hovered() 
            # or imgui.is_window_hovered(imgui.HoveredFlags_.root_and_child_windows)
            or imgui.is_window_hovered() or imgui.get_io().want_capture_mouse 
            or imgui.get_io().want_text_input
        )
        # print('self.cover',self.cover)
    def track_any_cover_style_editor(self):

        self.cover_style_editor = (
            imgui.is_any_item_hovered() 
            # or imgui.is_window_hovered(imgui.HoveredFlags_.root_and_child_windows)
            or imgui.is_window_hovered() or imgui.get_io().want_capture_mouse 
            or imgui.get_io().want_text_input
        )
        # print('self.cover_style_editor',self.cover)
    def poll_mouse(self, context: bpy.types.Context, event: bpy.types.Event,region):
        io = imgui.get_io()  # 获取 ImGui 的 IO 对象
        # 将 Blender 的鼠标位置转换为 ImGui 的坐标系
        io.add_mouse_pos_event(self.mpos[0], region.height - 1 - self.mpos[1])
        # 根据事件类型更新 ImGui 的鼠标状态
        if event.type == 'LEFTMOUSE':
            io.add_mouse_button_event(0, event.value == 'PRESS')
        elif event.type == 'RIGHTMOUSE':
            io.add_mouse_button_event(1, event.value == 'PRESS')
        elif event.type == 'MIDDLEMOUSE':
            io.add_mouse_button_event(2, event.value == 'PRESS')
        if event.type == 'WHEELUPMOUSE':
            io.add_mouse_wheel_event(0, 1)
        elif event.type == 'WHEELDOWNMOUSE':
            io.add_mouse_wheel_event(0, -1)

    def poll_events(self, context: bpy.types.Context, event: bpy.types.Event):
        io = imgui.get_io()

        # 将 Blender 事件映射为 ImGuiKey 枚举
        if event.type in self.key_map:
            imgui_key = self.key_map[event.type]  # 已映射为 ImGuiKey.xxx
            is_press = (event.value == 'PRESS')
            self._key_state[imgui_key] = is_press  # 👈 存储键盘状态
            io.add_key_event(imgui_key, is_press)

        # 更新修饰键状态（可选，用于确保一致性）

        # 分别更新 Ctrl、Shift、Alt、Super 修饰键状态
        def key_down(key_name):
            k = self.key_map.get(key_name)
            return k is not None and self._key_state.get(k, False)

        io.add_key_event(imgui.Key.left_ctrl, key_down('LEFT_CTRL'))
        # print('左ctrl',key_down('LEFT_CTRL'))
        io.add_key_event(imgui.Key.right_ctrl, key_down('RIGHT_CTRL'))
        io.add_key_event(imgui.Key.left_shift, key_down('LEFT_SHIFT'))
        io.add_key_event(imgui.Key.right_shift, key_down('RIGHT_SHIFT'))
        io.add_key_event(imgui.Key.left_alt, key_down('LEFT_ALT'))
        io.add_key_event(imgui.Key.right_alt, key_down('RIGHT_ALT'))
        io.add_key_event(imgui.Key.left_super, key_down('OSKEY'))

        if event.type == 'C' and event.ctrl and event.value == 'PRESS':
            GlobalImgui.get().ctrl_c=True
        if event.type == 'X' and event.ctrl and event.value == 'PRESS':
            GlobalImgui.get().ctrl_x=True
        if event.type == 'A' and event.ctrl and event.value == 'PRESS':
            GlobalImgui.get().ctrl_a=True
        if event.type == 'V' and event.ctrl and event.value == 'PRESS':
            GlobalImgui.get().ctrl_v=True
        if event.unicode and 0 < (char := ord(event.unicode)) < 0x10000:
            io.add_input_character(char)
        
def convert_color(h, s, v, alpha=255):
    """ Convert HSV to RGBA format and get ImU32 color value. """
    r, g, b = 0.0, .0, .0
    r, g, b = imgui.color_convert_hsv_to_rgb(h, s, v, r, g, b)  # Convert HSV to RGB
    return imgui.get_color_u32(imgui.ImVec4((r * 255), int(g * 255), int(b * 255), alpha))


class Imgui_Color_Picker_Imgui(bpy.types.Operator, BaseDrawCall):
    bl_idname = "imgui.color_picker"
    bl_label = "color picker"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.mode == 'SCULPT' and bpy.context.tool_settings.sculpt.brush == bpy.data.brushes['Paint']:
            sculpt = True
            return sculpt
        if context.area.type == 'IMAGE_EDITOR':
            if context.area.spaces.active.ui_mode=='PAINT':
                image_paint=True
                return image_paint
        if (context.mode in {'PAINT_VERTEX', 'PAINT_TEXTURE', 'PAINT_GPENCIL', 'VERTEX_GPENCIL', }) and context.area.type == 'VIEW_3D':
            return True
        return False
    def draw(self, context: bpy.types.Context):
        a = time.time()

        self.cover = False
        self.cover_style_editor = False
        # 展示一个 ImGui 测试窗口
        wf = imgui.WindowFlags_

        window_flags = wf.no_title_bar | wf.no_resize | wf.no_scrollbar | wf.always_auto_resize

        imgui.set_next_window_pos(
            imgui.ImVec2(self.show_window_pos[0] - 127 - imgui.get_style().indent_spacing * 0.5,
                         context.region.height - self.show_window_pos[1] - 129 - 10))
        _mian_show,_mian_x=imgui.begin("VRC", self.main_window[0], window_flags)

        # imgui.text("")
        start_pos = imgui.ImVec2(imgui.get_cursor_pos().x, +imgui.get_cursor_pos().y+ 10)
        imgui.set_cursor_pos(start_pos)
        im_cf = imgui.ColorEditFlags_
        if get_prefs().picker_switch:
            picker_type=im_cf.picker_hue_wheel
        else:
            picker_type=im_cf.picker_hue_bar
        misc_flags = picker_type | im_cf.no_options | im_cf.input_rgb | im_cf.no_alpha | im_cf.no_side_preview | im_cf.no_label
        color = get_brush_color_based_on_mode()
        if imgui.is_mouse_clicked(0):
            self.pre_color = copy.deepcopy(color)

        colorpicker_changed, picker_pos, picker_pos2, wheel_center = colorpicker('##aa', color, misc_flags, self)
        imgui.same_line()
        imgui.begin_group()
        global color_hsv, color_rgb, color_tmp, color_palette_dict
        color_bar_changed = color_bar(color, color_hsv, color_rgb, self)
        if imgui.is_mouse_down(0):
            if color_bar_changed:
                color_tmp = copy.deepcopy(color)
            id = imgui.get_current_context().hovered_id
            if hasattr(color_palette_dict, f'c{id}'):
                self.color_palette.insert(0, copy.deepcopy(color_palette_dict[id]))
        elif imgui.is_mouse_released(0):
            if colorpicker_changed:
                self.color_palette.insert(0, copy.deepcopy(color))

        if imgui.is_mouse_released(0):
            if color_tmp != [] and not colorpicker_changed:

                ids = [imgui.get_id(i) for i in ['H ', 'S ', 'V ', 'R ', 'G ', 'B ']]
                if imgui.get_current_context().hovered_id in ids:
                    self.color_palette.insert(0, copy.deepcopy(color_tmp))
        color_palette('##color_palette', color, self.backup_color, self.pre_color, self.color_palette)
        imgui.end_group()
        picker_switch_button(' ##1')
        start_pos = imgui.ImVec2(imgui.get_cursor_pos().x, imgui.get_cursor_pos().y -15)
        imgui.set_cursor_pos(start_pos)
        imgui.text('')
        # imgui.show_demo_window()
        self.track_any_cover()
        if imgui.is_item_hovered():
            imgui.set_keyboard_focus_here(-1)

        imgui.end()

    def invoke(self, context, event):
        self.cover = False
        self.cover_style_editor = False
        self.show_window_pos = (event.mouse_region_x, event.mouse_region_y)
        self.show_window_imgui = False
        self.verts = get_wheeL_tri(self.show_window_pos)
        self.backup_color = copy.deepcopy(get_brush_color_based_on_mode())
        self.area=context.area
        self.pre_color = copy.deepcopy(self.backup_color)
        global colors, color_palette_size
        if len(colors) > color_palette_size:
            del colors[color_palette_size:]
        try:
            self.color_palette=[list(c) for c in bpy.context.scene['color_picker_col']]
        except:
            self.color_palette = colors
        self.init_imgui(context)

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
    def refresh(self):
        for area in bpy.context.screen.areas:
            if area.type in ['VIEW_3D','IMAGE_EDITOR']:
                area.tag_redraw()
    def modal(self, context, event):
        if event.type == 'SPACE' and event.value == 'RELEASE':
            self.call_shutdown_imgui()
            self.refresh()
            return {'FINISHED'}
        if event.type == 'Z' and event.value == 'RELEASE':
            self.call_shutdown_imgui()
            self.refresh()
            return {'FINISHED'}
        a = time.time()
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
            return {'PASS_THROUGH'}
        if region:
            region.tag_redraw()
        # —— 计算区域内坐标 —— 
        mx = gx - region.x
        my = gy - region.y
        self.mpos=(gx,my)
        # （如果 ImGui 需要底部为 0，向上为正，这里就不翻转——mouse_region_y 已经是底部起算）
        # print(region)
        # —— 越界检测（可选） —— 
        if mx < 0 or mx > region.width or my < 0 or my > region.height:
            return {'PASS_THROUGH'}
        if event.type in {"ESC",'WINDOW_DEACTIVATE'}:
            self.call_shutdown_imgui()
            self.refresh()
            return {'FINISHED'}
        if event.type in {'RIGHTMOUSE'}:
            self.call_shutdown_imgui()
            self.refresh()
            return {'FINISHED'}
        if event.type == 'X' and event.value == 'RELEASE':
            from .utils import exchange_brush_color_based_on_mode
            exchange_brush_color_based_on_mode(exchange=True)

        if region:
            # region = context.region
            pass
        else:
            self.call_shutdown_imgui()
            self.refresh()
            return {'FINISHED'}
        self.poll_mouse(context, event,region)
        if not self.cover:
            return {"PASS_THROUGH"}
        self.poll_events(context, event)

        return {"RUNNING_MODAL"}


class Imgui_Window_Imgui(bpy.types.Operator, BaseDrawCall):
    bl_idname = "imgui.window"
    bl_label = "color picker"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        return 1

    def draw(self, context: bpy.types.Context):

        if context.region!=self.region:
            return
        print('draw',time.time())
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
            print('not _main_x:')
            self.show_window_imgui = False

    def invoke(self, context, event):
        if len(GlobalImgui.get().imgui_vrc_instance):
            GlobalImgui.get().imgui_vrc_instance[0].should_close=True
            GlobalImgui.get().imgui_vrc_instance.clear()
        GlobalImgui.get().imgui_vrc_instance.append(self)
        self.cover = False
        self.should_close=False
        self.cover_style_editor = False
        self.show_mirror_reminder_window = False
        self.mirror_reminder_window_open_time = None  # 记录窗口打开时间
        # self.text_str=''
        self.show_window_pos = (event.mouse_region_x, event.mouse_region_y)
        self.show_window_imgui = True
        self.area=context.area
        self.region=context.region
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
        print(self)
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
            if self.region==None:
                self.region=region

        # —— 计算区域内坐标 —— 
        mx = gx - region.x
        my = gy - region.y
        self.mpos=(gx,my)

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

        self.poll_mouse(context, event,region)
        
        self.poll_events(context, event)
        # print([x for x in gc.get_objects() if isinstance(x, Imgui_Window_Imgui)])
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
