import ctypes
from ctypes import wintypes
import win32con, win32gui
from imgui_bundle import imgui

# 定义 Subclass 函数签名
SUBCLASSPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    ctypes.c_uint32,
    ctypes.c_uint32
)
SetWindowSubclass = ctypes.windll.comctl32.SetWindowSubclass
SetWindowSubclass.argtypes = [
    wintypes.HWND, SUBCLASSPROC,
    ctypes.c_uint32, ctypes.c_uint32
]
SetWindowSubclass.restype = wintypes.BOOL

DefSubclassProc = ctypes.windll.comctl32.DefSubclassProc
DefSubclassProc.argtypes = [
    wintypes.HWND, wintypes.UINT,
    wintypes.WPARAM, wintypes.LPARAM
]
DefSubclassProc.restype = ctypes.c_long

RemoveWindowSubclass = ctypes.windll.comctl32.RemoveWindowSubclass
RemoveWindowSubclass.argtypes = [
    wintypes.HWND, SUBCLASSPROC,
    ctypes.c_uint32
]
RemoveWindowSubclass.restype = wintypes.BOOL

class BlenderImeHook:
    def __init__(self):
        # 拿到 Blender 主窗口
        # self.hwnd = win32gui.FindWindow("GHOST_WindowClass", None)
        self.hwnd = ctypes.windll.user32.FindWindowW("GHOST_WindowClass", None)
        if not self.hwnd:
            raise RuntimeError("找不到 Blender 主窗口 HWND")

        # 包装成 ctypes 回调
        self._subclass_proc = SUBCLASSPROC(self._proc)
        # 注册子类
        if not SetWindowSubclass(
                self.hwnd,
                self._subclass_proc,
                ctypes.cast(self._subclass_proc, ctypes.c_void_p).value,
                0
        ):
            raise RuntimeError("SetWindowSubclass 失败")

    def shutdown(self):
        RemoveWindowSubclass(
            self.hwnd,
            self._subclass_proc,
            ctypes.cast(self._subclass_proc, ctypes.c_void_p).value
        )

    def _proc(self, hwnd, msg, wParam, lParam, uId, dwRefData):
        if msg == win32con.WM_IME_COMPOSITION:
            # 拿到已确认文字
            GCS_RESULTSTR = 0x0800
            hImc = ctypes.windll.imm32.ImmGetContext(hwnd)
            size = ctypes.windll.imm32.ImmGetCompositionStringW(
                hImc, GCS_RESULTSTR, None, 0
            )
            if size > 0:
                buf = ctypes.create_unicode_buffer(size // 2)
                ctypes.windll.imm32.ImmGetCompositionStringW(
                    hImc, GCS_RESULTSTR, buf, size
                )
                for ch in buf.value:
                    imgui.get_io().add_input_character(ord(ch))
            ctypes.windll.imm32.ImmReleaseContext(hwnd, hImc)
            return 0

        # 交给下一个 Subclass／原 WNDPROC
        return DefSubclassProc(hwnd, msg, wParam, lParam)
BlenderImeHook()