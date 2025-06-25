import ctypes
from ctypes import wintypes
import sys
import time
import bpy
from imgui_bundle import imgui,ImVec2, ImVec4
from pathlib import Path
from ..shader import draw_circle, draw_rec
from ..utils.utils import get_brush_color_based_on_mode, get_prefs
from ..render import Renderer as BlenderImguiRenderer
from .widget_rewriting import ImageButton, TextButton
class GlobalImgui:
    _instance = None

    def __init__(self):
        self.imgui_vrc_instance=[]
        self.debug=True
        self.imgui_context = None
        self.imgui_backend = None
        self.draw_handlers = {}
        self.callbacks = {}
        self.next_callback_id = 0
        #鼠标键盘事件
        self.ctrl_c=False
        self.ctrl_x=False
        self.ctrl_v=False
        self.ctrl_a=False
        self.clipboard=''
        self.text_input_buf=''
        self.loaded_font=None
        #新窗口缓存
        self.show_new_window = [False]
        self.show_mirror_reminder_window=False
        self.mirror_reminder_window_open_time=None

        self.image_btn=ImageButton()
        self.text_btn=TextButton()
        #按钮配置
        self.btn_dict={
        'image_size': ImVec2(30.0, 30.0),
        'uv0': ImVec2(0, 0),
        'uv1' : ImVec2(1, 1),
        'bg_col' : ImVec4(0.1, 0.1, 0.1, 0.0),  # Black background
        'tint_col' : ImVec4(1.0, 1.0, 1.0, 1.0) } # No tint

        #镜像顶点组
        self.vg_left=False
        self.vg_right=False
        self.vg_middle=False
        self.vg_mul=False
        self.vg_select=False
        self.last_side=''
        #颜色配置
        self.set_color()
        #同步集合缓存
        self.item_current_idx=0
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = GlobalImgui()
        return cls._instance

    @staticmethod
    def init_font():
        io = imgui.get_io()
        io.fonts.clear()  # 清掉内置字体

        font_path = Path(__file__).parent.parent / "SourceHanSansCN-Normal.otf"


        # 获取中文全字符范围
        merged_ranges=[]
  
        merged_ranges.extend([0x1, 0xF4240])
      
        GlobalImgui.get().loaded_font=io.fonts.add_font_from_file_ttf(
            str(font_path),
            # 假设在 Blender 中运行
            # size_pixels=bpy.context.preferences.view.ui_scale * 20,
            size_pixels=20.0, # 使用一个固定值作为示例
            glyph_ranges_as_int_list=merged_ranges, # 使用我们定义的全范围
        )

        # 字体信息上传到 GPU
        # 这一步会因为字符太多而变得很慢
        print("Building font atlas... This may take a while.")
        io.fonts.build()
        print("Font atlas built successfully.")
    def set_color(self):
        self.child_bg=imgui.ImVec4(0.1, 0.1, 0.1, 1.0)
        self.title_bg_active_color = imgui.ImVec4(0.1, 0.1, 0.1, 0.9)
        self.title_bg_color = imgui.ImVec4(0.1, 0.1, 0.1, 0.9)
        self.title_bg_collapsed_color = imgui.ImVec4(78/255.0, 85/255.0, 91/255.0, 134/255.0)
        self.frame_bg_color = imgui.ImVec4(0.512, 0.494, 0.777, 0.573)
        self.window_bg_color =  imgui.ImVec4(0.137, 0.137, 0.137, 0.9)
        self.button_color =  imgui.ImVec4(0.33, 0.33, 0.33, 1)
        self.button_hovered_color =  imgui.ImVec4(0.39, 0.39, 0.39, 1)
        self.button_active_color =  imgui.ImVec4(71/255.0, 114/255.0, 179/255.0, 1)
        self.header_color =  imgui.ImVec4(75/255.0, 75/255.0, 75/255.0, 79/255.0)
    def init_imgui(self):
        if self.imgui_context is None:
            self.imgui_context = imgui.create_context()
            # imgui.set_current_context(self.imgui_context)  # 显式设置当前上下文
            # 2) 【Windows 专用】：告诉 ImGui 当前窗口句柄
            io = imgui.get_io()
            io.config_flags |= (imgui.ConfigFlags_.nav_enable_keyboard.value)  # Enable Keyboard Controls
            io.config_flags |= imgui.ConfigFlags_.docking_enable.value  # 启用窗口停靠
            # io.want_capture_keyboard = True  # 确保捕获键盘事件
            # io.config_input_text_enter_returns_true = True  # 允许回车确认输入
            # 3) 平台能力标记：键盘、剪贴板、鼠标光标、IME
            # io.backend_flags |= (
            #     imgui.BackendFlags_.has_mouse_cursors.value
            #     | imgui.BackendFlags_.HasSetClipboard.value
            #     | imgui.BackendFlags_.HasGetClipboard.value
            #     | imgui.BackendFlags_.HasKeyboard.value
            #     | imgui.BackendFlags_.HasIme.value
            # )
            if sys.platform == "win32":
                print('win32')
                # 获取当前 Blender 窗口句柄（HWND）
                user32 = ctypes.WinDLL('user32', use_last_error=True)
                GetForegroundWindow = user32.GetForegroundWindow
                GetForegroundWindow.restype = wintypes.HWND

                hwnd = GetForegroundWindow()
                imgui.platform_handle = hwnd
                print('hwnd',hwnd)
                io.want_capture_keyboard=True
                #访问键盘
   
                def _set_clipboard_text(_imgui_context: object, text: str) -> None:
                    print('get',text)
                    bpy.context.window_manager.clipboard = text

                    # @staticmethod
                def _get_clipboard_text(_imgui_context: object) -> str:
                    print('set',bpy.context.window_manager.clipboard)
                    return bpy.context.window_manager.clipboard
                # imgui.get_platform_io().platform_get_clipboard_text_fn = lambda *args: _get_clipboard_text()
                # imgui.get_platform_io().platform_get_clipboard_text_fn = lambda *args: _get_clipboard_text()
                imgui.get_platform_io().platform_set_clipboard_text_fn = _set_clipboard_text
                imgui.get_platform_io().platform_get_clipboard_text_fn = _get_clipboard_text

                
            self.init_font()
            self.imgui_backend = BlenderImguiRenderer()
            # self.imgui_backend.refresh_font_texture_ex()
            self.setup_key_map()
            # print('初始化imgui')
    # 定义剪贴板处理函数
    # @staticmethod
    
    def shutdown_imgui(self):
        
        # print('self.draw_handlers.items()',self.draw_handlers.items())
        for SpaceType, draw_handler in self.draw_handlers.items():
            SpaceType[0].draw_handler_remove(draw_handler, 'WINDOW')
        self.draw_handlers.clear()
        print('IMGUI DEBUG','shutdown_imgui')
        # imgui.destroy_context(self.imgui_context)
        


    def handler_add(self, callback, space_type_and_region, ops):
        # space_type_and_region: 形如 (SpaceType, region.id)
        if self.imgui_context is None:
            self.init_imgui()
        
        key = space_type_and_region
        if key[1] not in self.draw_handlers:
            self.draw_handlers[key] = key[0].draw_handler_add(
                self.draw,
                (key[0], ops),
                'WINDOW', 'POST_PIXEL'
            )

        handle = self.next_callback_id
        self.next_callback_id += 1
        self.callbacks[handle] = (callback, key[1])
        return handle

    def handler_remove(self, handle):
        print('关闭窗口或者新建另一个窗口',self.callbacks[handle])
        # clear all
        if handle not in self.callbacks:
            return
        #移除上一个窗口绘制
        for SpaceType, draw_handler in self.draw_handlers.items():
            if SpaceType[1]==self.callbacks[handle][1]:
                SpaceType[0].draw_handler_remove(draw_handler, 'WINDOW')
        del self.callbacks[handle]
        
        if not len(self.callbacks):
            self.shutdown_imgui()
        print('Imgui Debug:',self.draw_handlers)
    def apply_ui_settings(self):
        region = bpy.context.region
        imgui.get_io().display_size = region.width, region.height
        # 圆角控件
        style = imgui.get_style()
        style.window_padding = (1, 1)
        style.window_rounding = 6
        style.frame_rounding = 2
        style.frame_border_size = 1
        # style = imgui.get_current_context().style
        # bg color
        style.set_color_(2, imgui.ImVec4(0, 0, 0, 0.55))

    def draw(self, area, ops):
        a = time.time()
        context = bpy.context
        self.apply_ui_settings()  # 应用用户界面设置
        try:
            imgui.new_frame()  # 开始新的 ImGui 帧
        except:
            print('Gl draw')
            return
        # print('globalimgui draw')
        # imgui.get_io().font_default = imgui.get_io().fonts.fonts[1]
        # 定义自定义样式颜色
        
        # 将自定义颜色推送到 ImGui 样式堆栈
        imgui.push_style_color(imgui.Col_.frame_bg.value, self.frame_bg_color)
        imgui.push_style_color(imgui.Col_.window_bg.value, self.window_bg_color)
        imgui.push_style_color(imgui.Col_.title_bg.value, self.title_bg_color)
        imgui.push_style_color(imgui.Col_.title_bg_active.value, self.title_bg_active_color)
        imgui.push_style_color(imgui.Col_.title_bg_collapsed.value, self.title_bg_collapsed_color)
        imgui.push_style_color(imgui.Col_.button.value, self.button_color)
        imgui.push_style_color(imgui.Col_.button_hovered.value, self.button_hovered_color)
        imgui.push_style_color(imgui.Col_.button_active.value, self.button_active_color)
        imgui.push_style_color(imgui.Col_.header.value, self.header_color)
        imgui.get_style().set_color_(5, imgui.ImVec4(0, 0, 0, 0))
        imgui.push_style_var(20, 1)
        invalid_callback = []  # 创建一个列表来存储无效的回调函数

        # for cb, SpaceType in self.callbacks.values():
        #     # print('draw1',SpaceType,area)
        #     if SpaceType == area:
        #         # print('draw2',SpaceType,area)
        #         cb(bpy.context)
        for cb, region_id in self.callbacks.values():
            # print('draw1',SpaceType,area)
            if region_id == ops.region.as_pointer():
                # print('draw2',SpaceType,area)
                cb(bpy.context)
        # 从 ImGui 样式堆栈中弹出自定义颜色
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_color()
        imgui.pop_style_var(1)
        # print(222, imgui.is_key_pressed(imgui.Key.left_ctrl))
        imgui.end_frame()  # 结束 ImGui 帧
        imgui.render()  # 渲染 ImGui 绘制数据

        # 使用自定义渲染器渲染 ImGui 绘制数据
        self.imgui_backend.render(imgui.get_draw_data())
        if hasattr(ops, 'sv_cursor_pos'):
            if not get_prefs().picker_switch:
                draw_rec(ops.show_window_pos, 71.5, ops.h)
                draw_circle((ops.sv_cursor_pos.x, bpy.context.region.height - ops.sv_cursor_pos.y), ops.sv_cursor_rad / 2,
                            (*get_brush_color_based_on_mode(), 1), (1, 1, 1, .95))


    def setup_key_map(self):
        io = imgui.get_io()
        keys = (
            imgui.Key.tab,
            imgui.Key.left_arrow,
            imgui.Key.right_arrow,
            imgui.Key.up_arrow,
            imgui.Key.down_arrow,
            imgui.Key.home,
            imgui.Key.end,
            imgui.Key.insert,
            imgui.Key.delete,
            imgui.Key.backspace,
            imgui.Key.enter,
            imgui.Key.escape,
            imgui.Key.page_up,
            imgui.Key.page_down,
            imgui.Key.a,
            imgui.Key.c,
            imgui.Key.v,
            imgui.Key.x,
            imgui.Key.y,
            imgui.Key.z,
            imgui.Key.left_ctrl,
            imgui.Key.right_ctrl,
            imgui.Key.left_shift,
            imgui.Key.right_shift,
            imgui.Key.left_alt,
            imgui.Key.right_alt,
            imgui.Key.left_super,
            imgui.Key.right_super,

        )
        # for k in keys:
        #     # We don't directly bind Blender's event type identifiers
        #     # because imgui requires the key_map to contain integers only
        #     # io.add_input_character(k)
        #     io.key_map[k] = k
