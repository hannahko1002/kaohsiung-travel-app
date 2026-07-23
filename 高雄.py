import streamlit as st
import json
import random
import urllib.parse
import streamlit.components.v1 as components
import os
import requests

st.set_page_config(
    page_title="高雄 100+ 吃喝玩樂導覽系統",
    layout="wide"
)
st.markdown("""
    <style>
    .block-container {
        padding-top: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    html, body, [class*="css"], p, span, div, li, .stMarkdown {
        text-align: justify !important;
        text-justify: inter-ideograph;
    }
    .main-title { font-size: 40px; font-weight: bold; color: #0066CC; text-align: center !important; margin-bottom: 5px; }
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
    
    .line-share-btn {
        display: inline-block;
        background-color: #00B900;
        color: white !important;
        font-weight: bold;
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

if "current_item" not in st.session_state:
    st.info("👈 從左側邊欄設定您的專屬條件，點擊「生成隨機導覽」開始玩！")


# ==========================================
# 3. Gemini API 即時資料產生層
# ==========================================

# 高雄市 38 個行政區（2010 年縣市合併後的完整名單，含 3 個原住民區）
KAOHSIUNG_DISTRICTS = [
    "鹽埕區", "鼓山區", "左營區", "楠梓區", "三民區", "新興區", "前金區",
    "苓雅區", "前鎮區", "旗津區", "小港區",
    "鳳山區", "林園區", "大寮區", "大樹區", "大社區", "仁武區", "鳥松區",
    "岡山區", "橋頭區", "燕巢區", "田寮區", "阿蓮區", "路竹區", "湖內區",
    "茄萣區", "永安區", "彌陀區", "梓官區", "旗山區", "美濃區", "六龜區",
    "甲仙區", "杉林區", "內門區", "茂林區", "桃源區", "那瑪夏區",
]

# 景點仍維持原本 4 個主題分區，內容改由 Gemini 即時生成
KAOHSIUNG_ATTRACTION_ZONES = ["港灣與文創區", "歷史人文與古蹟", "自然景觀與園區", "購物商圈與市集"]

def _get_gemini_api_key():
    """優先讀取 Streamlit secrets，其次讀取環境變數 GEMINI_API_KEY。"""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY")


FOOD_ITEM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "type": {"type": "STRING"},
        "address": {"type": "STRING"},
        "hours": {"type": "STRING"},
        "desc": {"type": "STRING"},
        "parking_car": {"type": "STRING"},
        "parking_scooter": {"type": "STRING"},
        "parking_bike": {"type": "STRING"},
        "transit": {"type": "STRING"},
    },
    "required": ["name", "type", "address", "hours", "desc",
                 "parking_car", "parking_scooter", "parking_bike", "transit"],
}

ATTRACTION_ITEM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "type": {"type": "STRING"},
        "address": {"type": "STRING"},
        "hours": {"type": "STRING"},
        "desc": {"type": "STRING"},
        "transport": {"type": "STRING"},
    },
    "required": ["name", "type", "address", "hours", "desc", "transport"],
}


GEMINI_MODEL_FALLBACKS = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash"]


def _call_gemini(prompt, item_schema, api_key):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {"type": "ARRAY", "items": item_schema},
            "temperature": 0.9,
        },
    }

    last_error = None
    for model_name in GEMINI_MODEL_FALLBACKS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        resp = requests.post(url, json=payload, timeout=45)

        if resp.status_code == 404:
            # 這個模型名稱已被 Google 下架/不存在，改試下一個備用模型
            last_error = RuntimeError(f"模型 {model_name} 已無法使用（404），改嘗試下一個備用模型...")
            continue
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API（{model_name}）回傳 HTTP {resp.status_code}：{resp.text[:500]}")

        data = resp.json()

        if "candidates" not in data or not data["candidates"]:
            block_reason = data.get("promptFeedback", {}).get("blockReason", "無 candidates 欄位")
            raise RuntimeError(f"Gemini（{model_name}）未回傳任何內容（原因：{block_reason}）")

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Gemini（{model_name}）回傳格式不符預期：{data}") from e

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Gemini（{model_name}）回傳內容不是合法 JSON：{text[:500]}") from e

    raise last_error or RuntimeError("所有備用模型皆無法使用")



@st.cache_data(ttl=3600, show_spinner="🤖 AI 正在為您搜尋在地美食小吃...")
def generate_foods(district, api_key):
    prompt = f"""你是熟悉台灣高雄市在地美食文化的導覽專家。
請針對高雄市「{district}」，推薦 6 間該行政區內具代表性、口碑良好的美食小吃店家（可包含小吃、餐廳、飲料、甜點等）。
請以繁體中文撰寫，語氣生動、貼近觀光導覽文案風格。
每一間店家請提供以下欄位：
- name：店名
- type：類型（例如「鴨肉飯/老字號小吃」）
- address：地址（格式須為「高雄市{district}...」）
- hours：營業時間
- desc：40～80字特色簡介。內容須聚焦在「這間店」本身：招牌菜色、風味特色、食材或烹調方式、在地人氣原因等，每間店的寫法都要不同，避免使用千篇一律的罐頭句子；可適度提及「{district}」在地飲食文化或街區氛圍作為背景，但主角是店家本身而非整個行政區。
- parking_car：汽車停車資訊建議
- parking_scooter：機車停車資訊建議
- parking_bike：YouBike 站點資訊建議
- transit：大眾運輸（捷運/輕軌/公車）前往方式建議
請直接輸出 JSON 陣列，不要加上任何其他文字或 Markdown 標記。"""
    return _call_gemini(prompt, FOOD_ITEM_SCHEMA, api_key)


@st.cache_data(ttl=3600, show_spinner="🤖 AI 正在為您搜尋熱門景點...")
def generate_attractions(zone, api_key):
    prompt = f"""你是熟悉台灣高雄市觀光景點的導覽專家。
請針對高雄市「{zone}」這個主題分區，推薦 5 個屬於此類型、位於高雄市內具代表性的景點或文創商店。
請以繁體中文撰寫，語氣生動、貼近觀光導覽文案風格。
每一個景點請提供以下欄位：
- name：景點名稱
- type：類型（例如「文創展覽」）
- address：地址（須為「高雄市...」的完整地址）
- hours：開放時間
- desc：40～80字特色簡介。內容須聚焦在「這個景點」本身：歷史背景、建築或自然特色、可以體驗的活動、值得造訪的理由等，每個景點的寫法都要不同，避免使用千篇一律的罐頭句子；可適度呼應「{zone}」這個主題分區的調性，但主角是景點本身，不要寫成美食介紹。
- transport：建議的大眾運輸前往方式
請直接輸出 JSON 陣列，不要加上任何其他文字或 Markdown 標記。"""
    return _call_gemini(prompt, ATTRACTION_ITEM_SCHEMA, api_key)


def get_items(is_food, key):
    """依照分類與地區/主題，取得（快取的）Gemini 即時生成清單。"""
    api_key = _get_gemini_api_key()
    if not api_key:
        return []
    try:
        if is_food:
            return generate_foods(key, api_key)
        else:
            return generate_attractions(key, api_key)
    except Exception as e:
        st.session_state["gemini_error"] = str(e)
        return []


if _get_gemini_api_key() is None:
    st.error(
        "⚠️ 尚未設定 Gemini API 金鑰，無法載入即時資料。\n\n"
        "請在 Streamlit Cloud 的「App settings → Secrets」中加入：\n\n"
        "```\nGEMINI_API_KEY = \"你的金鑰\"\n```\n\n"
        "或在本機執行時，先設定環境變數 GEMINI_API_KEY 後再重新啟動 App。"
    )
    st.stop()

# ==========================================
# 4. 側邊欄控制區
# ==========================================
with st.sidebar:

    st.header("🎯 選擇探索類別：")
    category = st.radio(
        "選擇類別", 
        ["🍜 在地美食小吃 ", "🏛️ 熱門景點/文創商店"],
        label_visibility="collapsed"
    )
    
    is_food = "美食" in category
    district_options = KAOHSIUNG_DISTRICTS if is_food else KAOHSIUNG_ATTRACTION_ZONES
    selected_district = st.selectbox("📍 選擇區域商圈", district_options)

    with st.expander("📌 查看當前分組清單", expanded=False):
        preview_key = f"preview_{'food' if is_food else 'attr'}_{selected_district}"
        if st.button("🔍 載入清單預覽", key=f"btn_{preview_key}", use_container_width=True):
            st.session_state[preview_key] = get_items(is_food, selected_district)

        preview_items = st.session_state.get(preview_key)
        if preview_items:
            for item in preview_items:
                st.markdown(f"- **{item['name']}** ({item['type']})")
        elif preview_items is not None:
            st.caption("⚠️ 暫時無法取得 AI 即時資料，請稍後再試一次。")
        else:
            st.caption("點擊上方按鈕才會呼叫 AI 載入清單（避免浪費 API 額度）。")

    st.divider()

    generate_btn = st.button("🎲 生成隨機導覽", type="primary", use_container_width=True)

# 輔助函式
def get_google_maps_url(address, name):
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(f'{address} {name}')}"

def get_google_maps_embed_url(address, name):
    return f"https://maps.google.com/maps?q={urllib.parse.quote(f'{name} {address}')}&z=17&output=embed"

def get_parking_info_by_mode(item, mode):
    if "汽車" in mode:
        return item.get("parking_car", "周邊設有汽車收費停車場或路邊停車格。")
    elif "機車" in mode:
        return item.get("parking_scooter", "周邊設有劃線機車停車格。")
    elif "YouBike" in mode or "腳踏車" in mode:
        return item.get("parking_bike", "鄰近設有 YouBike 2.0 租還站點。")
    else:
        return item.get("transit", "建議搭乘捷運、輕軌或公車前往。")

def pick_next_item(candidates, current_item=None):
    if not candidates:
        return None
    if current_item and len(candidates) > 1:
        candidates = [x for x in candidates if x["name"] != current_item["name"]]
    return random.choice(candidates)

# ==========================================
# 5. 主畫面呈現
# ==========================================
if generate_btn:
    candidates = get_items(is_food, selected_district)
    selected_item = pick_next_item(candidates)

    if selected_item is None:
        st.session_state.pop("current_item", None)
        st.session_state.pop("current_district", None)
        err_detail = st.session_state.get("gemini_error", "未知錯誤（可能是 API 額度用完或回傳格式異常）")
        st.error(f"⚠️ 這次向 Gemini 取得「{selected_district}」的資料失敗，請稍後再試一次。\n\n錯誤詳情：{err_detail}")
    else:
        st.session_state["current_item"] = selected_item
        st.session_state["current_district"] = selected_district
        st.session_state["current_is_food"] = is_food
        st.session_state["chat_history"] = []

if st.session_state.get("current_item"):
    item = st.session_state["current_item"]
    district = st.session_state["current_district"]
    maps_url = get_google_maps_url(item['address'], item['name'])
    embed_url = get_google_maps_embed_url(item['address'], item['name'])

    btn_col1, btn_col2, btn_col3, _ = st.columns([1.3, 1.3, 1.3, 5.5])

    with btn_col1:
        if st.button("🏠 返回首頁", type="secondary", use_container_width=True):
            st.session_state.pop("current_item", None)
            st.session_state.pop("current_district", None)
            st.session_state.pop("chat_history", None)
            st.rerun()

    with btn_col2:
        if st.button("🎲 換個推薦", type="secondary", use_container_width=True):
            is_food_now = st.session_state.get("current_is_food", is_food)
            candidates = get_items(is_food_now, selected_district)
            next_item = pick_next_item(candidates, st.session_state.get("current_item"))
            if next_item is None:
                err_detail = st.session_state.get("gemini_error", "未知錯誤（可能是 API 額度用完或回傳格式異常）")
                st.error(f"⚠️ 這次無法取得新的推薦，請稍後再試一次。\n\n錯誤詳情：{err_detail}")
            else:
                st.session_state["current_item"] = next_item
                st.session_state["chat_history"] = []
                st.rerun()

    with btn_col3:
        @st.dialog("🔗 分享地點給好友")
        def share_dialog():
            share_text = f"分享高雄好去處：【{item['name']}】（{item['type']}）！\n📍 地址：{item['address']}\n🗺️ Google 地圖導航：{maps_url}"
            line_url = f"https://line.me/R/msg/text/?{urllib.parse.quote(share_text)}"

            st.write(f"**將【{item['name']}】分享給好友一起玩！**")
            st.code(share_text, language=None)

            st.markdown(
                f'<a href="{line_url}" target="_blank" class="line-share-btn">💬 一鍵分享至 LINE</a>',
                unsafe_allow_html=True,
            )

        if st.button("🔗 分享連結", type="secondary", use_container_width=True):
            share_dialog()

if st.session_state.get("current_item"):
    item = st.session_state["current_item"]
    district = st.session_state.get("current_district", "高雄市")

    col1, col2 = st.columns([1, 1])

    with col1:
        components.iframe(embed_url, height=350, scrolling=False)
        
        st.markdown(f"""
        <div class="merchant-card">
            <h4>📍 地點詳細資訊</h4>
            <b>🏷️ 名稱：</b> <span>{item['name']} ({item['type']})</span><br>
            <b>📌 地址：</b> <span>{item['address']}</span><br>
            <b>🕒 營業時間：</b> <span>{item.get('hours', '請以現場公告為準')}</span><br>
            <a href="{maps_url}" target="_blank" class="map-btn">🗺️ 開啟 Google Maps 導航前往</a>
        </div>
        """, unsafe_allow_html=True)
        st.caption("ℹ️ 以上資料由 Gemini AI 即時生成，實際地址／營業時間請以店家公告或 Google 地圖最新資訊為準。")

    with col2:
        # 僅在此處加上 margin-top 修正，向上拉平對齊左側的 caption
        st.markdown(f"<h3 style='margin-top: -12px; margin-bottom: 4px; font-weight: bold;'>探索目標：{item['name']}</h3>", unsafe_allow_html=True)
        st.caption(f"📍 行政區劃：{district}")
        
        # 動態取得 item['desc']，如果沒有介紹則依美食／景點分別顯示不同的備用預設文字
        is_food_now = st.session_state.get("current_is_food", is_food)
        if is_food_now:
            fallback_desc = f"歡迎品嚐【{item['name']}】！這是{district}在地人氣的{item.get('type', '美食小吃')}，不妨親自到店裡感受道地的高雄好味道。"
        else:
            fallback_desc = f"歡迎造訪【{item['name']}】！這是{district}深具代表性的{item.get('type', '景點')}，很適合安排時間親自走一趟細細體驗。"
        item_desc = item.get('desc') or fallback_desc
        st.info(f"💡 **特色簡介**：{item_desc}")

        st.divider()
        st.subheader("AI 智慧導游服務")
        
        transport_mode = st.selectbox(
            "請選擇您的交通工具（將為您精準提供對應停車地點）：",
            ["🚗 汽車", "🛵 機車", "🚲 YouBike ", "🚊 捷運 "],
            index=0
        )

        specific_parking = get_parking_info_by_mode(item, transport_mode)
        st.success(f"**【{transport_mode}】停車導引：** {specific_parking}")

        st.markdown("**💡 快速提問按鈕：**")
        chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
        preset_input = None

        if chip_col1.button("🌤️ 即時天氣", use_container_width=True):
            preset_input = f"請問【{district}】現在的天氣和氣溫如何？"
        if chip_col2.button("🅿️ 停車資訊", use_container_width=True):
            preset_input = f"請問以【{item['name']}】為中心，駕駛/騎乘【{transport_mode}】過來，最方便的專屬停車地點在哪裡？"
        if chip_col3.button("🏛️ 熱門景點", use_container_width=True):
            preset_input = f"請問【{item['name']}】附近有哪些推薦的熱門景點？"
        if chip_col4.button("☕️ 精選咖啡", use_container_width=True):
            preset_input = f"請問【{item['name']}】附近有哪些適合休息的氣氛咖啡廳？"

        user_input = st.chat_input("詢問導游，例如：附近哪裡好停車？") or preset_input or ""

        if user_input and isinstance(user_input, str):
            embed_map_url = None
            location_base = f"高雄市 {item['address']} {item['name']}"
            
            if any(keyword in user_input for keyword in ["天氣", "氣溫", "溫度", "下雨", "雨", "幾度", "熱嗎", "帶傘", "天候"]):
                try:
                    import urllib3

                    # 🙈 關閉 SSL 安全警告訊息
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                    # 🔑 貼上你剛剛測試成功的 API Key
                    CWA_API_KEY = "CWA-FE43BB08-FB1C-44AA-9236-4A0E0F221D5C".strip()
                    
                    # 💡 關鍵：直接將 Key 帶在網址 URL 裡面（不要放在 headers）
                    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={CWA_API_KEY}"
                    
                    response = requests.get(url, timeout=5, verify=False)
                    
                    if response.status_code != 200:
                        raise Exception(f"HTTP {response.status_code}: {response.text}")

                    data = response.json()
                    
                    # 解析中央氣象署 JSON 結構（欄位為 PascalCase）
                    records = data.get("records", {})
                    locations = records.get("Locations", [{}])[0].get("Location", []) if "Locations" in records else records.get("Location", [])
                    
                    # 精準比對區域 (例如：鹽埕區)
                    # 💡 聰明模糊比對：無論 district 是 "鹽埕區"、"鹽埕" 還是 "港灣與文創區" 都能抓到！
                    target_loc = None
                    clean_district = district.replace("區", "").strip()

                    for loc in locations:
                        loc_name = loc.get("LocationName", "")
                        # 雙向比對：只要文字有重疊（例如 "鹽埕" 在 "鹽埕區" 裡面）就命中！
                        if clean_district in loc_name or loc_name in district:
                            target_loc = loc
                            break
                    
                    # 💡 保底機制：如果真的找不到（例如傳入非行政區名稱），預設抓第一筆（通常是第一個區）
                    if not target_loc and locations:
                        target_loc = locations[0]

                    if not target_loc:
                        raise Exception(
                            f"氣象署有回應但抓不到地區資料。records 的 keys={list(records.keys())}"
                        )

                    weather_elements = target_loc.get("WeatherElement", [])
                    temp = "暫無數據"
                    weather_desc = "多雲時晴"
                    for elem in weather_elements:
                        if elem.get("ElementName") == "溫度":
                            temp = elem["Time"][0]["ElementValue"][0]["Temperature"]
                        elif elem.get("ElementName") == "天氣現象":
                            weather_desc = elem["Time"][0]["ElementValue"][0]["Weather"]

                    reply = (
                        f"🌤️ **【中央氣象署】高雄市 {district} 即時氣象預報**\n\n"
                        f"• **當前定位**：高雄市 {district}（鄰近 {item['name']}）\n"
                        f"• **預報氣溫**：約 `{temp}°C`\n"
                        f"• **天氣狀況**：{weather_desc}\n\n"
                        f"💡 *出門造訪【{item['name']}】前記得留意天氣變化，做好防曬或隨身攜帶雨具！*"
                    )
                except Exception as e:
                    reply = (
                        f"🌤️ **【高雄市 {district}】氣象導覽**\n\n"
                        f"⚠️ **連線狀況**：無法即時取得氣象署連線（原因：`{e}`）\n\n"
                        f"💡 高雄市 {district} 通常陽光充足，造訪【{item['name']}】建議做好防曬！"
                    )
            elif "停車" in user_input:
                # 取得店家/地點名稱與地址
                place_name = item['name']
                place_address = item['address']

                if "YouBike" in transport_mode or "腳踏車" in transport_mode:
                    search_label = "YouBike 站"
                    # 搜尋關鍵字：YouBike near 店家地址
                    # 地圖會以店家為中心，並標出周邊 YouBike 站點
                    search_query = f"YouBike near {place_address}"
                    icon = "🚲"
                elif "大眾運輸" in transport_mode or "捷運" in transport_mode:
                    search_label = "捷運站"
                    # 搜尋關鍵字：捷運站 near 店家地址
                    search_query = f"捷運站 near {place_address}"
                    icon = "🚊"
                else:
                    search_label = "停車場"
                    # 搜尋關鍵字：停車場 near 店家地址
                    search_query = f"停車場 near {place_address}"
                    icon = "🅿️"

                # 組合 URL：
                # 1. z=15: 適中視角，確保能同時涵蓋店家與周邊站點
                # 2. hl=zh-TW: 繁體中文介面
                encoded_query = urllib.parse.quote(search_query)
                embed_map_url = f"https://maps.google.com/maps?q={encoded_query}&z=15&hl=zh-TW&output=embed"

                reply = (
                    f"{icon} **為您搜尋【{place_name}】周邊的{search_label}！**\n\n"
                    f"📍 **店家地址：** {place_address}\n"
                    f"**交通建議資訊：**\n{specific_parking}\n\n"
                    f"💡 *下方地圖已標示【{place_name}】的位置及其周邊的{search_label}！*"
                )
                # 咖啡廳 相關提問
            elif "咖啡" in user_input:
                # 使用 "咖啡廳 near 地址"
                search_query = f"咖啡廳 near {item['address']}"
                
                # 咖啡廳通常距離較近，z=15 或 z=16 均可
                encoded_query = urllib.parse.quote(search_query)
                embed_map_url = f"https://maps.google.com/maps?q={encoded_query}&z=15&hl=zh-TW&output=embed"

                reply = (
                    f"☕ **為您搜尋【{item['name']}】周邊精選咖啡廳！**\n\n"
                    f"下方地圖已標示【{item['name']}】周邊的咖啡廳位置，您可以直接點選查看評價與距離："
                )
                # 景點 / 順遊 相關提問
            elif "景點" in user_input:
                # 簡化搜尋關鍵字為 "景點 near 地址" 或 "tourist attraction near 地址"
                search_query = f"景點 near {item['address']}"
                
                # z=15 比例最適中，hl=zh-TW 確保中文語系
                encoded_query = urllib.parse.quote(search_query)
                embed_map_url = f"https://maps.google.com/maps?q={encoded_query}&z=15&hl=zh-TW&output=embed"
                
                reply = (
                    f"🏛️ **為您搜尋【{item['name']}】周邊熱門景點！**\n\n"
                    f"來到【{district}】，除了造訪【{item['name']}】外，周邊還有許多熱門景點可直接從下方地圖查看："
                )
            # 5. 其他提問預設回答
            # 其他自由提問
            else:
                # 建議使用 "user_input near 地址" 的組合，避免直接串接造成無效搜尋
                search_query = f"{user_input} near {item['address']}"
                encoded_query = urllib.parse.quote(search_query)
                embed_map_url = f"https://maps.google.com/maps?q={encoded_query}&z=15&hl=zh-TW&output=embed"
                
                reply = (
                    f"ℹ️ **關於【{item['name']}】的「{user_input}」資訊：**\n\n"
                    f"• **地點名稱**：{item['name']} ({item['type']})\n"
                    f"• **地址**：{item['address']}\n"
                    f"• **營業時間**：{item.get('hours', '請依現場公告為準')}\n"
                    f"• **當前選擇交通方式**：{transport_mode}\n\n"
                    f"已為您在下方地圖搜尋相關位置資訊！"
                )

            # 渲染導覽回答與實時動態 Google 地圖
            st.markdown(f"**🤖 導游回答：**\n\n{reply}")
            if embed_map_url:
                components.iframe(embed_map_url, height=350, scrolling=False)

# 尚未生成或選擇景點時，顯示首頁提示與熱門按鈕
else:
    st.markdown('<div class="main-title">高雄 38 行政區 × AI 即時美食景點導覽系統</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">【高雄商圈振興專案】由 Gemini AI 即時生成在地美食與特色景點，精準導流實體人潮！</div>', unsafe_allow_html=True)

    st.subheader("💡 簡單 3 步驟，探索高雄美食與景點")
    step_col1, step_col2, step_col3 = st.columns(3)
  
    with step_col1:
        st.markdown("#### 1️⃣ 選擇探索區域\n在 **「左側」** 選單選擇想前往的高雄行政區。")
    with step_col2:
        st.markdown("#### 2️⃣ 一鍵抽卡生成\n點擊 **「生成隨機導覽」**，系統將為您推薦地點。")
    with step_col3:
        st.markdown("#### 3️⃣ 開啟個人化導覽\n依照交通方式與需求，獲得最佳路徑與景點安排！")

    st.divider()

    st.subheader("🔥 熱門地標快速體驗")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    if quick_col1.button("🎨 駁二藝術特區周邊", use_container_width=True):
        items = get_items(False, "港灣與文創區")
        if items:
            st.session_state["current_item"] = items[0]
            st.session_state["current_district"] = "港灣與文創區"
            st.session_state["current_is_food"] = False
            st.session_state["chat_history"] = []
            st.rerun()

    if quick_col2.button("🍜 鹽埕區在地美食", use_container_width=True):
        items = get_items(True, "鹽埕區")
        if items:
            st.session_state["current_item"] = items[0]
            st.session_state["current_district"] = "鹽埕區"
            st.session_state["current_is_food"] = True
            st.session_state["chat_history"] = []
            st.rerun()

    if quick_col3.button("🐲 蓮池潭周邊景點", use_container_width=True):
        items = get_items(False, "自然景觀與園區")
        if items:
            st.session_state["current_item"] = items[0]
            st.session_state["current_district"] = "左營區"
            st.session_state["current_is_food"] = False
            st.session_state["chat_history"] = []
            st.rerun()

    if quick_col4.button("🧋 鹽埕區特色飲品", use_container_width=True):
        items = get_items(True, "鹽埕區")
        if items:
            idx = 1 if len(items) > 1 else 0
            st.session_state["current_item"] = items[idx]
            st.session_state["current_district"] = "鹽埕區"
            st.session_state["current_is_food"] = True
            st.session_state["chat_history"] = []
            st.rerun()
