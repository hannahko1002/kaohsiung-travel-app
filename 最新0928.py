import streamlit as st
import json
import random
import time
import urllib.parse
import streamlit.components.v1 as components
import os
import requests
import hashlib
from pathlib import Path

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

# ==========================================
# 0-A. 語言選擇（一律顯示在左側邊欄最上方，登入前也看得到）
# ==========================================
LANG_OPTIONS = {
    "🇹🇼 繁體中文": "zh",
    "🇺🇸 English": "en",
    "🇯🇵 日本語": "ja",
    "🇰🇷 한국어": "ko",
}
LANG_NAMES_FOR_AI = {"zh": "繁體中文", "en": "English", "ja": "日本語", "ko": "한국어"}

if "lang" not in st.session_state:
    st.session_state["lang"] = "zh"


def _on_lang_change():
    st.session_state["lang"] = LANG_OPTIONS[st.session_state["lang_selector_widget"]]


with st.sidebar:
    st.selectbox(
        "🌐 Language / 語言",
        options=list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.values()).index(st.session_state["lang"]),
        key="lang_selector_widget",
        on_change=_on_lang_change,
    )

LANG = st.session_state["lang"]

TRANSLATIONS = {
    "zh": {
        "login_title": "高雄 100+ 吃喝玩樂導覽系統",
        "login_subtitle": "登入後即可收藏喜愛的地點，方便下次快速查看！",
        "tab_login": "🔑 登入",
        "tab_register": "📝 註冊新帳號",
        "field_account": "帳號",
        "field_password": "密碼",
        "field_reg_account": "設定帳號",
        "field_reg_password": "設定密碼",
        "btn_login": "登入",
        "btn_register": "註冊",
        "err_login_fail": "帳號或密碼不正確，請再試一次。",
        "msg_register_missing": "請輸入帳號與密碼。",
        "msg_register_exists": "這個帳號已經被註冊過了，請直接登入或換一個帳號名稱。",
        "msg_register_success": "🎉 註冊成功！請切換到「登入」分頁輸入帳密。",
        "guest_caption": "不想註冊？也可以先逛逛看：",
        "guest_btn": "🚶 以遊客身分繼續瀏覽（無法收藏地點）",
        "home_hint": "👈 從左側邊欄設定您的專屬條件，點擊「生成隨機導覽」開始玩！",
        "sidebar_guest_info": "🚶 目前為**遊客瀏覽模式**\n\n登入後可收藏地點！",
        "sidebar_login_btn": "🔑 前往登入 / 註冊",
        "sidebar_welcome": "👋 歡迎回來，**{user}**",
        "sidebar_logout": "🚪 登出",
        "sidebar_fav_header": "⭐ 我的收藏（{count}）",
        "sidebar_fav_empty": "目前還沒有收藏地點，逛逛看並點擊⭐收藏吧！",
        "sidebar_category_header": "🎯 選擇探索類別：",
        "category_food": "🍜 在地美食小吃 ",
        "category_attraction": "🏛️ 熱門景點/文創商店",
        "sidebar_district_label": "📍 選擇區域商圈",
        "expander_preview_label": "📌 查看當前分組清單",
        "preview_load_btn": "🔍 載入清單預覽",
        "preview_no_data": "⚠️ 暫時無法取得 AI 即時資料，請稍後再試一次。",
        "preview_hint": "點擊上方按鈕才會呼叫 AI 載入清單（避免浪費 API 額度）。",
        "generate_btn": "🎲 生成隨機導覽",
        "home_title": "高雄 AI 即時美食景點導覽系統",
        "home_subtitle": "【高雄商圈振興專案】即時生成在地美食與特色景點，精準導流實體人潮！",
        "home_step_header": "💡 簡單 3 步驟，探索高雄美食與景點",
        "home_step1": "#### 1️⃣ 選擇探索區域\n在 **「左側」** 選單選擇想前往的高雄行政區。",
        "home_step2": "#### 2️⃣ 一鍵抽卡生成\n點擊 **「生成隨機導覽」**，系統將為您推薦地點。",
        "home_step3": "#### 3️⃣ 開啟個人化導覽\n依照交通方式與需求，獲得最佳路徑與景點安排！",
        "home_quick_header": "🔥 熱門地標快速體驗",
        "quick1": "🎨 駁二藝術特區周邊",
        "quick2": "🍜 鹽埕區在地美食",
        "quick3": "🐲 蓮池潭周邊景點",
        "quick4": "🧋 鹽埕區特色飲品",
        "btn_home": "🏠 返回首頁",
        "btn_shuffle": "🎲 換個推薦",
        "btn_share": "🔗 分享連結",
        "share_dialog_title": "🔗 分享地點給好友",
        "share_write": "**將【{name}】分享給好友一起玩！**",
        "share_line_btn": "💬 一鍵分享至 LINE",
        "share_text_template": "分享高雄好去處：【{name}】（{type}）！\n📍 地址：{address}\n🗺️ Google 地圖導航：{url}",
        "fav_locked_btn": "🔒 登入才能收藏",
        "fav_add_btn": "⭐ 收藏地點",
        "fav_remove_btn": "💔 取消收藏",
        "fav_toast_add": "已收藏【{name}】！",
        "fav_toast_remove": "已將【{name}】從收藏移除",
        "detail_header": "📍 地點詳細資訊",
        "detail_name_label": "🏷️ 名稱：",
        "detail_address_label": "📌 地址：",
        "detail_hours_label": "🕒 營業時間：",
        "detail_map_btn": "🗺️ 開啟 Google Maps 導航前往",
        "detail_caption": "ℹ️ 以上資料由 Gemini AI 即時生成，實際地址／營業時間請以店家公告或 Google 地圖最新資訊為準。",
        "hours_fallback": "請以現場公告為準",
        "explore_target": "探索目標：{name}",
        "district_caption": "📍 行政區劃：{district}",
        "feature_desc_label": "💡 **特色簡介**：{desc}",
        "food_fallback_desc": "歡迎品嚐【{name}】！這是{district}在地人氣的{type}，不妨親自到店裡感受道地的高雄好味道。",
        "attraction_fallback_desc": "歡迎造訪【{name}】！這是{district}深具代表性的{type}，很適合安排時間親自走一趟細細體驗。",
        "guide_subheader": "AI 智慧導游服務",
        "transport_label": "請選擇您的交通工具（將為您精準提供對應停車地點）：",
        "transport_car": "🚗 汽車",
        "transport_scooter": "🛵 機車",
        "transport_bike": "🚲 YouBike ",
        "transport_mts": "🚊 捷運 ",
        "parking_result_label": "**【{mode}】停車導引：** {info}",
        "quick_question_label": "**💡 快速提問按鈕：**",
        "chip_weather": "🌤️ 即時天氣",
        "chip_parking": "🅿️ 停車資訊",
        "chip_attraction": "🏛️ 熱門景點",
        "chip_coffee": "☕️ 精選咖啡",
        "chat_input_placeholder": "詢問導游，例如：附近哪裡好停車？",
    },
    "en": {
        "login_title": "Kaohsiung 100+ Food & Fun Guide",
        "login_subtitle": "Log in to save your favorite spots for quick access later!",
        "tab_login": "🔑 Log In",
        "tab_register": "📝 Sign Up",
        "field_account": "Username",
        "field_password": "Password",
        "field_reg_account": "Choose a username",
        "field_reg_password": "Choose a password",
        "btn_login": "Log In",
        "btn_register": "Sign Up",
        "err_login_fail": "Incorrect username or password. Please try again.",
        "msg_register_missing": "Please enter a username and password.",
        "msg_register_exists": "This username is already taken. Please log in or choose another name.",
        "msg_register_success": "🎉 Sign-up successful! Switch to the 'Log In' tab to sign in.",
        "guest_caption": "Not ready to sign up? Browse as a guest first:",
        "guest_btn": "🚶 Continue as Guest (favorites disabled)",
        "home_hint": "👈 Set your preferences in the sidebar, then tap 'Generate Random Tour' to start!",
        "sidebar_guest_info": "🚶 You're browsing as a **Guest**\n\nLog in to save favorite spots!",
        "sidebar_login_btn": "🔑 Log In / Sign Up",
        "sidebar_welcome": "👋 Welcome back, **{user}**",
        "sidebar_logout": "🚪 Log Out",
        "sidebar_fav_header": "⭐ My Favorites ({count})",
        "sidebar_fav_empty": "No favorites yet. Explore and tap ⭐ to save a spot!",
        "sidebar_category_header": "🎯 Choose a category:",
        "category_food": "🍜 Local Food & Snacks ",
        "category_attraction": "🏛️ Popular Attractions/Creative Shops",
        "sidebar_district_label": "📍 Choose an area",
        "expander_preview_label": "📌 Preview current list",
        "preview_load_btn": "🔍 Load preview list",
        "preview_no_data": "⚠️ Couldn't fetch live AI data right now, please try again later.",
        "preview_hint": "Tap the button above to call the AI and load the list (to save API quota).",
        "generate_btn": "🎲 Generate Random Tour",
        "home_title": "Kaohsiung AI Real-Time Food & Attraction Guide",
        "home_subtitle": "【Kaohsiung Business District Revitalization】Instantly generates local food and attractions to drive foot traffic!",
        "home_step_header": "💡 3 Simple Steps to Explore Kaohsiung",
        "home_step1": "#### 1️⃣ Choose an Area\nSelect the Kaohsiung district you'd like to visit from the **sidebar**.",
        "home_step2": "#### 2️⃣ One-Tap Draw\nTap **'Generate Random Tour'** and the system will recommend a spot.",
        "home_step3": "#### 3️⃣ Get a Personalized Guide\nGet the best route and tips based on your transport and needs!",
        "home_quick_header": "🔥 Popular Landmarks - Quick Try",
        "quick1": "🎨 Pier-2 Art Center Area",
        "quick2": "🍜 Yancheng District Local Food",
        "quick3": "🐲 Lotus Pond Area Attractions",
        "quick4": "🧋 Yancheng District Signature Drinks",
        "btn_home": "🏠 Home",
        "btn_shuffle": "🎲 Try Another",
        "btn_share": "🔗 Share Link",
        "share_dialog_title": "🔗 Share this spot with a friend",
        "share_write": "**Share【{name}】with a friend!**",
        "share_line_btn": "💬 Share to LINE",
        "share_text_template": "Check out this Kaohsiung spot: 【{name}】({type})!\n📍 Address: {address}\n🗺️ Google Maps: {url}",
        "fav_locked_btn": "🔒 Log in to save",
        "fav_add_btn": "⭐ Save Spot",
        "fav_remove_btn": "💔 Remove Favorite",
        "fav_toast_add": "Saved 【{name}】to favorites!",
        "fav_toast_remove": "Removed 【{name}】from favorites",
        "detail_header": "📍 Location Details",
        "detail_name_label": "🏷️ Name:",
        "detail_address_label": "📌 Address:",
        "detail_hours_label": "🕒 Hours:",
        "detail_map_btn": "🗺️ Open in Google Maps",
        "detail_caption": "ℹ️ The above data is generated live by Gemini AI. Please confirm the actual address/hours with the venue or Google Maps.",
        "hours_fallback": "Please check on-site signage",
        "explore_target": "Exploring: {name}",
        "district_caption": "📍 District: {district}",
        "feature_desc_label": "💡 **Highlights**: {desc}",
        "food_fallback_desc": "Welcome to 【{name}】! A popular local {type} in {district} — come experience authentic Kaohsiung flavor in person.",
        "attraction_fallback_desc": "Welcome to 【{name}】! A landmark {type} in {district}, well worth setting aside time to explore.",
        "guide_subheader": "AI Smart Guide Service",
        "transport_label": "Choose your transport (we'll give precise parking info for it):",
        "transport_car": "🚗 Car",
        "transport_scooter": "🛵 Scooter",
        "transport_bike": "🚲 YouBike ",
        "transport_mts": "🚊 Metro ",
        "parking_result_label": "**【{mode}】Parking Guide:** {info}",
        "quick_question_label": "**💡 Quick question buttons:**",
        "chip_weather": "🌤️ Live Weather",
        "chip_parking": "🅿️ Parking Info",
        "chip_attraction": "🏛️ Nearby Attractions",
        "chip_coffee": "☕️ Top Cafés",
        "chat_input_placeholder": "Ask the guide, e.g. 'Where's a good place to park nearby?'",
    },
    "ja": {
        "login_title": "高雄100+グルメ・観光ガイド",
        "login_subtitle": "ログインするとお気に入りの場所を保存でき、次回すぐ確認できます！",
        "tab_login": "🔑 ログイン",
        "tab_register": "📝 新規登録",
        "field_account": "アカウント",
        "field_password": "パスワード",
        "field_reg_account": "アカウントを設定",
        "field_reg_password": "パスワードを設定",
        "btn_login": "ログイン",
        "btn_register": "登録",
        "err_login_fail": "アカウントまたはパスワードが正しくありません。もう一度お試しください。",
        "msg_register_missing": "アカウントとパスワードを入力してください。",
        "msg_register_exists": "このアカウントは既に登録されています。ログインするか、別の名前をお選びください。",
        "msg_register_success": "🎉 登録が完了しました！「ログイン」タブに切り替えてください。",
        "guest_caption": "登録せずに、まず見て回りたい方はこちら：",
        "guest_btn": "🚶 ゲストとして利用する（お気に入り機能は使えません）",
        "home_hint": "👈 左のサイドバーで条件を設定し、「ランダムツアーを生成」をタップして始めましょう！",
        "sidebar_guest_info": "🚶 現在**ゲストモード**です\n\nログインするとお気に入りを保存できます！",
        "sidebar_login_btn": "🔑 ログイン／新規登録へ",
        "sidebar_welcome": "👋 おかえりなさい、**{user}**さん",
        "sidebar_logout": "🚪 ログアウト",
        "sidebar_fav_header": "⭐ お気に入り（{count}）",
        "sidebar_fav_empty": "まだお気に入りはありません。⭐をタップして保存しましょう！",
        "sidebar_category_header": "🎯 カテゴリーを選択：",
        "category_food": "🍜 地元グルメ・軽食 ",
        "category_attraction": "🏛️ 人気観光地／クリエイティブショップ",
        "sidebar_district_label": "📍 エリアを選択",
        "expander_preview_label": "📌 現在のリストをプレビュー",
        "preview_load_btn": "🔍 プレビューを読み込む",
        "preview_no_data": "⚠️ 現在AIデータを取得できません。しばらくしてから再度お試しください。",
        "preview_hint": "上のボタンを押すとAIがリストを読み込みます（APIクォータ節約のため）。",
        "generate_btn": "🎲 ランダムツアーを生成",
        "home_title": "高雄AIリアルタイム・グルメ観光ガイド",
        "home_subtitle": "【高雄商圏活性化プロジェクト】地元グルメと観光地をリアルタイムに生成し、実店舗への集客を促進！",
        "home_step_header": "💡 簡単3ステップで高雄を探索",
        "home_step1": "#### 1️⃣ エリアを選択\n**「左側」**のメニューから訪れたい高雄の行政区を選んでください。",
        "home_step2": "#### 2️⃣ ワンタップ生成\n**「ランダムツアーを生成」**をタップすると、システムがおすすめを提案します。",
        "home_step3": "#### 3️⃣ パーソナライズガイドを開始\n交通手段やニーズに合わせて最適なルートを取得！",
        "home_quick_header": "🔥 人気スポットを今すぐ体験",
        "quick1": "🎨 駁二芸術特区周辺",
        "quick2": "🍜 塩埕区の地元グルメ",
        "quick3": "🐲 蓮池潭周辺の観光地",
        "quick4": "🧋 塩埕区の名物ドリンク",
        "btn_home": "🏠 ホームに戻る",
        "btn_shuffle": "🎲 他のおすすめ",
        "btn_share": "🔗 リンクを共有",
        "share_dialog_title": "🔗 友達にスポットをシェア",
        "share_write": "**【{name}】を友達にシェアしよう！**",
        "share_line_btn": "💬 LINEでシェア",
        "share_text_template": "高雄のおすすめスポット：【{name}】（{type}）！\n📍 住所：{address}\n🗺️ Googleマップ：{url}",
        "fav_locked_btn": "🔒 ログインで保存可能",
        "fav_add_btn": "⭐ お気に入りに追加",
        "fav_remove_btn": "💔 お気に入り解除",
        "fav_toast_add": "【{name}】をお気に入りに追加しました！",
        "fav_toast_remove": "【{name}】をお気に入りから削除しました",
        "detail_header": "📍 スポット詳細情報",
        "detail_name_label": "🏷️ 名称：",
        "detail_address_label": "📌 住所：",
        "detail_hours_label": "🕒 営業時間：",
        "detail_map_btn": "🗺️ Googleマップで開く",
        "detail_caption": "ℹ️ 上記の情報はGemini AIによりリアルタイム生成されています。実際の住所・営業時間は店舗の掲示またはGoogleマップの最新情報をご確認ください。",
        "hours_fallback": "現地の掲示をご確認ください",
        "explore_target": "探索スポット：{name}",
        "district_caption": "📍 行政区：{district}",
        "feature_desc_label": "💡 **特徴紹介**：{desc}",
        "food_fallback_desc": "【{name}】へようこそ！{district}で人気の{type}です。ぜひ店舗で本場高雄の味をお楽しみください。",
        "attraction_fallback_desc": "【{name}】へようこそ！{district}を代表する{type}です。時間をとってじっくり訪れる価値があります。",
        "guide_subheader": "AIスマートガイドサービス",
        "transport_label": "交通手段を選択してください（該当の駐車情報をご案内します）：",
        "transport_car": "🚗 車",
        "transport_scooter": "🛵 バイク",
        "transport_bike": "🚲 YouBike ",
        "transport_mts": "🚊 MRT ",
        "parking_result_label": "**【{mode}】駐車ガイド：** {info}",
        "quick_question_label": "**💡 クイック質問ボタン：**",
        "chip_weather": "🌤️ 現在の天気",
        "chip_parking": "🅿️ 駐車場情報",
        "chip_attraction": "🏛️ 周辺の観光地",
        "chip_coffee": "☕️ おすすめカフェ",
        "chat_input_placeholder": "ガイドに質問（例：近くの駐車場は？）",
    },
    "ko": {
        "login_title": "가오슝 100+ 먹거리·놀거리 가이드",
        "login_subtitle": "로그인하면 좋아하는 장소를 저장해 다음에 빠르게 확인할 수 있어요!",
        "tab_login": "🔑 로그인",
        "tab_register": "📝 회원가입",
        "field_account": "아이디",
        "field_password": "비밀번호",
        "field_reg_account": "아이디 설정",
        "field_reg_password": "비밀번호 설정",
        "btn_login": "로그인",
        "btn_register": "가입하기",
        "err_login_fail": "아이디 또는 비밀번호가 올바르지 않습니다. 다시 시도해 주세요.",
        "msg_register_missing": "아이디와 비밀번호를 입력해 주세요.",
        "msg_register_exists": "이미 등록된 아이디입니다. 로그인하거나 다른 이름을 사용해 주세요.",
        "msg_register_success": "🎉 가입이 완료되었습니다! '로그인' 탭에서 로그인해 주세요.",
        "guest_caption": "가입하지 않고 먼저 둘러보고 싶다면:",
        "guest_btn": "🚶 게스트로 둘러보기 (즐겨찾기 불가)",
        "home_hint": "👈 왼쪽 사이드바에서 조건을 설정하고 '무작위 투어 생성'을 눌러 시작하세요!",
        "sidebar_guest_info": "🚶 현재 **게스트 모드**입니다\n\n로그인하면 장소를 저장할 수 있어요!",
        "sidebar_login_btn": "🔑 로그인 / 회원가입",
        "sidebar_welcome": "👋 다시 오신 것을 환영합니다, **{user}**님",
        "sidebar_logout": "🚪 로그아웃",
        "sidebar_fav_header": "⭐ 내 즐겨찾기 ({count})",
        "sidebar_fav_empty": "아직 즐겨찾기가 없어요. 둘러보고 ⭐를 눌러 저장해 보세요!",
        "sidebar_category_header": "🎯 카테고리 선택：",
        "category_food": "🍜 현지 맛집·간식 ",
        "category_attraction": "🏛️ 인기 명소/문화상점",
        "sidebar_district_label": "📍 지역 선택",
        "expander_preview_label": "📌 현재 목록 미리보기",
        "preview_load_btn": "🔍 미리보기 불러오기",
        "preview_no_data": "⚠️ 지금은 AI 실시간 데이터를 가져올 수 없습니다. 잠시 후 다시 시도해 주세요.",
        "preview_hint": "위 버튼을 눌러야 AI가 목록을 불러옵니다 (API 사용량 절약을 위해).",
        "generate_btn": "🎲 무작위 투어 생성",
        "home_title": "가오슝 AI 실시간 맛집·명소 가이드",
        "home_subtitle": "【가오슝 상권 활성화 프로젝트】현지 맛집과 명소를 실시간 생성하여 오프라인 방문을 유도합니다!",
        "home_step_header": "💡 간단한 3단계로 가오슝 탐험하기",
        "home_step1": "#### 1️⃣ 탐색 지역 선택\n**'왼쪽'** 메뉴에서 방문하고 싶은 가오슝 행정구를 선택하세요.",
        "home_step2": "#### 2️⃣ 원터치 생성\n**'무작위 투어 생성'**을 누르면 시스템이 장소를 추천해 드려요.",
        "home_step3": "#### 3️⃣ 맞춤 가이드 시작\n교통수단과 필요에 맞춰 최적의 경로와 코스를 안내받으세요!",
        "home_quick_header": "🔥 인기 명소 빠른 체험",
        "quick1": "🎨 보얼 예술특구 주변",
        "quick2": "🍜 옌청구 현지 맛집",
        "quick3": "🐲 롄츠탄 주변 명소",
        "quick4": "🧋 옌청구 특색 음료",
        "btn_home": "🏠 홈으로",
        "btn_shuffle": "🎲 다른 추천 보기",
        "btn_share": "🔗 링크 공유",
        "share_dialog_title": "🔗 친구에게 장소 공유하기",
        "share_write": "**【{name}】을(를) 친구에게 공유하세요!**",
        "share_line_btn": "💬 LINE으로 공유",
        "share_text_template": "가오슝 추천 장소: 【{name}】（{type}）!\n📍 주소: {address}\n🗺️ 구글 지도: {url}",
        "fav_locked_btn": "🔒 로그인해야 저장 가능",
        "fav_add_btn": "⭐ 장소 저장",
        "fav_remove_btn": "💔 즐겨찾기 해제",
        "fav_toast_add": "【{name}】을(를) 즐겨찾기에 추가했어요!",
        "fav_toast_remove": "【{name}】을(를) 즐겨찾기에서 삭제했어요",
        "detail_header": "📍 장소 상세 정보",
        "detail_name_label": "🏷️ 이름:",
        "detail_address_label": "📌 주소:",
        "detail_hours_label": "🕒 영업시간:",
        "detail_map_btn": "🗺️ 구글 지도에서 열기",
        "detail_caption": "ℹ️ 위 정보는 Gemini AI가 실시간으로 생성했습니다. 실제 주소/영업시간은 매장 공지나 구글 지도 최신 정보를 확인해 주세요.",
        "hours_fallback": "현장 공지를 확인해 주세요",
        "explore_target": "탐색 대상: {name}",
        "district_caption": "📍 행정구: {district}",
        "feature_desc_label": "💡 **특징 소개**: {desc}",
        "food_fallback_desc": "【{name}】에 오신 것을 환영합니다! {district}에서 인기 있는 {type}로, 직접 방문해 정통 가오슝의 맛을 느껴보세요.",
        "attraction_fallback_desc": "【{name}】에 오신 것을 환영합니다! {district}을(를) 대표하는 {type}로, 시간을 내어 천천히 둘러볼 가치가 있습니다.",
        "guide_subheader": "AI 스마트 가이드 서비스",
        "transport_label": "이용할 교통수단을 선택하세요 (해당 주차 정보를 정확히 안내해 드립니다):",
        "transport_car": "🚗 자동차",
        "transport_scooter": "🛵 오토바이",
        "transport_bike": "🚲 YouBike ",
        "transport_mts": "🚊 지하철 ",
        "parking_result_label": "**【{mode}】주차 안내:** {info}",
        "quick_question_label": "**💡 빠른 질문 버튼:**",
        "chip_weather": "🌤️ 실시간 날씨",
        "chip_parking": "🅿️ 주차 정보",
        "chip_attraction": "🏛️ 인기 명소",
        "chip_coffee": "☕️ 추천 카페",
        "chat_input_placeholder": "가이드에게 질문하기 (예: 근처 주차하기 좋은 곳은?)",
    },
}


