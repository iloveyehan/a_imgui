# window_hook.py
import ctypes
import ctypes.wintypes as wintypes
import win32con
import win32gui
from imgui_bundle import imgui

# 全局变量
_global_state = {
    "hwnd": None,
    "old_wndproc": None,
    "wndproc_func": None
}

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p
)

def message_to_string(msg_type):
    for name, value in vars(win32con).items():
        if value == msg_type and name.startswith("WM_"):
            return name
    return f"Unknown message: {msg_type}"

def _wndproc(hwnd, msg, wParam, lParam):
    try:
        hwnd_val = ctypes.cast(hwnd, ctypes.c_void_p).value if hwnd else 0
        msg_val = int(msg) if msg is not None else 0
        wParam_val = int(wParam) if wParam is not None else 0
        lParam_val = int(lParam) if lParam is not None else 0
    except Exception as e:
        print("参数转换异常:", e)
        if _global_state["old_wndproc"]:
            return _global_state["old_wndproc"](hwnd, msg, wParam, lParam)
        return 0

    if imgui.get_io().want_text_input:
        if msg_val == win32con.WM_IME_COMPOSITION:
            GCS_RESULTSTR = 0x0800
            hImc = ctypes.windll.imm32.ImmGetContext(hwnd_val)
            ctypes.windll.imm32.ImmSetOpenStatus(hImc, True)
            ctypes.windll.imm32.ImmAssociateContext(hwnd, hImc)
            if hImc:
                size = ctypes.windll.imm32.ImmGetCompositionStringW(hImc, GCS_RESULTSTR, None, 0)
                if size > 0:
                    buf = ctypes.create_unicode_buffer(size // 2 + 1)
                    ctypes.windll.imm32.ImmGetCompositionStringW(hImc, GCS_RESULTSTR, buf, size)
                    text = buf.value
                    for ch in text:
                        imgui.get_io().add_input_character(ord(ch))
                ctypes.windll.imm32.ImmReleaseContext(hwnd_val, hImc)
            return 0

        if msg_val == win32con.WM_IME_CHAR:
            imgui.get_io().add_input_character(wParam_val)
            return 0

    # Debug 打印（可选）
    name = message_to_string(msg_val)
    if name:
        print(name)

    if _global_state["old_wndproc"]:
        return _global_state["old_wndproc"](hwnd, msg, wParam, lParam)
    return 0

def hook_wndproc(window_class_name="GHOST_WindowClass"):
    """手动注册窗口钩子"""
    hwnd = win32gui.FindWindow(window_class_name, None)
    if not hwnd:
        raise RuntimeError(f"找不到窗口：{window_class_name}")

    wndproc_func = WNDPROC(_wndproc)

    SetWindowLongPtr = (
        ctypes.windll.user32.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8
        else ctypes.windll.user32.SetWindowLongW
    )
    SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    SetWindowLongPtr.restype = ctypes.c_void_p

    old_proc_ptr = SetWindowLongPtr(hwnd, win32con.GWL_WNDPROC, wndproc_func)
    if not old_proc_ptr:
        raise RuntimeError("挂钩窗口失败")

    OldWndProcType = ctypes.WINFUNCTYPE(
        ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p
    )
    _global_state["hwnd"] = hwnd
    _global_state["wndproc_func"] = wndproc_func  # 防止被GC
    _global_state["old_wndproc"] = OldWndProcType(old_proc_ptr)

    print("✅ 窗口过程已挂钩")

def unhook_wndproc():
    """手动注销钩子"""
    hwnd = _global_state["hwnd"]
    old_proc = _global_state["old_wndproc"]
    if hwnd and old_proc:
        SetWindowLongPtr = (
            ctypes.windll.user32.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8
            else ctypes.windll.user32.SetWindowLongW
        )
        SetWindowLongPtr(hwnd, win32con.GWL_WNDPROC, old_proc)
        print("❎ 窗口过程已还原")

    # 清除引用，允许 GC
    _global_state["hwnd"] = None
    _global_state["old_wndproc"] = None
    _global_state["wndproc_func"] = None
