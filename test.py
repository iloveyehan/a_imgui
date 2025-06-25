imgui.push_id("##VerticalScrolling")
for i in range(5):
    if i > 0:
        imgui.same_line()
    imgui.begin_group()
    names = ["Top", "25%", "Center", "75%", "Bottom"]
    imgui.text_unformatted(names[i])

    child_flags = imgui.WindowFlags_.menu_bar.value if static.enable_extra_decorations else 0
    child_id = imgui.get_id(f"{i}")
    child_is_visible = imgui.begin_child(child_id, ImVec2(child_w, 200.0), True, child_flags)
    if imgui.begin_menu_bar():
        imgui.text_unformatted("abc")
        imgui.end_menu_bar()
    if scroll_to_off:
        imgui.set_scroll_y(static.scroll_to_off_px)
    if scroll_to_pos:
        imgui.set_scroll_from_pos_y(imgui.get_cursor_start_pos().y + static.scroll_to_pos_px, i * 0.25)
    if child_is_visible:
        for item in range(100):
            if static.enable_track and item == static.track_item:
                imgui.text_colored(ImVec4(1, 1, 0, 1), f"Item {item}")
                imgui.set_scroll_here_y(i * 0.25)
            else:
                imgui.text(f"Item {item}")
    scroll_y = imgui.get_scroll_y()
    scroll_max_y = imgui.get_scroll_max_y()
    imgui.end_child()
    imgui.text(f"{scroll_y:.0f}/{scroll_max_y:.0f}")
    imgui.end_group()
imgui.pop_id()