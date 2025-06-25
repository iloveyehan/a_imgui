from pathlib import Path
import bpy
import gpu
import numpy as np
import OpenImageIO as oiio
from imgui_bundle import imgui
from ..render import Renderer as BlenderImguiRenderer
from ..imgui_setup.imgui_global import GlobalImgui
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
         # 先把 area 和 region 存下来
        self.area   = context.area
        self.region = context.region
        print(self.area,self.region)
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
        # if self.area.type=='VIEW_3D':
        #     self.imgui_handle = GlobalImgui.get().handler_add(self.draw, bpy.types.SpaceView3D, self)
       # ※ 关键：把 context.region.type 也传进去，让 imgui-bundle 只在这个 region 触发 draw
        if self.area.type == 'VIEW_3D':
            print('添加句柄,',self.region.as_pointer())
            self.imgui_handle = GlobalImgui.get().handler_add(
                self.draw,
                (bpy.types.SpaceView3D, self.region.as_pointer()),
                self,
            ) 
        
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

            # print(f"图像规格：{width}x{height}, 通道数：{nchannels}, OIIO格式：{oiio_format}")

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
                # print("检测到3通道RGB图像，添加一个完全不透明的Alpha通道。")
                rgba_pixels = np.zeros((height, width, 4), dtype=np.uint8)
                rgba_pixels[:, :, :3] = pixels_np[:, :, :3]
                rgba_pixels[:, :, 3] = 255
                final_pixels_np = rgba_pixels
                target_channels = 4
                gpu_format_str = 'RGBA8'
            elif nchannels == 4:
                # print("图像已包含Alpha通道。")
                final_pixels_np = pixels_np
                target_channels = 4
                gpu_format_str = 'RGBA8'
            elif nchannels == 1:
                # print("检测到1通道灰度图像，转换为RGBA。")
                rgba_pixels = np.zeros((height, width, 4), dtype=np.uint8)
                rgba_pixels[:, :, 0] = pixels_np[:, :, 0]
                rgba_pixels[:, :, 1] = pixels_np[:, :, 0]
                rgba_pixels[:, :, 2] = pixels_np[:, :, 0]
                rgba_pixels[:, :, 3] = 255
                final_pixels_np = rgba_pixels
                target_channels = 4
                gpu_format_str = 'RGBA8'
            else:
                # print(f"警告：不支持的通道数 ({nchannels})。尝试使用原始数据。")
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
            # print(f"成功创建GPUTexture：尺寸 {width}x{height}, 格式 {gpu_format_str}")

            return gpu_texture

        except Exception as e:
            print(f"在加载PNG到GPU纹理时发生错误：{e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            img_input.close()

    def load_icon_texture(self,path):
        # print('载入图像路径:',Path(__file__))
        tex=self.load_png_to_gpu_texture(str(Path(__file__).parent.parent/'icons'/path))
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
    def poll_mouse(self, context: bpy.types.Context, event: bpy.types.Event):
        io = imgui.get_io()  # 获取 ImGui 的 IO 对象
        # 将 Blender 的鼠标位置转换为 ImGui 的坐标系
        io.add_mouse_pos_event(self.mpos[0], self.region.height - 1 - self.mpos[1])
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
   