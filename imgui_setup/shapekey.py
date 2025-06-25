import bpy
from imgui_bundle import imgui
from .selectable_input import selectable_input
from .imgui_global import GlobalImgui
from ..utils.mesh import has_shape_key
from ..utils.scene import get_all_collections
selected = False
def set_toggle_style_color(name,texture_id,condition,image_size=imgui.ImVec2(25.0, 25.0),tp=''):
    button_color =  imgui.ImVec4(0.33, 0.33, 0.33, 1)
    button_active_color =  imgui.ImVec4(71/255.0, 114/255.0, 179/255.0, 1)
    if condition:
        imgui.push_style_color(imgui.Col_.button.value, button_active_color)
        imgui.push_style_color(imgui.Col_.button_hovered.value, button_active_color)
        imgui.push_style_color(imgui.Col_.button_active.value, button_active_color)
    else:
        imgui.push_style_color(imgui.Col_.button.value, button_color)
        imgui.push_style_color(imgui.Col_.button_hovered.value, button_color)
        imgui.push_style_color(imgui.Col_.button_active.value, button_color)
    if GlobalImgui.get().image_btn.new(name, 
                            texture_id,
                            image_size=imgui.ImVec2(25.0, 25.0),tp=tp):pass

    imgui.pop_style_color()
    imgui.pop_style_color()
    imgui.pop_style_color()
