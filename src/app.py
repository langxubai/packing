import streamlit as st
import pandas as pd
import json
import os
from streamlit_gsheets import GSheetsConnection

# --- 0. 配置与常量 ---
st.set_page_config(page_title="旅行打包助手", page_icon="🧳")

# --- 1. 智能连接初始化 ---

def get_connection():
    """
    自适应获取连接：
    1. 优先尝试寻找本地 .streamlit/google-creds.json
    2. 如果找不到，则由 st-gsheets-connection 自动寻找 Streamlit Cloud Secrets
    """
    local_creds = ".streamlit/google-creds.json"
    
    if os.path.exists(local_creds):
        # 本地开发模式：使用本地 JSON 文件路径
        return st.connection(
            "gsheets", 
            type=GSheetsConnection, 
            service_account=local_creds
        )
    else:
        # 云端部署模式：自动从 Secrets 中读取名为 [connections.gsheets] 的配置
        return st.connection("gsheets", type=GSheetsConnection)

# 初始化连接
conn = get_connection()

def load_data():
    """从云端加载数据"""
    try:
        # ttl=0 确保禁用缓存，获取最新勾选状态
        df = conn.read(ttl=0) 
        if df is not None and not df.empty:
            raw_json = df.iloc[0, 0]
            return json.loads(raw_json)
        return get_default_data()
    except Exception:
        return get_default_data()

def save_data():
    """保存数据到云端"""
    data_to_save = {
        "templates": st.session_state.templates,
        "current_trip": st.session_state.current_trip
    }
    json_str = json.dumps(data_to_save, ensure_ascii=False)
    df = pd.DataFrame([json_str])
    # 覆盖写入
    conn.update(data=df)

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

# --- 2. 初始化 Session State ---

if 'templates' not in st.session_state or 'current_trip' not in st.session_state:
    saved_data = load_data()
    st.session_state.templates = saved_data.get("templates", {})
    st.session_state.current_trip = saved_data.get("current_trip", {})

# --- 3. 业务逻辑函数 ---

def create_new_trip(selected_items):
    """根据选中的模板物品，重置当前旅行清单"""
    st.session_state.current_trip = {item: False for item in selected_items}
    save_data() 
    st.success("新旅程清单已同步至云端！")

def toggle_item(item_name):
    """勾选/取消勾选物品时的回调函数"""
    st.session_state.current_trip[item_name] = not st.session_state.current_trip[item_name]
    save_data() 

# --- 4. 页面布局 ---

st.title("🧳 智能打包清单 (云端同步版)")

tab1, tab2, tab3 = st.tabs(["✅ 开始打包", "🆕 新旅程", "📝 编辑模板"])

# --- TAB 1: 打包执行 ---
with tab1:
    st.header("当前打包进度")
    
    if not st.session_state.current_trip:
        st.info("目前没有进行中的打包任务，请去 '新建旅程' 页面生成一个！")
    else:
        total_items = len(st.session_state.current_trip)
        packed_items = sum(st.session_state.current_trip.values())
        progress = packed_items / total_items if total_items > 0 else 0
        
        st.progress(progress)
        st.caption(f"已完成: {packed_items}/{total_items}")

        if progress == 1.0:
            st.balloons()
            st.success("这就齐活了！祝你旅途愉快！✈️")

        st.divider()

        col1, col2 = st.columns(2)
        items = list(st.session_state.current_trip.keys())
        
        for i, item in enumerate(items):
            is_checked = st.session_state.current_trip[item]
            target_col = col1 if i % 2 == 0 else col2
            
            target_col.checkbox(
                item, 
                value=is_checked, 
                key=f"check_{i}", 
                on_change=toggle_item, 
                args=(item,)
            )

        if st.button("重置当前清单状态"):
            for k in st.session_state.current_trip:
                st.session_state.current_trip[k] = False
            save_data()
            st.rerun()

# --- TAB 2: 新建旅程 ---
with tab2:
    st.header("准备出发去哪里？")
    
    with st.form("new_trip_form"):
        all_selected = []
        for category, items in st.session_state.templates.items():
            st.subheader(category)
            selected = st.multiselect(f"选择 {category}", items, default=items, key=f"select_{category}")
            all_selected.extend(selected)
        
        if st.form_submit_button("生成清单 🚀"):
            if not all_selected:
                st.warning("请至少选择一项物品")
            else:
                create_new_trip(all_selected)
                st.rerun()

# --- TAB 3: 模板管理 ---
with tab3:
    st.header("管理你的装备库")
    col_cat, col_edit = st.columns([1, 2])
    
    with col_cat:
        cat_list = list(st.session_state.templates.keys())
        selected_cat = st.radio("选择分类", cat_list) if cat_list else None

        st.markdown("---")
        new_cat_name = st.text_input("新建分类名")
        if st.button("添加分类"):
            if new_cat_name and new_cat_name not in st.session_state.templates:
                st.session_state.templates[new_cat_name] = []
                save_data()
                st.rerun()
        
        if st.button("删除当前选中分类", type="primary"):
            if selected_cat:
                del st.session_state.templates[selected_cat]
                save_data()
                st.rerun()

    with col_edit:
        if selected_cat:
            current_items = st.session_state.templates[selected_cat]
            df_items = pd.DataFrame({"物品名称": current_items})
            edited_df = st.data_editor(df_items, num_rows="dynamic", use_container_width=True)
            
            if st.button("保存该分类更改"):
                new_list = [x for x in edited_df["物品名称"].tolist() if x and str(x).strip() != ""]
                st.session_state.templates[selected_cat] = new_list
                save_data()
                st.success(f"{selected_cat} 已更新并同步！")