def t(key, **kwargs):
    """依目前語言取得翻譯文字，缺漏時自動 fallback 回繁體中文。"""
    text = TRANSLATIONS.get(LANG, TRANSLATIONS["zh"]).get(key)
    if text is None:
        text = TRANSLATIONS["zh"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


# ==========================================
# 0. 會員系統：登入 / 註冊 / 遊客 / 收藏
# ==========================================
USERS_FILE = Path(__file__).parent / "users.json"


def load_users():
    """讀取帳號資料（帳號、雜湊密碼、收藏清單）。"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(username, password):
    username = username.strip()
    if not username or not password:
        return False, "請輸入帳號與密碼。"
    users = load_users()
    if username in users:
        return False, "這個帳號已經被註冊過了，請直接登入或換一個帳號名稱。"
    users[username] = {"password": hash_password(password), "favorites": []}
    save_users(users)
    return True, "🎉 註冊成功！請切換到「登入」分頁輸入帳密。"


def verify_login(username, password):
    users = load_users()
    user = users.get(username.strip())
    if not user:
        return False
    return user["password"] == hash_password(password)


def _favorite_key(item):
    return f"{item.get('name')}|{item.get('address')}"


def get_favorites(username):
    users = load_users()
    return users.get(username, {}).get("favorites", [])


def is_favorited(username, item):
    return any(_favorite_key(f) == _favorite_key(item) for f in get_favorites(username))


def add_favorite(username, item, district, is_food):
    users = load_users()
    if username not in users:
        return
    favs = users[username].setdefault("favorites", [])
    if not any(_favorite_key(f) == _favorite_key(item) for f in favs):
        fav_entry = dict(item)
        fav_entry["district"] = district
        fav_entry["is_food"] = is_food
        favs.append(fav_entry)
        save_users(users)


def remove_favorite(username, item):
    users = load_users()
    if username not in users:
        return
    favs = users[username].get("favorites", [])
    users[username]["favorites"] = [f for f in favs if _favorite_key(f) != _favorite_key(item)]
    save_users(users)


if "auth_status" not in st.session_state:
    st.session_state["auth_status"] = None  # None＝尚未選擇；"guest"＝遊客；其他＝已登入帳號

# 尚未登入也未選擇遊客身分時，顯示登入頁面並中止後續內容
if st.session_state["auth_status"] is None:
    st.markdown(f'<div class="main-title">{t("login_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">{t("login_subtitle")}</div>', unsafe_allow_html=True)

    gate_col1, gate_col2, gate_col3 = st.columns([1, 1.4, 1])
    with gate_col2:
        login_tab, register_tab = st.tabs([t("tab_login"), t("tab_register")])

        with login_tab:
            login_user = st.text_input(t("field_account"), key="login_user_input", placeholder=t("field_account"))
            login_pw = st.text_input(t("field_password"), type="password", key="login_pw_input")
            if st.button(t("btn_login"), type="primary", use_container_width=True):
                if verify_login(login_user, login_pw):
                    st.session_state["auth_status"] = login_user.strip()
                    st.rerun()
                else:
                    st.error(t("err_login_fail"))

        with register_tab:
            reg_user = st.text_input(t("field_reg_account"), key="reg_user_input")
            reg_pw = st.text_input(t("field_reg_password"), type="password", key="reg_pw_input")
            if st.button(t("btn_register"), use_container_width=True):
                ok, msg = register_user(reg_user, reg_pw)
                if ok:
                    st.success(t("msg_register_success"))
                else:
                    err_map = {
                        "請輸入帳號與密碼。": t("msg_register_missing"),
                        "這個帳號已經被註冊過了，請直接登入或換一個帳號名稱。": t("msg_register_exists"),
                    }
                    st.error(err_map.get(msg, msg))

        st.divider()
        st.caption(t("guest_caption"))
        if st.button(t("guest_btn"), use_container_width=True):
            st.session_state["auth_status"] = "guest"
            st.rerun()

    st.stop()

CURRENT_USER = st.session_state["auth_status"]  # "guest" 或實際帳號名稱
IS_GUEST = CURRENT_USER == "guest"

if "current_item" not in st.session_state:
    st.info(t("home_hint"))


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

# ⚠️ 直接寫死在程式碼中的 Gemini API 金鑰（請直接把下面的字串換成你自己的金鑰）。
# 注意：這種寫法方便本機測試，但如果之後要把程式碼上傳到 GitHub 等公開地方，
# 記得把這組金鑰移除或改用 .streamlit/secrets.toml，避免金鑰外流。
GEMINI_API_KEY_HARDCODED = "AQ.Ab8RN6Kfl5o0ElHRScHLiM1jOwUed3NdDf3I8dqiGMzG1aLPGg"


def _get_gemini_api_key():
    """直接回傳寫死在程式碼中的 Gemini API 金鑰。"""
    return GEMINI_API_KEY_HARDCODED


def _is_valid_gemini_key_format(key):
    """粗略檢查金鑰『格式』是否像 Gemini API Key。

    Google 從 2026 年中起，Gemini API 金鑰改發新格式：
    - 舊版 Standard key：`AIzaSy` 開頭（即將於 2026/09 起停用）
    - 新版 Auth key：`AQ.` 開頭（目前 AI Studio 新申請的金鑰都是這個格式）
    兩種格式現在都是合法、可用的 Gemini API Key，只有 `ya29.`（Google 登入用的
    純 OAuth access token，不是 API Key）才視為明顯錯誤格式。
    """
    if not key or not isinstance(key, str):
        return False
    key = key.strip()
    if key.startswith("ya29."):
        return False
    return key.startswith("AIzaSy") or key.startswith("AQ.")


def _debug_api_key_status():
    """回傳除錯資訊字串，協助排查為什麼 Gemini API 金鑰無法使用。"""
    lines = []

    val = GEMINI_API_KEY_HARDCODED
    has_key = bool(val) and val != "請貼上你的 Gemini API 金鑰"
    lines.append(f"🔑 程式碼中{'✅ 已' if has_key else '❌ 尚未'}貼上實際的 GEMINI_API_KEY_HARDCODED 金鑰")

    if has_key:
        preview = f"{val[:6]}...{val[-4:]}" if val and len(val) > 12 else "(空值或太短)"
        lines.append(f"👀 讀到的金鑰開頭/結尾（僅供核對，非完整金鑰）：`{preview}`")
        if _is_valid_gemini_key_format(val):
            lines.append("✅ 格式檢查：這組金鑰格式看起來正確（`AIzaSy` 或 `AQ.` 開頭）。")
        else:
            lines.append(
                "❌ 格式檢查：這組金鑰**不是**以 `AIzaSy` 或 `AQ.` 開頭，看起來不是有效的 "
                "Gemini API Key（可能誤貼成 Google 帳號登入用的 OAuth token，通常是 "
                "`ya29.` 開頭）。請到 "
                "[Google AI Studio](https://aistudio.google.com/apikey) 重新產生正確的 API Key。"
            )
    else:
        lines.append(
            "請把程式碼最上方 `GEMINI_API_KEY_HARDCODED = \"AQ.Ab8RN6Kfl5o0ElHRScHLiM1jOwUed3NdDf3I8dqiGMzG1aLPGg\"` "
            "這一行的字串換成你在 Google AI Studio 產生的實際金鑰。"
        )

    return "\n\n".join(lines)


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


def _post_gemini(url, payload, api_key, max_retries=3, retry_wait_seconds=2):
    """呼叫 Gemini API：優先用 x-goog-api-key header，若遇到
    401 ACCESS_TOKEN_TYPE_UNSUPPORTED（金鑰被誤判成 OAuth token），
    自動改用官方文件另一種傳遞方式 `?key=` 網址參數重試。

    這個 401 錯誤目前已知在 Google 端具有間歇性（同一組金鑰有時候正常、
    有時候被拒絕），因此這裡會針對這個特定錯誤自動重試幾次，
    每次都是真實呼叫 Gemini API，不會使用任何內建/假資料。
    """
    last_resp = None
    for attempt in range(max_retries):
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=45)

        if resp.status_code == 401 and "ACCESS_TOKEN_TYPE_UNSUPPORTED" in resp.text:
            # header 方式被誤判成 OAuth token，改用 query string 方式再試一次
            resp = requests.post(
                url,
                params={"key": api_key},
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=45,
            )

        if resp.status_code == 200:
            return resp

        last_resp = resp
        # 只針對這個已知會間歇性發生的錯誤自動重試；其他錯誤（例如 404、額度用完）不重試
        is_intermittent_auth_error = (
            resp.status_code == 401 and "ACCESS_TOKEN_TYPE_UNSUPPORTED" in resp.text
        )
        if is_intermittent_auth_error and attempt < max_retries - 1:
            time.sleep(retry_wait_seconds)
            continue
        break

    return last_resp


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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        resp = _post_gemini(url, payload, api_key)

        if resp.status_code == 404:
            # 這個模型名稱已被 Google 下架/不存在，改試下一個備用模型
            last_error = RuntimeError(f"模型 {model_name} 已無法使用（404），改嘗試下一個備用模型...")
            continue
        if resp.status_code != 200:
            raise RuntimeError(
                f"Gemini API（{model_name}）回傳 HTTP {resp.status_code}"
                f"（已自動重試多次仍失敗）：{resp.text[:500]}"
            )

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
def generate_foods(district, api_key, lang="zh"):
    output_lang = LANG_NAMES_FOR_AI.get(lang, "繁體中文")
    prompt = f"""你是熟悉台灣高雄市在地美食文化的導覽專家。
請針對高雄市「{district}」，推薦 6 間該行政區內「真實存在」、具體且有名字的美食小吃店家（可包含小吃、餐廳、飲料、甜點等）。
重要規則（務必遵守）：
- name 必須是真實店家的具體名稱（例如「無老鍋」「一心鴨肉」這類真實可查的店名），絕對不可以用「{district}人氣OO店」「{district}特色XX店」這種套用行政區名稱、聽起來像範本／罐頭的空泛店名。
- 如果你對某個真實店名不確定完整正確性，仍請盡量給出最貼近你所知、實際存在過的具體店家名稱，而不是生成通用化的假名稱。
- 6 間店家的類型與風味應盡量多元、不要重複同一種類型。
請使用「{output_lang}」撰寫所有欄位內容（address 除外，address 一律保留繁體中文地址，方便對應台灣實際地圖），語氣生動、貼近觀光導覽文案風格。
每一間店家請提供以下欄位：
- name：真實店名（不可為範本化名稱，可用{output_lang}標示，但需讓人能對應到該店家）
- type：類型（例如「鴨肉飯/老字號小吃」，請用{output_lang}）
- address：地址（格式須為「高雄市{district}...」，一律使用繁體中文，請提供你所知最接近實際的地址）
- hours：營業時間（請用{output_lang}）
- desc：40～80字特色簡介（請用{output_lang}）。內容須聚焦在「這間店」本身：招牌菜色、風味特色、食材或烹調方式、在地人氣原因等，每間店的寫法都要不同，避免使用千篇一律的罐頭句子；可適度提及「{district}」在地飲食文化或街區氛圍作為背景，但主角是店家本身而非整個行政區。
- parking_car：汽車停車資訊建議（請用{output_lang}）
- parking_scooter：機車停車資訊建議（請用{output_lang}）
- parking_bike：YouBike 站點資訊建議（請用{output_lang}）
- transit：大眾運輸（捷運/輕軌/公車）前往方式建議（請用{output_lang}）
請直接輸出 JSON 陣列，不要加上任何其他文字或 Markdown 標記。"""
    return _call_gemini(prompt, FOOD_ITEM_SCHEMA, api_key)


@st.cache_data(ttl=3600, show_spinner="🤖 AI 正在為您搜尋熱門景點...")
def generate_attractions(zone, api_key, lang="zh"):
    output_lang = LANG_NAMES_FOR_AI.get(lang, "繁體中文")
    prompt = f"""你是熟悉台灣高雄市觀光景點的導覽專家。
請針對高雄市「{zone}」這個主題分區，推薦 5 個「真實存在」、具體且有名字的景點或文創商店。
重要規則（務必遵守）：
- name 必須是真實存在的具體景點名稱（例如「駁二藝術特區」「蓮池潭」這類真實可查的地名），絕對不可以用「{zone}文創園區」「{zone}觀景平台」這種套用主題分區名稱、聽起來像範本／罐頭的空泛地名。
- 如果你對某個真實地名不確定完整正確性，仍請盡量給出最貼近你所知、實際存在過的具體景點名稱，而不是生成通用化的假名稱。
- 5 個景點應盡量分散在高雄市內不同地點，不要重複同一個地方。
請使用「{output_lang}」撰寫所有欄位內容（address 除外，address 一律保留繁體中文地址，方便對應台灣實際地圖），語氣生動、貼近觀光導覽文案風格。
每一個景點請提供以下欄位：
- name：真實景點名稱（不可為範本化名稱，可用{output_lang}標示，但需讓人能對應到該景點）
- type：類型（例如「文創展覽」，請用{output_lang}）
- address：地址（須為「高雄市...」的完整地址，一律使用繁體中文，請提供你所知最接近實際的地址）
- hours：開放時間（請用{output_lang}）
- desc：40～80字特色簡介（請用{output_lang}）。內容須聚焦在「這個景點」本身：歷史背景、建築或自然特色、可以體驗的活動、值得造訪的理由等，每個景點的寫法都要不同，避免使用千篇一律的罐頭句子；可適度呼應「{zone}」這個主題分區的調性，但主角是景點本身，不要寫成美食介紹。
- transport：建議的大眾運輸前往方式（請用{output_lang}）
請直接輸出 JSON 陣列，不要加上任何其他文字或 Markdown 標記。"""
    return _call_gemini(prompt, ATTRACTION_ITEM_SCHEMA, api_key)


def get_items(is_food, key):
    """依照分類與地區/主題，取得（快取的）Gemini 即時生成清單。

    只使用即時 Gemini 資料，不使用任何內建／備用資料。
    會依目前選擇的語言（LANG）生成對應語言的內容，並個別快取。
    若 Gemini API 失敗，回傳空清單，由呼叫端顯示錯誤訊息。
    """
    api_key = _get_gemini_api_key()
    if not api_key:
        st.session_state["gemini_error"] = "尚未設定 Gemini API 金鑰。"
        return []
    try:
        if is_food:
            return generate_foods(key, api_key, LANG)
        else:
            return generate_attractions(key, api_key, LANG)
    except Exception as e:
        st.session_state["gemini_error"] = str(e)
        return []


_GEMINI_KEY_RAW = _get_gemini_api_key()

if not _GEMINI_KEY_RAW or _GEMINI_KEY_RAW == "請貼上你的 Gemini API 金鑰":
    st.error(
        "⚠️ 尚未設定 Gemini API 金鑰，無法載入即時資料。\n\n"
        "請打開程式碼，找到最上方這一行，把它換成你自己的金鑰：\n\n"
        "```python\nGEMINI_API_KEY_HARDCODED = \"請貼上你的 Gemini API 金鑰\"\n```\n\n"
        "金鑰請到 https://aistudio.google.com/apikey 產生"
        "（目前 AI Studio 新產生的金鑰是 `AQ.` 開頭，是正常的新版格式；"
        "舊版 `AIzaSy` 開頭的金鑰也還能用，但即將於 2026 年 9 月停用）。"
    )
    with st.expander("🔧 疑難排解：點我看詳細除錯資訊（截圖這裡給人看最準）", expanded=True):
        st.markdown(_debug_api_key_status())
    st.stop()

if not _is_valid_gemini_key_format(_GEMINI_KEY_RAW):
    st.error(
        "⚠️ 目前設定的 GEMINI_API_KEY_HARDCODED **格式不正確**，不是有效的 Gemini API 金鑰，"
        "無法載入即時資料。\n\n"
        "常見原因：誤貼成 Google 帳號的 OAuth 登入權杖（通常是 `ya29.` 開頭），"
        "這種權杖無法用來呼叫 Gemini API。\n\n"
        "請改用以下步驟取得正確金鑰：\n\n"
        "1. 前往 https://aistudio.google.com/apikey\n"
        "2. 點「Create API key」產生一組金鑰（`AQ.` 或 `AIzaSy` 開頭皆可）\n"
        "3. 回到程式碼最上方，更新：\n\n"
        "```python\nGEMINI_API_KEY_HARDCODED = \"你剛剛產生的金鑰\"\n```"
    )
    with st.expander("🔧 疑難排解：點我看詳細除錯資訊（截圖這裡給人看最準）", expanded=True):
        st.markdown(_debug_api_key_status())
    st.stop()

# ==========================================
# 4. 側邊欄控制區
# ==========================================
with st.sidebar:

    if IS_GUEST:
        st.info(t("sidebar_guest_info"))
        if st.button(t("sidebar_login_btn"), use_container_width=True):
            st.session_state["auth_status"] = None
            st.rerun()
    else:
        st.success(t("sidebar_welcome", user=CURRENT_USER))
        if st.button(t("sidebar_logout"), use_container_width=True):
            st.session_state["auth_status"] = None
            st.rerun()

        my_favorites = get_favorites(CURRENT_USER)
        with st.expander(t("sidebar_fav_header", count=len(my_favorites)), expanded=False):
            if not my_favorites:
                st.caption(t("sidebar_fav_empty"))
            else:
                for fav in my_favorites:
                    fav_col1, fav_col2 = st.columns([4, 1])
                    with fav_col1:
                        if st.button(
                            f"📍 {fav['name']}",
                            key=f"goto_fav_{_favorite_key(fav)}",
                            use_container_width=True,
                        ):
                            st.session_state["current_item"] = fav
                            st.session_state["current_district"] = fav.get("district", "高雄市")
                            st.session_state["current_is_food"] = fav.get("is_food", True)
                            st.session_state["chat_history"] = []
                            st.rerun()
                    with fav_col2:
                        if st.button("🗑️", key=f"del_fav_{_favorite_key(fav)}"):
                            remove_favorite(CURRENT_USER, fav)
                            st.rerun()

    st.divider()

    st.header(t("sidebar_category_header"))
    category = st.radio(
        "選擇類別",
        [t("category_food"), t("category_attraction")],
        label_visibility="collapsed"
    )

    is_food = "美食" in category or "Food" in category or "グルメ" in category or "맛집" in category
    district_options = KAOHSIUNG_DISTRICTS if is_food else KAOHSIUNG_ATTRACTION_ZONES
    selected_district = st.selectbox(t("sidebar_district_label"), district_options)

    with st.expander(t("expander_preview_label"), expanded=False):
        preview_key = f"preview_{'food' if is_food else 'attr'}_{selected_district}_{LANG}"
        if st.button(t("preview_load_btn"), key=f"btn_{preview_key}", use_container_width=True):
            st.session_state[preview_key] = get_items(is_food, selected_district)

        preview_items = st.session_state.get(preview_key)
        if preview_items:
            for item in preview_items:
                st.markdown(f"- **{item['name']}** ({item['type']})")
        elif preview_items is not None:
            st.caption(t("preview_no_data"))
        else:
            st.caption(t("preview_hint"))

    st.divider()

    generate_btn = st.button(t("generate_btn"), type="primary", use_container_width=True)

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

    is_food_now = st.session_state.get("current_is_food", is_food)

    btn_col1, btn_col2, btn_col3, btn_col4, _ = st.columns([1.3, 1.3, 1.3, 1.6, 3.9])

    with btn_col1:
        if st.button(t("btn_home"), type="secondary", use_container_width=True):
            st.session_state.pop("current_item", None)
            st.session_state.pop("current_district", None)
            st.session_state.pop("chat_history", None)
            st.rerun()

    with btn_col2:
        if st.button(t("btn_shuffle"), type="secondary", use_container_width=True):
            is_food_now = st.session_state.get("current_is_food", is_food)
            candidates = get_items(is_food_now, selected_district)
            next_item = pick_next_item(candidates, st.session_state.get("current_item"))
            if next_item is None:
                err_detail = st.session_state.get("gemini_error", "未知錯誤（可能是 API 額度用完或回傳格式異常）")
                st.error(f"⚠️ 這次無法取得新的推薦，請稍後再試一次。\n\n錯誤詳情：{err_detail}")
            else:
                st.session_state["current_item"] = next_item
                st.session_state["current_district"] = selected_district
                st.session_state["current_is_food"] = is_food_now
                st.session_state["chat_history"] = []
                st.rerun()

    with btn_col3:
        @st.dialog(t("share_dialog_title"))
        def share_dialog():
            share_text = t("share_text_template", name=item['name'], type=item['type'], address=item['address'], url=maps_url)
            line_url = f"https://line.me/R/msg/text/?{urllib.parse.quote(share_text)}"

            st.write(t("share_write", name=item['name']))
            st.code(share_text, language=None)

            st.markdown(
                f'<a href="{line_url}" target="_blank" class="line-share-btn">{t("share_line_btn")}</a>',
                unsafe_allow_html=True,
            )

        if st.button(t("btn_share"), type="secondary", use_container_width=True):
            share_dialog()

    with btn_col4:
        # 收藏功能：僅登入帳號可用，遊客顯示停用按鈕提示
        if IS_GUEST:
            st.button(t("fav_locked_btn"), type="secondary", use_container_width=True, disabled=True)
        else:
            already_fav = is_favorited(CURRENT_USER, item)
            fav_label = t("fav_remove_btn") if already_fav else t("fav_add_btn")
            if st.button(fav_label, key=f"fav_toggle_{_favorite_key(item)}", type="secondary", use_container_width=True):
                if already_fav:
                    remove_favorite(CURRENT_USER, item)
                    st.toast(t("fav_toast_remove", name=item['name']))
                else:
                    add_favorite(CURRENT_USER, item, district, is_food_now)
                    st.toast(t("fav_toast_add", name=item['name']))
                st.rerun()

if st.session_state.get("current_item"):
    item = st.session_state["current_item"]
    district = st.session_state.get("current_district", "高雄市")

    col1, col2 = st.columns([1, 1])

    with col1:
        components.iframe(embed_url, height=350, scrolling=False)
        
        st.markdown(f"""
        <div class="merchant-card">
            <h4>{t("detail_header")}</h4>
            <b>{t("detail_name_label")}</b> <span>{item['name']} ({item['type']})</span><br>
            <b>{t("detail_address_label")}</b> <span>{item['address']}</span><br>
            <b>{t("detail_hours_label")}</b> <span>{item.get('hours', t("hours_fallback"))}</span><br>
            <a href="{maps_url}" target="_blank" class="map-btn">{t("detail_map_btn")}</a>
        </div>
        """, unsafe_allow_html=True)
        st.caption(t("detail_caption"))

    with col2:
        # 僅在此處加上 margin-top 修正，向上拉平對齊左側的 caption
        st.markdown(f"<h3 style='margin-top: -12px; margin-bottom: 4px; font-weight: bold;'>{t('explore_target', name=item['name'])}</h3>", unsafe_allow_html=True)
        st.caption(t("district_caption", district=district))
        
        # 動態取得 item['desc']，如果沒有介紹則依美食／景點分別顯示不同的備用預設文字
        is_food_now = st.session_state.get("current_is_food", is_food)
        if is_food_now:
            fallback_desc = t("food_fallback_desc", name=item['name'], district=district, type=item.get('type', '美食小吃'))
        else:
            fallback_desc = t("attraction_fallback_desc", name=item['name'], district=district, type=item.get('type', '景點'))
        item_desc = item.get('desc') or fallback_desc
        st.info(t("feature_desc_label", desc=item_desc))

        st.divider()
        st.subheader(t("guide_subheader"))
        
        transport_mode = st.selectbox(
            t("transport_label"),
            [t("transport_car"), t("transport_scooter"), t("transport_bike"), t("transport_mts")],
            index=0
        )

        specific_parking = get_parking_info_by_mode(item, transport_mode)
        st.success(t("parking_result_label", mode=transport_mode, info=specific_parking))

        st.markdown(t("quick_question_label"))
        chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
        preset_input = None

        if chip_col1.button(t("chip_weather"), use_container_width=True):
            preset_input = f"請問【{district}】現在的天氣和氣溫如何？"
        if chip_col2.button(t("chip_parking"), use_container_width=True):
            preset_input = f"請問以【{item['name']}】為中心，駕駛/騎乘【{transport_mode}】過來，最方便的專屬停車地點在哪裡？"
        if chip_col3.button(t("chip_attraction"), use_container_width=True):
            preset_input = f"請問【{item['name']}】附近有哪些推薦的熱門景點？"
        if chip_col4.button(t("chip_coffee"), use_container_width=True):
            preset_input = f"請問【{item['name']}】附近有哪些適合休息的氣氛咖啡廳？"

        user_input = st.chat_input(t("chat_input_placeholder")) or preset_input or ""

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
    st.markdown(f'<div class="main-title">{t("home_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">{t("home_subtitle")}</div>', unsafe_allow_html=True)

    st.subheader(t("home_step_header"))
    step_col1, step_col2, step_col3 = st.columns(3)
  
    with step_col1:
        st.markdown(t("home_step1"))
    with step_col2:
        st.markdown(t("home_step2"))
    with step_col3:
        st.markdown(t("home_step3"))

    st.divider()

    st.subheader(t("home_quick_header"))
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    if quick_col1.button(t("quick1"), use_container_width=True):
        items = get_items(False, "港灣與文創區")
        if items:
            st.session_state["current_item"] = items[0]
            st.session_state["current_district"] = "港灣與文創區"
            st.session_state["current_is_food"] = False
            st.session_state["chat_history"] = []
            st.rerun()

    if quick_col2.button(t("quick2"), use_container_width=True):
        items = get_items(True, "鹽埕區")
        if items:
            st.session_state["current_item"] = items[0]
            st.session_state["current_district"] = "鹽埕區"
            st.session_state["current_is_food"] = True
            st.session_state["chat_history"] = []
            st.rerun()

    if quick_col3.button(t("quick3"), use_container_width=True):
        items = get_items(False, "自然景觀與園區")
        if items:
            st.session_state["current_item"] = items[0]
            st.session_state["current_district"] = "左營區"
            st.session_state["current_is_food"] = False
            st.session_state["chat_history"] = []
            st.rerun()

    if quick_col4.button(t("quick4"), use_container_width=True):
        items = get_items(True, "鹽埕區")
        if items:
            idx = 1 if len(items) > 1 else 0
            st.session_state["current_item"] = items[idx]
            st.session_state["current_district"] = "鹽埕區"
            st.session_state["current_is_food"] = True
            st.session_state["chat_history"] = []
            st.rerun()