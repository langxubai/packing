import streamlit as st
import pandas as pd
import json
import os

# --- 0. 配置与常量 ---
st.set_page_config(page_title="旅行打包助手 (自动保存版)", page_icon="🧳")
DATA_FILE = "packing_data.json"

# --- 1. 持久化存储函数 ---

def load_data():
    """从本地加载数据，如果文件不存在则返回默认初始数据"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("数据文件损坏，已加载默认设置。")
            return get_default_data()
    else:
        return get_default_data()

def get_default_data():
    """默认的模板数据"""
    return {
        "templates": {
            "电子产品": ["手机充电器", "充电宝", "耳机", "电脑 & 充电器", "转换插头"],
            "洗漱用品": ["牙刷牙膏", "洗面奶", "毛巾", "洗发水小样"],
            "衣物": ["内衣裤 (x3)", "袜子 (x3)", "睡衣", "外套"],
            "证件/重要": ["护照/身份证", "现金/信用卡", "家门钥匙"]
        },
        "current_trip": {}
    }

def save_data():
    """将当前的 session_state 数据保存到本地 JSON 文件"""
    data_to_save = {
        "templates": st.session_state.templates,
        "current_trip": st.session_state.current_trip
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# --- 2. 初始化 Session State ---

if 'templates' not in st.session_state or 'current_trip' not in st.session_state:
    saved_data = load_data()
    st.session_state.templates = saved_data.get("templates", {})
    st.session_state.current_trip = saved_data.get("current_trip", {})

# --- 3. 业务逻辑函数 ---

def create_new_trip(selected_items):
    """根据选中的模板物品，重置当前旅行清单"""
    st.session_state.current_trip = {item: False for item in selected_items}
    save_data() # <--- 关键点：操作后立即保存
    st.success("新旅程清单已生成并保存！")

def toggle_item(item_name):
    """勾选/取消勾选物品时的回调函数"""
    # 状态取反
    st.session_state.current_trip[item_name] = not st.session_state.current_trip[item_name]
    save_data() # <--- 关键点：每次勾选都自动保存

# --- 4. 页面布局 ---

st.title("🧳 我的智能打包清单 (自动保存)")

tab1, tab2, tab3 = st.tabs(["✅ 开始打包", "🆕 新旅程", "📝 编辑模板"])

# ==========================================
# TAB 1: 打包执行 (Checklist)
# ==========================================
with tab1:
    st.header("当前打包进度")
    
    if not st.session_state.current_trip:
        st.info("目前没有进行中的打包任务，请去 '新建旅程' 页面生成一个！")
    else:
        # 计算进度
        total_items = len(st.session_state.current_trip)
        packed_items = sum(st.session_state.current_trip.values())
        progress = packed_items / total_items if total_items > 0 else 0
        
        st.progress(progress)
        st.caption(f"已完成: {packed_items}/{total_items}")

        if progress == 1.0:
            st.balloons()
            st.success("这就齐活了！祝你旅途愉快！✈️")

        st.divider()

        # 显示清单
        col1, col2 = st.columns(2)
        items = list(st.session_state.current_trip.keys())
        
        for i, item in enumerate(items):
            is_checked = st.session_state.current_trip[item]
            target_col = col1 if i % 2 == 0 else col2
            
            # 这里的逻辑稍微改了一下，使用 on_change 回调来实现实时保存
            target_col.checkbox(
                item, 
                value=is_checked, 
                key=f"check_{i}", 
                on_change=toggle_item, # 绑定回调函数
                args=(item,)           # 传参给回调函数
            )

        if st.button("重置当前清单状态（全部设为未打包）"):
            for k in st.session_state.current_trip:
                st.session_state.current_trip[k] = False
            save_data() # 保存重置后的状态
            st.rerun()

# ==========================================
# TAB 2: 新建旅程 (Selector)
# ==========================================
with tab2:
    st.header("准备出发去哪里？")
    st.write("从下方的模板中挑选这次需要带的东西：")
    
    with st.form("new_trip_form"):
        all_selected = []
        
        for category, items in st.session_state.templates.items():
            st.subheader(category)
            selected = st.multiselect(
                f"选择 {category}",
                items,
                default=items,
                key=f"select_{category}"
            )
            all_selected.extend(selected)
        
        st.divider()
        submitted = st.form_submit_button("生成清单 🚀")
        
        if submitted:
            if not all_selected:
                st.warning("请至少选择一项物品")
            else:
                create_new_trip(all_selected)
                # 强制刷新一下页面以跳转到最新状态（可选）
                st.rerun()

# ==========================================
# TAB 3: 模板管理 (Editor)
# ==========================================
with tab3:
    st.header("管理你的装备库")
    
    col_cat, col_edit = st.columns([1, 2])
    
    with col_cat:
        cat_list = list(st.session_state.templates.keys())
        if cat_list:
            selected_cat = st.radio("选择分类", cat_list)
        else:
            selected_cat = None
            st.warning("暂无分类，请先添加")

        st.markdown("---")
        # 添加新分类
        new_cat_name = st.text_input("新建分类名")
        if st.button("添加分类"):
            if new_cat_name and new_cat_name not in st.session_state.templates:
                st.session_state.templates[new_cat_name] = []
                save_data() # 保存
                st.success(f"分类 {new_cat_name} 已添加")
                st.rerun()
        
        # 删除分类
        if st.button("删除当前选中分类", type="primary"):
            if selected_cat:
                del st.session_state.templates[selected_cat]
                save_data() # 保存
                st.rerun()

    with col_edit:
        if selected_cat:
            current_items = st.session_state.templates[selected_cat]
            df = pd.DataFrame({"物品名称": current_items})
            
            edited_df = st.data_editor(
                df, 
                num_rows="dynamic", 
                key=f"editor_{selected_cat}",
                use_container_width=True
            )
            
            if st.button("保存该分类更改"):
                new_list = [x for x in edited_df["物品名称"].tolist() if x and str(x).strip() != ""]
                st.session_state.templates[selected_cat] = new_list
                save_data() # <--- 关键点：保存修改后的模板
                st.success(f"{selected_cat} 已更新并保存！")