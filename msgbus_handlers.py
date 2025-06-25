from pathlib import Path
import time
import bpy
from .imgui_setup.imgui_global import GlobalImgui
from .common.class_loader.auto_load import ClassAutoloader
msgbus_handler=ClassAutoloader(Path(__file__))
from bpy.app.handlers import persistent
@persistent
def load_post_handler(dummy):
    # register_sculpt_warning_handler()
    # 每次新文件加载完成后，重新执行消息总线订阅
    register_msgbus()
def unregister_msgbus():
    bpy.msgbus.clear_by_owner(__name__)
    print("[IMGUI DEBUG]消息总线订阅已移除。")
def reg_msgbus_handler():
    msgbus_handler.init()
    msgbus_handler.register()
    # bpy.types.TOPBAR_MT_editor_menus.append(menu_func)
    bpy.app.handlers.load_post.append(load_post_handler)
    # register_sculpt_warning_handler()
    register_msgbus()
def unreg_msgbus_handler():
    unregister_msgbus()
    msgbus_handler.unregister()
    # bpy.types.TOPBAR_MT_editor_menus.remove(menu_func)
    # unregister_sculpt_warning_handler()
    if load_post_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_handler)
def mirror_x_changed(*args):    
    # print('qt_window',qt_window,bpy.context.view_layer.objects.active.name)
    if GlobalImgui.get().draw_handlers !={}:
        obj = bpy.context.view_layer.objects.active
        # print(f"当前物体 {obj.name} 的 use_mesh_mirror_x = {obj.use_mesh_mirror_x}")
        if (obj.mode in  ['SCULPT','EDIT']):
            # print('模式',obj.mode)
            if not getattr(obj, 'use_mesh_mirror_x', True):
                GlobalImgui.get().show_mirror_reminder_window = True
                GlobalImgui.get().mirror_reminder_window_open_time = time.time()  # 记录当前时间
    
    # on_active_or_mode_change()
def register_msgbus():
    # 监听所有 Object 实例的 mode 属性变化 :contentReference[oaicite:1]{index=1}
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=__name__,
        args=(),
        notify=mirror_x_changed,
        options={'PERSISTENT'}
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "use_mesh_mirror_x"),
        owner=__name__,
        args=(),
        notify=mirror_x_changed,
        options={'PERSISTENT'},
    )