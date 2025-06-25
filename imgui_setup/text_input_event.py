import bpy
from imgui_bundle import imgui
import ctypes

from .imgui_global import GlobalImgui

def on_text_edit(data: "imgui.InputTextCallbackData") -> int:
    # print('text','on_text_edit')
    # io = imgui.get_io()
    s = data.selection_start
    e = data.selection_end
    # print('s',s,'e',e,io.key_ctrl,imgui.is_key_pressed(imgui.Key.c))
    # if io.key_ctrl and imgui.is_key_pressed(imgui.Key.c):
    #     print(11133)
    
    if e > s:
        sel_bytes = data.buf[s:e]
    elif s>e:
        sel_bytes = data.buf[e:s]
    else:
        sel_bytes=''
    # text=sel_bytes
    # self.clipboard=text
    if GlobalImgui.get().ctrl_c:
        bpy.context.window_manager.clipboard=sel_bytes
        GlobalImgui.get().ctrl_c=False
    if GlobalImgui.get().ctrl_x:
        print('ctrl x')
        bpy.context.window_manager.clipboard=sel_bytes
        if e>s:
            print('e>s')
        # 先删除选中区域
            data.delete_chars(s, e - s)
        elif s>e:
            print('s>e')
            data.delete_chars(e, s - e)
        GlobalImgui.get().ctrl_x = False
    if GlobalImgui.get().ctrl_v:
        paste_text = bpy.context.window_manager.clipboard
        s = data.selection_start
        e = data.selection_end
        
        if e>s:
            print('e>s')
        # 先删除选中区域
            data.delete_chars(s, e - s)
            data.insert_chars(s, paste_text)
        elif s==e:
            data.insert_chars(s, paste_text)
        else:
            print('s>e')
            data.delete_chars(e, s - e)
            data.insert_chars(e, paste_text)
        GlobalImgui.get().text_input_buf = data.buf  # 更新数据源
        GlobalImgui.get().ctrl_v = False
    if GlobalImgui.get().ctrl_a:
        # 选中全部内容
        data.selection_start = 0
        data.selection_end = data.buf_text_len  # 或 len(data.buf)
        data.cursor_pos = data.buf_text_len     # 将光标移到最后
        GlobalImgui.get().ctrl_a = False
    if imgui.is_key_down(imgui.Key.enter):
        print('enter')
        # imgui.set_keyboard_focus_here(-1)
        # # imgui.input_text()
    GlobalImgui.get().text_input_buf = data.buf
    return 0
