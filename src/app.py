import streamlit as st
import pandas as pd
import json
from streamlit_gsheets import GSheetsConnection

# --- 0. 配置与常量 ---
st.set_page_config(page_title="旅行打包助手 (云端同步版)", page_icon="🧳")

# --- 1. Google Sheets 连接与持久化 ---

# 初始化连接
# 注意：需要在 Streamlit Cloud 的 Secrets 中配置好 connection 信息
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """从 Google Sheets 加载数据"""
    try:
        # 读取表格内容
        df = conn.read(ttl=0) # ttl=0 确保每次都获取最新数据，不使用缓存
        if df.empty:
            return get_default_data()
        
        # 假设我们将数据以 key-value 形式存在表格里，或者直接存一个大的 JSON 字符串
        # 这里采用最稳妥的方式：将整个数据字典转为 JSON 存入第一行第一列
        raw_json = df.iloc[0, 0]
        return json.loads(raw_json)
    except Exception as e:
        # 如果读取失败（如表格为空或不存在），返回默认值
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
    """将数据保存回 Google Sheets"""
    data_to_save = {
        "templates": st.session_state.templates,
        "current_trip": st.session_state.current_trip
    }
    # 将字典转为 JSON 字符串并放入 DataFrame
    json_str = json.dumps(data_to_save, ensure_ascii=False)
    df = pd.DataFrame([json_str])
    
    # 更新到表格（这会覆盖整个工作表，简单高效）
    conn.update(data=df)

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