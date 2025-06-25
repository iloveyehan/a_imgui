from .imgui_global import GlobalImgui
from imgui_bundle import imgui

from .text_input_event import on_text_edit
def selectable_input(label: str, selected: bool, buf1: list[str], buf2: list[float], width=0, flags=0) -> bool:
    imgui.push_id(label)
    imgui.push_style_var(imgui.StyleVar_.item_spacing,
                            (imgui.get_style().item_spacing.x, imgui.get_style().frame_padding.y * 2))

    # 关键修复1: 添加 allow_overlap 防止事件拦截
    selectable_flags = (
            flags |
            imgui.SelectableFlags_.allow_double_click |
            imgui.SelectableFlags_.no_auto_close_popups |
            imgui.SelectableFlags_.allow_overlap  # 允许其他组件接收事件
    )
    ret, selected_out = imgui.selectable("##Selectable", selected, selectable_flags,imgui.ImVec2(width, 20))
    imgui.pop_style_var()

    selectable_min = imgui.get_item_rect_min()
    height = imgui.get_item_rect_size().y
    width = 80 if width == 0 else width

    # ---------- 输入框 1 ----------
    input_id1 = imgui.get_id("##Input1")
    storage = imgui.get_state_storage()
    active1 = storage.get_bool(input_id1, False)

    rect1_min = selectable_min
    rect1_max = imgui.ImVec2(rect1_min.x + width*.6, rect1_min.y + height)

    # 修复双击判断逻辑
    if imgui.is_mouse_double_clicked(0) and imgui.is_mouse_hovering_rect(rect1_min, rect1_max):
        storage.set_bool(input_id1, True)
        # imgui.set_keyboard_focus_here(-1)  # 设置焦点到下一个控件

    changed1 = False
    changed=False
    if active1:
        imgui.set_cursor_screen_pos(rect1_min)
        imgui.push_item_width(width*0.6)
        # imgui.set_keyboard_focus_here()
        changed1, buf1[0] = imgui.input_text("##Input1", buf1[0], 
                                                flags=imgui.InputTextFlags_.auto_select_all|imgui.InputTextFlags_.enter_returns_true|imgui.InputTextFlags_.callback_always.value,
                                                callback=on_text_edit)
        imgui.pop_item_width()

        # 鼠标点击其他区域时，退出编辑状态
        # if imgui.is_item_deactivated_after_edit():
        #     storage.set_bool(input_id1, False)
        if (imgui.is_mouse_clicked(0) and not imgui.is_mouse_hovering_rect(rect1_min, rect1_max)) or imgui.is_key_down(imgui.Key.enter):
            # imgui.get_io().add_key_event(imgui.Key.enter, True)
            
            # storage.set_bool(input_id1, True)
            buf1[0]=GlobalImgui.get().text_input_buf
            storage.set_bool(input_id1, False)
            print(1111,changed1,buf1,buf1[0])
            changed=True
    else:
        def truncate_text_to_fit(text, max_width):
            result = ""
            total_width = 0
            for c in text:
                w = imgui.calc_text_size(c).x
                if total_width + w > max_width:
                    break
                result += c
                total_width += w
            return result
        truncated_text = truncate_text_to_fit(buf1[0], max_width=width*0.6)
        imgui.get_window_draw_list().add_text(
            imgui.ImVec2(rect1_min.x + 4, rect1_min.y + 2),
            imgui.get_color_u32(imgui.Col_.text),
            # buf1[0]
            truncated_text
        )

    # ---------- 输入框 2 ---------- (相同修复)
    imgui.same_line()
    imgui.set_cursor_pos(imgui.ImVec2(width*0.6, +imgui.get_cursor_pos().y-3))
    imgui.push_style_color(imgui.Col_.frame_bg, imgui.ImVec4(0.2, 0.2, 0.5, 0))  # 蓝色背景
    imgui.push_style_color(imgui.Col_.frame_bg_hovered, imgui.ImVec4(0.3, 0.3, 0.6, 0))
    imgui.push_style_color(imgui.Col_.frame_bg_active, imgui.ImVec4(0.4, 0.4, 0.7, 0))
    imgui.push_item_width(width*0.4)
    changed2,buf2[0]=imgui.drag_float("##Input2", buf2[0], v_speed=0.01)
    imgui.pop_item_width()
    imgui.pop_style_color(3)

    imgui.pop_id()
    return changed, changed2, selected_out,buf1[0]