def shapkey_widget(self):
    window_padding=imgui.get_style().window_padding
    item_spacing=imgui.get_style().item_spacing
    item_inner_spacing=imgui.get_style().item_inner_spacing
    indent_spacing=imgui.get_style().indent_spacing
    frame_padding=imgui.get_style().frame_padding
    global selected
    obj = bpy.context.object
    self.obj = obj
    if self.obj is None or self.obj.type!='MESH':return
    imgui.separator()
    imgui.set_next_item_open(True, cond=imgui.Cond_.once)
    # if imgui.tree_node("形态键"):
    if imgui.collapsing_header("形态键"):
        # if self.obj.type!='MESH':
        #     imgui.tree_pop()
        #     return
        imgui.begin_group()
        if not hasattr(self, "child_window_height"):
            self.child_window_height = 200  # 初始高度
        if not hasattr(self, "is_dragging_resizer_sk"):
            self.is_dragging_resizer_sk = False
        if not hasattr(self, "drag_sk_start_mouse_y"):
            self.drag_sk_start_mouse_y = 0
        if not hasattr(self, "start_height_sk"):
            self.start_height_sk = 200
        w=imgui.get_window_size().x-25 -indent_spacing*2-item_spacing.x-frame_padding.x-window_padding.x
        Scroll_width=w if w>230 else 230
        collections=get_all_collections(bpy.context.scene.collection)
        items = ['##Scene Collection' if cl.name == 'Scene Collection' else cl.name for cl in collections]


        if not hasattr(self, 'select_combo_filter'):
            self.select_combo_filter = imgui.TextFilter()
        # combo_preview_value 现在放后面更新
        combo_preview_value = items[GlobalImgui.get().item_current_idx]
        imgui.text("同步集合")
        imgui.same_line()
        text_len=imgui.calc_text_size('同步集合').x
        imgui.set_next_item_width(Scroll_width-text_len-50)
        if imgui.begin_combo("##combo", combo_preview_value,imgui.ComboFlags_.no_arrow_button):
            if imgui.is_window_appearing():
                imgui.set_keyboard_focus_here()
                self.select_combo_filter.clear()

            imgui.set_next_item_shortcut(imgui.Key.mod_ctrl | imgui.Key.f)
            self.select_combo_filter.draw("##Filter", -1)

            for n, it in enumerate(items):
                if it =='##Scene Collection':
                    continue
                if self.select_combo_filter.pass_filter(it):
                    is_selected = (GlobalImgui.get().item_current_idx == n)
                    if imgui.selectable(it, is_selected)[0]:
                        GlobalImgui.get().item_current_idx = n  # ⚠️ 会在下一个 frame 生效
                    if is_selected:
                        
                        imgui.set_item_default_focus()
            # print('选中了',GlobalImgui.get().item_current_idx)
            selected_text = items[GlobalImgui.get().item_current_idx]
            if selected_text !='##Scene Collection':
                try:
                    self.obj.mio3sksync.syncs=bpy.data.collections[f'{selected_text}']
                except:
                    print('请安装mio shapekey插件')
                # print('设置了')
            else:
                try:
                    self.obj.mio3sksync.syncs=None
                except:
                    print('请安装mio shapekey插件')
                # print('没设置')
            imgui.end_combo()
        
        if GlobalImgui.get().item_current_idx!=0:
            imgui.same_line()
            if GlobalImgui.get().image_btn.new("##btn_clear_sync_col", 
                                self.btn_clear_all_sk_value,
                                image_size=imgui.ImVec2(20.0, 20.0),tp='清除同步集合'):
                GlobalImgui.get().item_current_idx=0
                try:
                    self.obj.mio3sksync.syncs=None
                except:
                    print('请安装mio shapekey插件')
        # 滚动窗口
        imgui.push_style_color(imgui.Col_.child_bg, GlobalImgui.get().child_bg)
        visible = imgui.begin_child("ScrollableChild", imgui.ImVec2(Scroll_width, self.child_window_height), True)


            
        if visible:
        
            imgui.begin_group()
        
            if not hasattr(self, "shape_key_buf"):
                self.last_count = -1
                self.selected_index = -1
            # 每帧更新 obj 和 shape keys

            if has_shape_key(self.obj):
                
                key_blocks = self.obj.data.shape_keys.key_blocks
                # 判断 shape key 数量是否变化（或初始化）
                # if hasattr(self, "sk"):

                    # print(len(self.sk),len(key_blocks))
                if not hasattr(self, "sk") or self.last_count != len(key_blocks):
                    self.sk = key_blocks
                    self.shape_key_rows = []
                    for key in self.sk:
                        self.shape_key_rows.append({
                            "key": key,
                            "buf_name": [key.name],
                            "buf_value": [float(f"{key.value:.3f}")],
                        })
                else:
                    self.sk = key_blocks  # 同步最新 key_blocks

            else:
                self.sk = []
                self.shape_key_rows = []

            # 同步 Blender -> ImGui（仅当 ImGui 未主动选中时）
            if has_shape_key(self.obj) and self.obj.active_shape_key_index != self.selected_index:
                self.selected_index = self.obj.active_shape_key_index

            # UI 绘制
            for idx, row in enumerate(self.shape_key_rows):
                label = f"key_{idx}"
                is_selected = (self.selected_index == idx)
                row["buf_name"][0] = row['key'].name
                row["buf_value"][0] = float(f"{row['key'].value:.3f}")
                changed_name, changed_val, selected ,row["buf_name"][0]= selectable_input(
                    label,
                    self.selected_index == idx,
                    row["buf_name"],
                    row["buf_value"],
                    width=Scroll_width,
                )
                if selected:
                    self.selected_index = idx
                    if self.obj.active_shape_key_index != idx:
                        self.obj.active_shape_key_index = idx  # 👈 仅在 ImGui 中点击时更新 Blender
                if changed_name:
                    print(row["buf_name"][0])
                    row['key'].name = row["buf_name"][0]

                if changed_val:
                    try:
                        v = float(row["buf_value"][0])
                        v = max(min(v, row['key'].slider_max), row['key'].slider_min)
                        row["buf_value"][0] = float(f"{v:.3f}")
                        row['key'].value = row["buf_value"][0]

                        
                    except ValueError:
                        pass  # 非法输入不更新
            
            imgui.end_group()
            
            # ... (前面的代码保持不变) ...
        imgui.end_child()
        
        imgui.pop_style_color()

        # 拖动条高度（可视为拖拽手柄）
        resizer_height = 6
        cursor_pos_before_resizer = imgui.get_cursor_screen_pos()
        resizer_min = cursor_pos_before_resizer
        resizer_max = imgui.ImVec2(resizer_min.x + Scroll_width, resizer_min.y + resizer_height)

        # 1. 关键步骤：先设置光标并创建不可见的按钮
        #    这样我们才能在后面检查它的状态 (hovered, active)
        imgui.set_cursor_screen_pos(resizer_min)
        imgui.invisible_button("resizer", imgui.ImVec2(Scroll_width, resizer_height))

        # 2. 检查按钮状态来决定高亮效果和鼠标样式
        #    is_item_active: 正在被按住拖动
        #    is_item_hovered: 鼠标正悬停在上面
        is_active = imgui.is_item_active()
        is_hovered = imgui.is_item_hovered()

        # 根据状态选择颜色
        color_normal = imgui.get_color_u32(imgui.ImVec4(0.4, 0.4, 0.4, 1.0))
        color_hovered = imgui.get_color_u32(imgui.ImVec4(0.6, 0.6, 0.6, 1.0))
        color_active = imgui.get_color_u32(imgui.ImVec4(0.8, 0.8, 0.8, 1.0))

        resizer_color = color_normal
        if is_active:
            resizer_color = color_active
        elif is_hovered:
            resizer_color = color_hovered

        # <--- 新增：当悬停或激活时，改变鼠标光标样式为上下箭头
        if is_hovered or is_active:
            imgui.set_mouse_cursor(imgui.MouseCursor_.resize_ns)

        # 3. 根据上面确定的颜色，绘制拖动条
        draw_list = imgui.get_window_draw_list()
        draw_list.add_rect_filled(resizer_min, resizer_max, resizer_color)

        # 4. 处理拖拽逻辑 (这部分和之前一样)
        if is_active:
            if not self.is_dragging_resizer_sk:
                self.is_dragging_resizer_sk = True
                self.drag_sk_start_mouse_y = imgui.get_mouse_pos().y
                self.start_height_sk = self.child_window_height

            delta_y = imgui.get_mouse_pos().y - self.drag_sk_start_mouse_y
            self.child_window_height = max(50, self.start_height_sk + delta_y)
        else:
            self.is_dragging_resizer_sk = False
        imgui.end_group()
        # imgui.tree_pop()
    
        # imgui.set_cursor_screen_pos(imgui.ImVec2(resizer_min.x+100, resizer_max.y))
        imgui.same_line()
        imgui.begin_group()
        if GlobalImgui.get().image_btn.new("##btn_add_sk", 
                                self.btn_add_sk,
                                image_size=imgui.ImVec2(25.0, 25.0),tp='新建空白形态键'):pass
        # imgui.new_line()
        if GlobalImgui.get().image_btn.new("##btn_rm_sk", 
                                self.btn_rm_sk,
                                image_size=imgui.ImVec2(25.0, 25.0),tp='移除选中形态键'):pass
        # imgui.new_line()
        if GlobalImgui.get().image_btn.new("##btn_sk_special", 
                                self.btn_sk_special,
                                image_size=imgui.ImVec2(25.0, 25.0),tp='mio占位符\n暂不可用'):pass
        # imgui.new_line()
        if GlobalImgui.get().image_btn.new("##btn_mv_sk_up", 
                                self.btn_mv_sk_up,
                                image_size=imgui.ImVec2(25.0, 25.0),tp='上移形态键'):pass
        # imgui.new_line()
        if GlobalImgui.get().image_btn.new("##btn_mv_sk_down", 
                                self.btn_mv_sk_down,
                                image_size=imgui.ImVec2(25.0, 25.0),tp='下移形态键'):pass
        if GlobalImgui.get().image_btn.new("##btn_clear_all_sk_value", 
                                self.btn_clear_all_sk_value,
                                image_size=imgui.ImVec2(25.0, 25.0),tp='把所有形态键设为0'):pass
        imgui.end_group()
        slider_width=0
        if has_shape_key(self.obj) and not self.obj.active_shape_key_index==0:
            imgui.push_style_color(imgui.Col_.frame_bg, imgui.ImVec4(0.32, 0.32, 0.32, 1)) 
            imgui.push_style_color(imgui.Col_.frame_bg_hovered, imgui.ImVec4(0.47, 0.47, 0.47, 1))
            imgui.push_style_color(imgui.Col_.frame_bg_active, imgui.ImVec4(0.16, 0.16, 0.16, 1))
            imgui.push_item_width((Scroll_width-imgui.calc_text_size('minmax').x-50-imgui.get_style().item_spacing.x)/2)
            _,bpy.context.object.active_shape_key.slider_min=imgui.drag_float('min',bpy.context.object.active_shape_key.slider_min, v_speed=0.01)
            imgui.same_line()
            _,bpy.context.object.active_shape_key.slider_max=imgui.drag_float('max',bpy.context.object.active_shape_key.slider_max, v_speed=0.01)
            imgui.pop_item_width()
            imgui.pop_style_color(3)
            imgui.same_line()
        slider_width=Scroll_width-25
        imgui.set_cursor_pos_x(slider_width)
        set_toggle_style_color("##btn_solo_active_sk",
                               self.btn_solo_active_sk,
                               bpy.context.object.show_only_shape_key,tp='单独显示形态键')
        imgui.same_line()
        set_toggle_style_color("##btn_sk_edit_mode",
                               self.btn_sk_edit_mode,
                               bpy.context.object.use_shape_key_edit_mode,tp='形态键编辑模式')