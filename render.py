import sys
from imgui_bundle import imgui
from imgui_bundle.python_backends.base_backend import BaseOpenGLRenderer
# if '3.10' in sys.version:
#     from .extern.imgui_bundle3_10.imgui_bundle import imgui
#     from .extern.imgui_bundle3_10.imgui_bundle.python_backends.base_backend import BaseOpenGLRenderer
# else:
#     from .extern.imgui_bundle3_11.imgui_bundle import imgui
#     from .extern.imgui_bundle3_11.imgui_bundle.python_backends.base_backend import BaseOpenGLRenderer
import gpu
import bpy
import ctypes
import platform
import time
from gpu_extras.batch import batch_for_shader
import numpy as np
# import OpenGL.GL as gl  # noqa
from gpu.types import GPUShader, GPUShaderCreateInfo
class Renderer(BaseOpenGLRenderer):
    vertex_source="""
                in  vec3 Position;
                in  vec2 UV;
                in  vec4 Color;
                out vec2 Frag_UV;
                out vec4 final_col;
                uniform mat4 ProjMtx;
                void main() {
                    Frag_UV = UV;
                    final_col=Color;
                    gl_Position = ProjMtx * vec4(Position.xy, 0, 1);
                }
                """
    fragment_source="""
                    in vec2 Frag_UV;
                    in vec4 final_col;
                    out vec4 Frag_Color;
                    uniform sampler2D Texture;
    
                    void main() {     
                                  
                        Frag_Color = final_col;
                        Frag_Color.rgb = pow(Frag_Color.rgb,vec3(2.2)); 
                        Frag_Color.a = 1.0 - pow((1.0 - Frag_Color.a),2.2);
                        Frag_Color  = (texture(Texture, Frag_UV.st)) *Frag_Color;                     
                    }   
                                                """
    instance = None
    _texture_cache={}
    t=0
    t_draw=0
    font=None
    def __init__(self):
        super(Renderer,self).__init__()
        self._shader_handle = None
        self._vert_handle = None
        self._fragment_handle = None

        self._attrib_location_tex = None
        self._attrib_proj_mtx = None
        self._attrib_location_position = None
        self._attrib_location_uv = None
        self._attrib_location_color = None

        self._vbo_handle = None
        self._elements_handle = None
        self._vao_handle = None
        self._font_tex = None
        
        Renderer.instance = self
        
        # 立即建立設備物件 (著色器)
        self._create_device_objects()
        
        # 註冊字體紋理刷新處理器，確保在檔案載入後重新載入字體
        if self.refresh_font_texture_ex not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(self.refresh_font_texture_ex)
        
        # 首次載入字體紋理
        self.refresh_font_texture_ex()


    def create_imgui_shader(self) -> GPUShader:
        """
        创建用于 ImGui 的自定义 GPUShader，包含 Position, UV, Color 输入，
        以及支持 sRGB gamma 修正与 alpha 处理的片元逻辑。
        
        Returns:
            GPUShader: 可直接用于绑定和绘制的 GPUShader 对象
        """
        shader_info = GPUShaderCreateInfo()
        # shader_info.name = "IMGUI_CUSTOM_SHADER"
        vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
        vert_out.smooth('VEC2', "Frag_UV")
        vert_out.smooth('VEC4', "final_col")
        # 顶点输入（slot必须与你的顶点绑定顺序一致）
        shader_info.vertex_in(0, "VEC3", "Position")
        shader_info.vertex_in(1, "VEC2", "UV")
        shader_info.vertex_in(2, "VEC4", "Color")

        # 顶点到片段的输出
        shader_info.vertex_out(vert_out)
        # shader_info.vertex_out("VEC4", "final_col")

        # Uniforms 和采样器
        shader_info.push_constant("MAT4", "ProjMtx")       # 投影矩阵
        shader_info.sampler(0, "FLOAT_2D", "Texture")  # 纹理采样器

        # 顶点着色器源码
        shader_info.vertex_source('''
            void main() {
                Frag_UV = UV;
                final_col = Color;
                gl_Position = ProjMtx * vec4(Position.xy, 0.0, 1.0);
            }
        ''')

        # 片元着色器源码
        shader_info.fragment_source('''
            void main() {
                vec4 tex_color = texture(Texture, Frag_UV);
                vec4 col = final_col;
                col.rgb = pow(col.rgb, vec3(2.2));
                col.a = 1.0 - pow(1.0 - col.a, 2.2);
                Frag_Color = tex_color * col;
            }
        ''')

        # 输出颜色
        shader_info.fragment_out(0, "VEC4", "Frag_Color")

        # 创建并返回 shader
        return gpu.shader.create_from_info(shader_info)

    def refresh_font_texture(self):
        # self.refresh_font_texture_ex(self)
        if self.refresh_font_texture_ex not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(self.refresh_font_texture_ex)

    @staticmethod
    @bpy.app.handlers.persistent
    def refresh_font_texture_ex(scene=None):
        self = Renderer.instance
        if self is None: # 以防處理器在實例設置前被呼叫
            return
        # img = bpy.data.images.get(".imgui_font", None)
        # print('img',)
        # 只有當圖像不存在或其綁定代碼無效時才刷新
        # Windows上 img.bindcode == 0 可能表示紋理尚未載入或已失效
        # print(self._texture_cache)
        # if not img or img.bindcode == 0:
        if self.font is None:
        # if not img:

            # print(f"Refreshing font texture. Current img: {img}, bindcode: {img.bindcode if img else 'N/A'}")
            font_matrix: np.ndarray = self.io.fonts.get_tex_data_as_rgba32()
            width = font_matrix.shape[1]
            height = font_matrix.shape[0]
            pixels = font_matrix.data
            # if not img:
                # 建立新的Blender圖像資料塊
                # img = bpy.data.images.new(".imgui_font", width, height, alpha=True, float_buffer=True)
                # img.colorspace_settings.name = 'Non-Color' # 根據需要設定色彩空間
            # 將 uint8 像素數據轉換為 float32 (0.0-1.0) 以適應Blender的 float_buffer 圖像
            pixels_float = np.frombuffer(pixels, dtype=np.uint8).astype(np.float32) / 255.0
            # img.pixels.foreach_set(pixels_float) # [5, 6, 7]
            gpu_buffer = gpu.types.Buffer('FLOAT', (width * height * 4,), pixels_float)

            # 创建 GPU 纹理
            self.font = gpu.types.GPUTexture(size=(width, height), format='RGBA8', data=gpu_buffer)
            # print(f"成功创建GPUTexture：尺寸 {width}x{height}, 格式 {'RGBA8'}")
            self.io.fonts.clear_tex_data() # 上傳到GPU後清除CPU端的字體數據

            # 將Blender圖像載入到OpenGL紋理中，並獲取其綁定代碼 [3]
            # img.gl_load() 
            
            # 儲存OpenGL整數 ID
            # self._font_texture = img.bindcode
            self._font_texture = 1

            # 從Blender圖像建立並快取 GPUTexture 物件 [8, 9, 10, 11]
            # 這個 GPUTexture 物件是 gpu.types.GPUShader.uniform_sampler 所期望的
            Renderer._texture_cache[self._font_texture] = self.font
            # Renderer._texture_cache[self._font_texture] = gpu.texture.from_image(img)
            self._font_tex = Renderer._texture_cache[self._font_texture]

            # 將 ImGui 的字體紋理 ID 設置為 OpenGL 整數 ID
            self.io.fonts.tex_id = self._font_texture
            # print(f"Font texture refreshed. New ID: {self._font_texture}")
        else:
            # print(111)
            # self._font_texture = img.bindcode
            self._font_texture = 1
            # if self._font_texture not in Renderer._texture_cache:
                # Renderer._texture_cache[self._font_texture] = gpu.texture.from_image(img)
            self._font_tex = Renderer._texture_cache[self._font_texture]
            self.io.fonts.tex_id = self._font_texture
        # else:
        #     # 如果圖像已存在且綁定代碼有效，則確保 _font_tex 和 _font_texture 已設置
        #     # 這處理了Blender可能重新載入檔案但Renderer實例仍然存在的情況
        #     self._font_texture = img.bindcode
        #     self._font_texture = 1
        #     if self._font_texture not in Renderer._texture_cache:
        #         Renderer._texture_cache[self._font_texture] = gpu.texture.from_image(img)
        #     self._font_tex = Renderer._texture_cache[self._font_texture]
        #     self.io.fonts.tex_id = self._font_texture
            # print(f"Font texture already loaded. ID: {self._font_texture}")
        # bpy.data.images.remove(img)

    def _create_device_objects(self):
        # 建立自訂著色器一次
        # self._bl_shader = gpu.types.GPUShader(self.vertex_source, self.fragment_source)
        self._bl_shader = self.create_imgui_shader()
        print("Custom shader created.")
        # se
    def _invalidate_device_objects(self):
        # 清理資源，在 ImGui 上下文銷毀時呼叫
        self.io.fonts.tex_id = 0 # 重置 ImGui 的字體紋理 ID
        self._font_texture = 0
        self._font_tex = None
        
        # 清除紋理快取
        # GPUTexture 物件由Blender的上下文管理，通常不需要明確的glDeleteTextures
        # 我們只需清除Python引用
        Renderer._texture_cache.clear()
        
        # 著色器清理
        if self._bl_shader:
            self._bl_shader.free() # 釋放著色器資源
            self._bl_shader = None
        # print("Device objects invalidated.")


    def render(self, draw_data):
        io = self.io
        shader = self._bl_shader
        # print('shader = self._bl_shader',time.time()-self.t,shader)
        # 获取显示尺寸和缩放后的帧缓冲区尺寸
        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_framebuffer_scale[0])
        fb_height = int(display_height * io.display_framebuffer_scale[1])

        # 如果帧缓冲区宽度或高度为0，则退出函数
        if fb_width == 0 or fb_height == 0:
            return


        # 根据显示缩放比例调整剪裁矩形
        draw_data.scale_clip_rects(io.display_framebuffer_scale)
        # print('scale_clip_rects',time.time()-self.t)
        #记录上一帧
        last_enable_blend = gpu.state.blend_get()
        last_enable_depth_test = gpu.state.depth_test_get()
        # 设置图形管线的状态
        gpu.state.blend_set('ALPHA')  # 设置混合模式为透明
        gpu.state.depth_test_set('LESS_EQUAL')  # 禁用深度测试
        # gpu.state.face_culling_set('NONE')  # 禁用面剔除
        gpu.state.program_point_size_set(False)  # 不使用程序设置的点大小
        gpu.state.scissor_test_set(True)  # 启用剪裁测试
        self.refresh_font_texture_ex()
        # 绑定着色器并设置投影矩阵
        shader.bind()
        # print('shader.bind',time.time()-self.t)
        shader.uniform_float("ProjMtx", self._create_projection_matrix(display_width, display_height))
        # shader.uniform_sampler("Texture", self._font_tex)  # 设置纹理采样器
        # print('shader.uniform_float',time.time()-self.t)
        # 遍历所有的绘制命令列表
        for commands in draw_data.cmd_lists:
            # 获取索引缓冲区的大小和地址，转换为numpy数组

            size = commands.idx_buffer.size()* imgui.INDEX_SIZE // 4
            # address = commands.idx_buffer_data
            address = commands.idx_buffer.data_address()
            idx_buffer_np = np.ctypeslib.as_array(ctypes.cast(address, ctypes.POINTER(ctypes.c_int)), shape=(size,))

            # 获取顶点缓冲区的大小和地址，转换为numpy数组
            size = commands.vtx_buffer.size()* imgui.VERTEX_SIZE // 4
            # address = commands.vtx_buffer_data
            address = commands.vtx_buffer.data_address()
            vtx_buffer_np = np.ctypeslib.as_array(ctypes.cast(address, ctypes.POINTER(ctypes.c_float)), shape=(size,))
            vtx_buffer_shaped = vtx_buffer_np.reshape(-1, imgui.VERTEX_SIZE // 4)

            idx_buffer_offset = 0
            # print('cmd_buffer',time.time()-self.t)
            # 遍历每个绘制命令
            for command in commands.cmd_buffer:
                b=time.time()
                loop=time.time()
                
                # 设置剪裁矩形
                x, y, z, w = command.clip_rect
                gpu.state.scissor_set(int(x), int(fb_height - w), int(z - x), int(w - y))

                # 獲取當前命令的紋理 ID
                current_texture_id = command.texture_id
                is_font_tex = (current_texture_id == self._font_texture)
                # print(time.time()-self.t,'当前texture_id',current_texture_id)
                # print("裁剪", time.time()-b)
                # self.t=time.time()
                # 從快取中檢索 GPUTexture 物件
                # if not is_font_tex:
                #     current_gpu_texture = Renderer._texture_cache.get(160)
                # else:
                #     current_gpu_texture = Renderer._texture_cache.get(current_texture_id)
                current_gpu_texture = Renderer._texture_cache.get(current_texture_id)

                # print('current_texture_id',current_texture_id,current_gpu_texture)
                if current_gpu_texture is None:
                    # 警告：ImGui 命令使用了未知紋理 ID。這表示該紋理未通過我們的系統載入/快取。
                    # 為了避免崩潰，使用字體紋理作為備用。
                    # 在實際應用中，您可能需要載入一個佔位符紋理或記錄更嚴重的錯誤。
                    # print(f"Warning: ImGui command uses unknown texture ID {current_texture_id}. Using font texture as fallback.")
                    current_gpu_texture = self._font_tex # 備用字體紋理
                    if current_gpu_texture is None:
                        # 如果連字體紋理都不可用，則跳過此命令以防止崩潰。
                        # print("Error: Font texture not available. Skipping draw command.")
                        idx_buffer_offset += command.elem_count
                        continue
                # print("current_gpu_texture", time.time()-self.t)
                b=time.time()
                # 為此繪圖命令綁定正確的紋理
                shader.uniform_sampler("Texture", current_gpu_texture)

                # 提取顶点、UV和颜色信息，准备绘制
                vertices = vtx_buffer_shaped[:, :2]
                uvs = vtx_buffer_shaped[:, 2:4]
                # 判断当前纹理是否是字体纹理
                
                # uvs = vtx_buffer_shaped[:, 2:4].copy()
                # 如果不是字体纹理，则翻转 v 坐标
                # if not is_font_tex:
                    # uvs[:, 1] = 1.0 - uvs[:, 1]
                # uvs[:, 1] = 1.0 - uvs[:, 1]
                colors = vtx_buffer_shaped.view(np.uint8)[:, 4 * 4:].astype('f') / 255.0
                
                # 提取索引数据
                indices = idx_buffer_np[idx_buffer_offset:idx_buffer_offset + command.elem_count]
                # print("uniform_sampler", time.time()-b)
                # 创建批处理对象并绘制
                b=time.time()
                batch = batch_for_shader(shader, 'TRIS', {
                    "Position": vertices,
                    "UV": uvs,
                    "Color": colors,
                }, indices=indices)
                # print("创建批处理", time.time()-b)
                b=time.time()
                batch.draw(shader)
                
                # 更新索引缓冲区偏移
                idx_buffer_offset += command.elem_count
                # print("draw耗时", time.time()-b)
                # print("单个循环", time.time()-loop)
        gpu.state.blend_set('ALPHA')
        gpu.state.scissor_test_set(False)  # 启用剪裁测试

    def _create_projection_matrix(self, width, height):
        ortho_projection = (
            2.0 / width, 0.0, 0.0, 0.0,
            0.0, 2.0 / -height, 0.0, 0.0,
            0.0, 0.0, -1.0, 0.0,
            -1.0, 1.0, 0.0, 1.0
        )
        return ortho_projection