def selectable_input_vg(label: str, selected: bool, buf1: list[str],  width=0, flags=0) -> bool:
    imgui.push_id(label)
    imgui.push_style_var(imgui.StyleVar_.item_spacing,
                            (imgui.get_style().item_spacing.x, imgui.get_style().frame_padding.y * 2))

    # 关键修复1: 添加 allow_overlap 防止事件拦截
    selectable_flags = (
            flags |
            imgui.SelectableFlags_.allow_double_click |
            imgui.SelectableFlags_.no_auto_close_popups |
            imgui.SelectableFlags_.allow_overlap  # 允许其他组件接收事件
    )
    ret, selected_out = imgui.selectable("##Selectable", selected, selectable_flags,imgui.ImVec2(width, 20))
    imgui.pop_style_var()

    selectable_min = imgui.get_item_rect_min()
    height = imgui.get_item_rect_size().y
    width = 80 if width == 0 else width

    # ---------- 输入框 1 ----------
    input_id1 = imgui.get_id("##Input2")
    storage = imgui.get_state_storage()
    active1 = storage.get_bool(input_id1, False)

    rect1_min = selectable_min
    rect1_max = imgui.ImVec2(rect1_min.x + width*.6, rect1_min.y + height)

    # 修复双击判断逻辑
    if imgui.is_mouse_double_clicked(0) and imgui.is_mouse_hovering_rect(rect1_min, rect1_max):
        storage.set_bool(input_id1, True)
        # imgui.set_keyboard_focus_here(-1)  # 设置焦点到下一个控件

    changed1 = False
    changed=False
    if active1:
        imgui.set_cursor_screen_pos(rect1_min)
        imgui.push_item_width(width*0.6)
        # imgui.set_keyboard_focus_here()
        changed1, buf1[0] = imgui.input_text("##Input1", buf1[0], 
                                                flags=imgui.InputTextFlags_.auto_select_all|imgui.InputTextFlags_.enter_returns_true|imgui.InputTextFlags_.callback_always.value,
                                                callback=on_text_edit)
        imgui.pop_item_width()

        # 鼠标点击其他区域时，退出编辑状态
        # if imgui.is_item_deactivated_after_edit():
        #     storage.set_bool(input_id1, False)
        if (imgui.is_mouse_clicked(0) and not imgui.is_mouse_hovering_rect(rect1_min, rect1_max)) or imgui.is_key_down(imgui.Key.enter):
            # imgui.get_io().add_key_event(imgui.Key.enter, True)
            
            # storage.set_bool(input_id1, True)
            buf1[0]=GlobalImgui.get().text_input_buf
            storage.set_bool(input_id1, False)
            print(1111,changed1,buf1,buf1[0])
            changed=True
    else:
        def truncate_text_to_fit(text, max_width):
            result = ""
            total_width = 0
            for c in text:
                w = imgui.calc_text_size(c).x
                if total_width + w > max_width:
                    break
                result += c
                total_width += w
            return result
        truncated_text = truncate_text_to_fit(buf1[0], max_width=width*0.6)
        imgui.get_window_draw_list().add_text(
            imgui.ImVec2(rect1_min.x + 4, rect1_min.y + 2),
            imgui.get_color_u32(imgui.Col_.text),
            # buf1[0]
            truncated_text
        )

    # imgui.pop_style_color(3)

    imgui.pop_id()
    return changed, selected_out,buf1[0]
