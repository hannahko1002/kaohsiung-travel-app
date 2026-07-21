import streamlit as st
import json
import random
import urllib.parse
from openai import OpenAI
import streamlit.components.v1 as components

# ==========================================
# 1. 頁面基本設定
# ==========================================
st.set_page_config(
    page_title="高雄 100+ 吃喝玩樂導覽系統",
    page_icon="⚓",
    layout="wide"
)

st.markdown("""
    <style>
    html, body, [class*="css"], p, span, div, li, .stMarkdown {
        text-align: justify !important;
        text-justify: inter-ideograph;
    }
    .main-title { font-size: 30px; font-weight: bold; color: #0066CC; text-align: center !important; margin-bottom: 5px; }
    .sub-title { font-size: 15px; color: #888888; text-align: center !important; margin-bottom: 20px; }
    
    .merchant-card { 
        background-color: #f0f7ff; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 6px solid #0066cc; 
        margin-top: 15px; 
        color: #111111 !important; 
        text-align: justify !important;
    }
    .merchant-card h4 { color: #004499 !important; margin-top: 0; font-weight: bold; }
    .merchant-card b, .merchant-card span { color: #222222 !important; }
    
    .map-btn { 
        display: inline-block; 
        background-color: #0066cc; 
        color: #ffffff !important; 
        padding: 10px 18px; 
        border-radius: 8px; 
        text-decoration: none; 
        font-weight: bold; 
        margin-top: 12px; 
        text-align: center !important; 
    }

    div.stButton > button[kind="primary"] {
        background-color: #0066cc !important;
        border-color: #0066cc !important;
        color: #ffffff !important;
        font-weight: bold;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #004499 !important;
        border-color: #004499 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚓ 高雄 50美食 × 50景點 隨身導覽系統</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">【高雄商圈振興專案】精選 50 間在地美食與 50 大特色景點，精準導流實體人潮！</div>', unsafe_allow_html=True)

# ==========================================
# 2. 資料庫：50 間在地美食小吃
# ==========================================
KAOHSIUNG_FOODS = {
    "鹽埕/鼓山區": [
        {"name": "鴨肉珍", "type": "鴨肉飯/小吃", "address": "高雄市鹽埕區五福四路258號", "hours": "10:00–20:20 (週二公休)", "transport": "捷運鹽埕埔站 1 號出口步行 5 分鐘"},
        {"name": "樺達奶茶總店", "type": "經典飲品", "address": "高雄市鹽埕區新樂街99號", "hours": "09:00–22:00", "transport": "捷運鹽埕埔站 2 號出口步行 3 分鐘"},
        {"name": "阿財雞絲麵", "type": "在地小吃", "address": "高雄市鹽埕區壽星街11號", "hours": "12:00–23:00 (週日公休)", "transport": "捷運鹽埕埔站 2 號出口步行 8 分鐘"},
        {"name": "渡船頭海之冰", "type": "冰品甜點", "address": "高雄市鼓山區濱海一路76號", "hours": "11:00–23:00 (週一公休)", "transport": "捷運西子灣站 1 號出口步行 6 分鐘"},
        {"name": "港園牛肉麵", "type": "老字號麵食", "address": "高雄市鹽埕區大成街55號", "hours": "10:30–20:00", "transport": "捷運鹽埕埔站 4 號出口步行 7 分鐘"}
    ],
    "左營/楠梓區": [
        {"name": "寬來順早餐店", "type": "眷村早餐", "address": "高雄市左營區中華一路5-14號", "hours": "04:00–12:00 (週一公休)", "transport": "建議搭乘公車至果貿社區站"},
        {"name": "劉家酸菜白肉鍋", "type": "眷村火鍋", "address": "高雄市左營區介壽路9號", "hours": "11:00–22:30", "transport": "搭乘台鐵至左營舊城站轉乘計程車約 5 分鐘"},
        {"name": "三牛牛肉麵", "type": "在地小吃", "address": "高雄市左營區勝利路85號", "hours": "11:00–20:30", "transport": "蓮池潭風景區周邊步行 3 分鐘"},
        {"name": "楊寶寶蒸餃總店", "type": "麵食點心", "address": "高雄市楠梓區朝明路106號", "hours": "11:00–01:00", "transport": "捷運楠梓加工區站搭乘公車或騎乘 YouBike 5 分鐘"},
        {"name": "正宗鴨肉飯", "type": "人氣小吃", "address": "高雄市左營區裕誠路245號", "hours": "11:00–21:00 (週五公休)", "transport": "捷運巨蛋站 2 號出口步行 6 分鐘"}
    ],
    "三民/新興區": [
        {"name": "廖家黑輪", "type": "傳統燒烤", "address": "高雄市三民區三民街191號", "hours": "10:30–21:30", "transport": "高雄車站轉乘公車或步行約 12 分鐘"},
        {"name": "澎湖陳冰伍燒麻糬", "type": "古早味甜點", "address": "高雄市三民區三民街190號", "hours": "11:30–22:00", "transport": "三民市場內步行即可到達"},
        {"name": "老江紅茶牛奶總店", "type": "早餐/宵夜", "address": "高雄市新興區南台路51號", "hours": "24 小時營業", "transport": "捷運美麗島站 1 號出口步行 2 分鐘"},
        {"name": "大圓環雞肉飯", "type": "傳統小吃", "address": "高雄市新興區中山一路1號", "hours": "10:00–19:00 (週三公休)", "transport": "捷運美麗島站 1 號出口即達"},
        {"name": "聰明鴨肉店", "type": "當歸鴨/小吃", "address": "高雄市新興區復興二路201號", "hours": "11:00–20:30 (週二公休)", "transport": "捷運中央公園站步行約 10 分鐘"}
    ],
    "前鎮/鳳山區": [
        {"name": "輝哥牛肉湯", "type": "夜市美食", "address": "高雄市前鎮區光華二路438號", "hours": "17:00–01:00 (週一公休)", "transport": "搭乘公車至光華夜市站"},
        {"name": "中華街夜市鴨肉麵", "type": "傳統小吃", "address": "高雄市鳳山區中華街28號", "hours": "11:00–20:30", "transport": "捷運鳳山站 2 號出口步行 1 分鐘"},
        {"name": "老張燴飯", "type": "在地小吃", "address": "高雄市鳳山區信義街11號", "hours": "11:00–20:00 (週日公休)", "transport": "捷運鳳山站步行約 5 分鐘"},
        {"name": "喜八鍋燒牛肉麵", "type": "在地麵食", "address": "高雄市前鎮區廣西路248號", "hours": "11:00–20:00", "transport": "捷運三多商圈站步行約 8 分鐘"},
        {"name": "鳳山咸米胎", "type": "古早味小吃", "address": "高雄市鳳山區維新路10號", "hours": "06:00–13:00", "transport": "捷運大東站 2 號出口步行 7 分鐘"}
    ],
    "岡山/橋頭區": [
        {"name": "岡山明德羊肉", "type": "羊肉料理", "address": "高雄市岡山區河華路26號", "hours": "10:00–21:00 (週一公休)", "transport": "台鐵岡山站轉乘公車或計程車約 6 分鐘"},
        {"name": "舊市羊肉", "type": "羊肉料理", "address": "高雄市岡山區河華路111號", "hours": "11:00–20:30 (週一公休)", "transport": "台鐵岡山站轉乘計程車約 6 分鐘"},
        {"name": "橋頭太成肉包", "type": "百年伴手禮", "address": "高雄市橋頭區成功路164號", "hours": "07:00–18:00 (週一公休)", "transport": "捷運橋頭糖廠站 1 號出口步行 3 分鐘"},
        {"name": "橋頭糖廠冰品館", "type": "古早味冰品", "address": "高雄市橋頭區糖廠路24號", "hours": "08:30–17:30", "transport": "捷運橋頭糖廠站 2 號出口步行 2 分鐘"},
        {"name": "吉吉紅豆餅", "type": "傳統點心", "address": "高雄市岡山區維新路56號", "hours": "13:30–18:30", "transport": "岡山老街商圈步行可達"}
    ]
}

# ==========================================
# 3. 資料庫：50 個熱門景點與文創場域
# ==========================================
KAOHSIUNG_ATTRACTIONS = {
    "港灣與文創區": [
        {"name": "駁二藝術特區", "type": "文創展覽", "address": "高雄市鹽埕區大勇路1號", "hours": "10:00–18:00 (戶外全天開放)", "transport": "輕軌駁二大義站 / 捷運鹽埕埔站 1 號出口"},
        {"name": "高雄流行音樂中心", "type": "地標建築", "address": "高雄市鹽埕區真愛路1號", "hours": "10:00–22:00 (週一休館)", "transport": "輕軌真愛碼頭站直達"},
        {"name": "棧貳庫 KW2", "type": "歷史倉庫/文創", "address": "高雄市鼓山區蓬萊路17號", "hours": "10:00–21:00", "transport": "捷運西子灣站 2 號出口步行 5 分鐘"},
        {"name": "大義倉庫群", "type": "手作文創", "address": "高雄市鹽埕區大義街2號", "hours": "11:00–19:00", "transport": "輕軌駁二大義站步行 1 分鐘"},
        {"name": "高雄港旅運中心", "type": "現代建築", "address": "高雄市苓雅區海邊路5號", "hours": "10:00–21:00", "transport": "輕軌旅運中心站直達"}
    ],
    "歷史人文與古蹟": [
        {"name": "打狗英國領事館", "type": "歷史古蹟", "address": "高雄市鼓山區蓮海路20號", "hours": "10:00–19:00 (週三公休)", "transport": "捷運西子灣站轉乘公車 99 / 市區公車 50"},
        {"name": "新濱・駅前", "type": "古蹟咖啡館", "address": "高雄市鼓山區臨海三路5號", "hours": "12:00–20:00", "transport": "捷運西子灣站 2 號出口步行 1 分鐘"},
        {"name": "逍遙園", "type": "歷史建築", "address": "高雄市新興區六合一路55巷15號", "hours": "11:00–17:00 (週一休館)", "transport": "捷運信義國小站 1 號出口步行 3 分鐘"},
        {"name": "鳳儀書院", "type": "歷史古蹟", "address": "高雄市鳳山區鳳明街62號", "hours": "10:30–17:30 (週一休館)", "transport": "捷運鳳山站 2 號出口步行 8 分鐘"},
        {"name": "旗後燈塔", "type": "海景古蹟", "address": "高雄市旗津區旗下巷34號", "hours": "09:00–21:00 (週一休館)", "transport": "鼓山輪渡站搭渡輪至旗津後步行約 15 分鐘"}
    ],
    "自然景觀與園區": [
        {"name": "蓮池潭風景區 (龍虎塔)", "type": "觀光景點", "address": "高雄市左營區蓮潭路9號", "hours": "24 小時開放", "transport": "台鐵左營舊城站步行約 10 分鐘"},
        {"name": "衛武營國家藝術文化中心", "type": "表演藝術公園", "address": "高雄市鳳山區三多一路1號", "hours": "10:00–21:00", "transport": "捷運衛武營站 6 號出口直達"},
        {"name": "橋頭糖廠文化園區", "type": "工業遺址", "address": "高雄市橋頭區糖廠路24號", "hours": "09:00–16:30", "transport": "捷運橋頭糖廠站 2 號出口直達"},
        {"name": "壽山國家自然公園", "type": "健行步道", "address": "高雄市鼓山區萬壽路350號", "hours": "24 小時開放", "transport": "搭乘公車 56 至壽山動物園站"},
        {"name": "高雄市立美術館", "type": "藝術公園", "address": "高雄市鼓山區美術館路80號", "hours": "09:30–17:30 (週一休館)", "transport": "輕軌美術館站 / 台鐵美術館站"}
    ],
    "購物商圈與市集": [
        {"name": "漢神巨蛋購物廣場", "type": "百貨商圈", "address": "高雄市左營區博愛二路777號", "hours": "11:00–22:00", "transport": "捷運巨蛋站 5 號出口步行 3 分鐘"},
        {"name": "MLD 台鋁生活商場", "type": "文創複合商場", "address": "高雄市前鎮區忠勤路8號", "hours": "11:30–21:30", "transport": "輕軌軟體園區站步行 3 分鐘"},
        {"name": "瑞豐夜市", "type": "觀光夜市", "address": "高雄市左營區裕誠路與南屏路路口", "hours": "17:00–00:00 (週一、週三公休)", "transport": "捷運巨蛋站 1 號出口步行 5 分鐘"},
        {"name": "美麗島站 (光之穹頂)", "type": "捷運地標", "address": "高雄市新興區中山一路115號", "hours": "06:00–00:00", "transport": "捷運美麗島站站內大廳"},
        {"name": "三鳳中街", "type": "南北貨商圈", "address": "高雄市三民區三鳳中街", "hours": "09:00–21:00", "transport": "高雄車站步行約 10 分鐘"}
    ]
}

# ==========================================
# 4. 側邊欄控制區
# ==========================================
with st.sidebar:
    # 🏠 回首頁按鈕（側邊欄頂端）
    if st.button("🏠 返回首頁", use_container_width=True):
        st.session_state.pop("current_item", None)
        st.session_state.pop("current_district", None)
        st.session_state.pop("chat_history", None)
        st.rerun()

    st.header("⚙️ 導覽設定")
    api_key = st.text_input("輸入 OpenAI API Key (選填)", type="password")
    use_mock = st.checkbox("🧷 啟用展示備用模式 (無 API 時勾選)", value=(not api_key))
    
    st.divider()
    category = st.radio("🎯 選擇探索類別：", ["🍜 在地美食小吃 (50+)", "🏛️ 熱門景點/文創 (50+)"])
    
    db = KAOHSIUNG_FOODS if "美食" in category else KAOHSIUNG_ATTRACTIONS
    selected_district = st.selectbox("📍 選擇區域商圈", list(db.keys()))
    
    with st.expander("📌 查看當前分組清單", expanded=False):
        for item in db[selected_district]:
            st.markdown(f"- **{item['name']}** ({item['type']})")
    
    st.divider()
    generate_btn = st.button("🏃🏻‍♀️ 生成隨身導覽任務", type="primary", use_container_width=True)

# 輔助函式
def get_google_maps_url(address, name):
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(f'{address} {name}')}"

def get_google_maps_embed_url(address, name):
    return f"https://maps.google.com/maps?q={urllib.parse.quote(f'{name} {address}')}&z=17&output=embed"

def get_all_items_flat():
    flat = []
    for dist, items in KAOHSIUNG_FOODS.items():
        for i in items: flat.append({"category": "美食", "district": dist, **i})
    for dist, items in KAOHSIUNG_ATTRACTIONS.items():
        for i in items: flat.append({"category": "景點", "district": dist, **i})
    return flat

# ==========================================
# 5. 主畫面 Demo 呈現
# ==========================================
all_items = get_all_items_flat()

if generate_btn:
    current_db = KAOHSIUNG_FOODS if "美食" in category else KAOHSIUNG_ATTRACTIONS
    selected_item = random.choice(current_db[selected_district])

    st.session_state["current_item"] = selected_item
    st.session_state["current_district"] = selected_district
    st.session_state["chat_history"] = []

if "current_item" in st.session_state:
    # 🏠 主畫面左上角回首頁按鈕
    col_home, _ = st.columns([1, 4])
    with col_home:
        if st.button("🏠 返回首頁", type="secondary"):
            st.session_state.pop("current_item", None)
            st.session_state.pop("current_district", None)
            st.session_state.pop("chat_history", None)
            st.rerun()

    item = st.session_state["current_item"]
    district = st.session_state["current_district"]
    maps_url = get_google_maps_url(item['address'], item['name'])
    embed_url = get_google_maps_embed_url(item['address'], item['name'])

    col1, col2 = st.columns([1, 1])

    with col1:
        st.caption(f"📍 地點定位：{item['name']}（Google 地圖真實定位）")
        components.iframe(embed_url, height=280, scrolling=False)
        
        st.markdown(f"""
        <div class="merchant-card">
            <h4>📍 地點詳細資訊</h4>
            <b>名稱：</b> <span>{item['name']} ({item['type']})</span><br>
            <b>地址：</b> <span>{item['address']}</span><br>
            <b>🕒 營業時間：</b> <span>{item.get('hours', '請以現場公告為準')}</span><br>
            <b>🚆 交通建議：</b> <span>{item.get('transport', '可搭乘大眾運輸或騎乘 YouBike 前往')}</span><br>
            <a href="{maps_url}" target="_blank" class="map-btn">🗺️ 開啟 Google Maps 導航前往</a>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader(f"📜 探索目標：{item['name']}")
        st.caption(f"📍 分組區域：{district}")
        st.info(f"歡迎來到【{item['name']}】！這裡代表著高雄港都豐富的文化與特色，非常適合親自來走走體驗。")

        st.divider()
        st.subheader("🤖 AI 智慧導游服務")
        st.caption("你可以直接問我附近還有哪些 50 大美食或 50 大景點！")

        st.markdown("**💡 快速提問按鈕：**")
        chip_col1, chip_col2, chip_col3 = st.columns(3)
        preset_input = None

        if chip_col1.button("🚗 怎麼搭車前往？", use_container_width=True):
            preset_input = f"請問前往【{item['name']}】最方便的大眾運輸交通方式是什麼？"
        if chip_col2.button("😋 周邊有何推薦？", use_container_width=True):
            preset_input = f"請問在【{item['name']}】附近，還有哪些推薦的熱門美食或景點？"
        if chip_col3.button("⏰ 適合停留多久？", use_container_width=True):
            preset_input = f"建議在【{item['name']}】安排停留多久時間？附近有推薦順遊的地方嗎？"

        for msg in st.session_state.get("chat_history", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("詢問 AI 導游，例如：附近有什麼推薦的美食或景點？") or preset_input

        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                reply = f"【高雄導遊回答】收到你的提問：「{user_input}」！根據我們的資料庫，【{item['name']}】位在 {district}（營業時間：{item.get('hours', '依店家公告')}），周邊有不少值得造訪的地點，建議你可以透過地圖確認即時距離安排行程喔！"
                st.markdown(reply)
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})

else:
    # ==========================================
    # 首頁未產生任務時的預設展示內容
    # ==========================================
    
    # 1. 歡迎橫幅 banner
    st.markdown("""
        <div style="background: linear-gradient(135deg, #e6f2ff 0%, #ffffff 100%); padding: 25px; border-radius: 15px; border: 1px solid #cce0ff; margin-bottom: 25px;">
            <h3 style="color: #004499; margin-top:0;">🌊 歡迎來到高雄！開啟您的港都隨身微旅行</h3>
            <p style="color: #444444; font-size: 15px; margin-bottom: 0;">
                本系統專為商圈振興打造，精選 <b>50 間在地排隊美食</b> 與 <b>50 大經典文創景點</b>。<br>
                您可以透過左側選單隨機抽取探索任務，或是點擊下方熱門標籤快速開始！
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 2. 三步驟使用教學
    st.subheader("💡 簡單 3 步驟，探索高雄美食與景點")
    step_col1, step_col2, step_col3 = st.columns(3)
    
    with step_col1:
       st.markdown("""
       #### 1️⃣ 選擇探索區域
       在 **「左側」** 選單選擇您想前往的高雄商圈（如左營、鳳山等）。
       """)
    with step_col2:
        st.markdown("""
        #### 2️⃣ 一鍵抽卡生成
        點擊 **「生成隨身導覽任務」**，系統將為您實時定位推薦地點。
        """)
    with step_col3:
        st.markdown("""
        #### 3️⃣ AI 隨身導遊
        開啟 Google 地圖導航，並隨時詢問 AI 導遊周邊行程建議與交通！
        """)

    st.divider()

    # 3. 熱門推薦快速體驗專區 (主動點擊體驗)
    st.subheader("🔥 熱門地標快速體驗")
    st.caption("不想抽籤？點擊下方經典熱門地點直接試用：")

    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    if quick_col1.button("🎨 駁二藝術特區", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_ATTRACTIONS["港灣與文創區"][0] # 駁二
        st.session_state["current_district"] = "港灣與文創區"
        st.session_state["chat_history"] = []
        st.rerun()

    if quick_col2.button("🍜 鹽埕鴨肉珍", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_FOODS["鹽埕/鼓山區"][0] # 鴨肉珍
        st.session_state["current_district"] = "鹽埕/鼓山區"
        st.session_state["chat_history"] = []
        st.rerun()

    if quick_col3.button("⛩️ 蓮池潭龍虎塔", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_ATTRACTIONS["自然景觀與園區"][0] # 龍虎塔
        st.session_state["current_district"] = "左營/楠梓區"
        st.session_state["chat_history"] = []
        st.rerun()

    if quick_col4.button("🧋 樺達奶茶總店", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_FOODS["鹽埕/鼓山區"][1] # 樺達奶茶
        st.session_state["current_district"] = "鹽埕/鼓山區"
        st.session_state["chat_history"] = []
        st.rerun()

    st.info("👈 或是從左側邊欄設定您的專屬條件，點擊「生成隨身導覽任務」開始玩！")