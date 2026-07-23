import streamlit as st
import json
import random
import urllib.parse
from openai import OpenAI
import streamlit.components.v1 as components
import os
import streamlit as st
import urllib.parse
import urllib.request
import json

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


KAOHSIUNG_FOODS = {
    "鹽埕區": [
        {
            "name": "鴨肉珍", 
            "type": "鴨肉飯/老字號小吃", 
            "address": "高雄市鹽埕區五福四路258號", 
            "hours": "10:00–20:20 (週二公休)",
            "desc": "鹽埕區極具代表性的老字號！必點鮮嫩多汁的切盤鴨肉與淋上濃郁肉燥的鴨肉飯，再配上一碗當歸鴨血湯，古早味十足。",
            "parking_car": "五福四路公有收費停車場、鹽埕立體停車場、大勇路平面停車場",
            "parking_scooter": "五福四路兩側路邊機車停車格、大勇路劃線機車位",
            "parking_bike": "YouBike 2.0 捷運鹽埕埔站（1號出口）站",
            "transit": "捷運鹽埕埔站 1 號出口步行約 5 分鐘"
        },
        {
            "name": "樺達奶茶總店", 
            "type": "經典港藝奶茶", 
            "address": "高雄市鹽埕區新樂街99號", 
            "hours": "09:00–22:00",
            "desc": "高雄奶茶界的開山始祖！堅持不加冰塊並搭配光泉鮮乳，濃郁茶香與奶香的和諧比例，是走訪新樂街奶茶一條街絕不可錯過的經典。",
            "parking_car": "大勇路平面停車場、鹽埕埔捷運站轉乘停車場（新樂街巷窄不建議汽車駛入）",
            "parking_scooter": "新樂街與大勇路口劃線機車格",
            "parking_bike": "YouBike 2.0 捷運鹽埕埔站（2號出口）站",
            "transit": "捷運鹽埕埔站 2 號出口步行約 3 分鐘"
        },
        {
            "name": "阿財雞絲麵", 
            "type": "手工雞絲麵/黑白切", 
            "address": "高雄市鹽埕區壽星街11號", 
            "hours": "12:00–23:00 (週日公休)",
            "desc": "巷弄隱藏版的古早味小吃！自家手工製作的雞絲麵香氣十足，搭配清甜湯頭與黑白切太監雞、太監鴨，充滿濃濃古意人情味。",
            "parking_car": "七賢三路路邊收費停車格、鹽埕立體停車場",
            "parking_scooter": "壽星街與七賢三路劃線機車位",
            "parking_bike": "YouBike 2.0 鹽埕國小站",
            "transit": "捷運鹽埕埔站 2 號出口步行約 8 分鐘"
        },
        {
            "name": "港園牛肉麵", 
            "type": "半世紀牛肉拌麵", 
            "address": "高雄市鹽埕區大成街55號", 
            "hours": "10:30–20:00",
            "desc": "傳承超過半世紀的牛肉麵名店！豬油拌香的乾拌麵搭配軟嫩入味的厚切牛肉塊，再加點蒜泥與豬油更是老饕指定的經典吃法。",
            "parking_car": "公園二路公有收費停車場、真愛碼頭平面停車場",
            "parking_scooter": "公園二路與大成街口劃線機車格",
            "parking_bike": "YouBike 2.0 五福大成街口站",
            "transit": "捷運鹽埕埔站 4 號出口步行約 7 分鐘"
        },
        {
            "name": "北港蔡三代筒仔米糕", 
            "type": "米糕/蒸蛋湯", 
            "address": "高雄市鹽埕區河西路167號", 
            "hours": "13:30–21:30 (週三公休)",
            "desc": "飄香數十年的愛河畔古早味！粒粒分明蒸得入味的糯米飯，淋上特製肉燥，再配上一碗全台獨創的蒸蛋湯，在地人大推的黃金組合。",
            "parking_car": "愛河河西路沿線公有收費停車格",
            "parking_scooter": "河西路與興華街口劃線機車位",
            "parking_bike": "YouBike 2.0 愛河河西路站",
            "transit": "捷運鹽埕埔站 2 號出口步行約 7 分鐘"
        },
        {
            "name": "汕頭天天沙茶火鍋", 
            "type": "手工沙茶牛肉鍋", 
            "address": "高雄市鹽埕區七賢三路240號", 
            "hours": "11:30–14:00, 17:00–23:30 (週四公休)",
            "desc": "主打手作溫體牛肉與獨門香濃花生沙茶醬！湯頭鮮甜回甘，搭配新鮮蔬菜與炸扁魚底蘊，是鹽埕區極具代表性的老字號沙茶鍋。",
            "parking_car": "七賢三路路邊收費停車格、鹽埕立體停車場",
            "parking_scooter": "七賢三路兩側劃線機車格",
            "parking_bike": "YouBike 2.0 鹽埕國小站",
            "transit": "捷運鹽埕埔站 2 號出口步行約 8 分鐘"
        },
        {
            "name": "阿英排骨飯", 
            "type": "古早味炸排骨飯", 
            "address": "高雄市鹽埕區富野路79-2號", 
            "hours": "10:30–13:45, 17:00–19:45 (週四公休)",
            "desc": "鹽埕區無人不知的人氣便當老店！現點現炸的古早味醃製排骨，外酥內嫩又多汁，搭配古早味酸菜與滷汁，超級下飯。",
            "parking_car": "富野路路邊停車格、建國四路收費停車場",
            "parking_scooter": "富野路劃線機車格",
            "parking_bike": "YouBike 2.0 鹽埕國小站",
            "transit": "捷運鹽埕埔站 2 號出口步行約 6 分鐘"
        }
    ],
    "鼓山區": [
        {
            "name": "渡船頭海之冰", 
            "type": "大碗公水果冰", 
            "address": "高雄市鼓山區濱海一路76號", 
            "hours": "11:00–23:00 (週一公休)",
            "desc": "大碗公冰的始祖！提供多種倍數份量的高雄冰品代表，滿滿的水果與滿牆的學生留言塗鴉，是前往旗津渡船頭前的青春回憶。",
            "parking_car": "鼓山一路停三停車場、西子灣遊客中心收費停車場",
            "parking_scooter": "鼓山渡船頭專用機車停車區、濱海一路機車格",
            "parking_bike": "YouBike 2.0 捷運西子灣站（1號出口）站",
            "transit": "捷運西子灣站 1 號出口步行約 6 分鐘"
        },
        {
            "name": "阿雪花生糖/古早味冰品", 
            "type": "古早味花生糖/刨冰", 
            "address": "高雄市鼓山區延平街61號", 
            "hours": "11:00–20:00",
            "desc": "哈瑪星在地古早味！手工現做香濃不黏牙的花生糖與傳統刨冰，用料紮實且甜而不膩，深受在地居民與中山大學學生喜愛。",
            "parking_car": "濱海二路收費停車場",
            "parking_scooter": "延平街口劃線機車格",
            "parking_bike": "YouBike 2.0 捷運西子灣站",
            "transit": "捷運西子灣站 1 號出口步行約 4 分鐘"
        },
        {
            "name": "萬全肉圓", 
            "type": "清蒸肉圓/米粉湯", 
            "address": "高雄市鼓山區臨海一路1號", 
            "hours": "06:30–17:30 (週四公休)",
            "desc": "飄香西子灣五十年的清蒸肉圓名店！外皮 Q 彈滑嫩，內餡肉質紮實香氣濃郁，再淋上特製甘甜醬汁，配上一碗大腸米粉湯非常滿足。",
            "parking_car": "臨海一路路邊收費停車格",
            "parking_scooter": "臨海一路與臨海二路口機車格",
            "parking_bike": "YouBike 2.0 捷運西子灣站",
            "transit": "捷運西子灣站 1 號出口步行約 2 分鐘"
        },
        {
            "name": "鼓山大溝頂黑輪", 
            "type": "台式關東煮/烤黑輪", 
            "address": "高雄市鼓山區河川街76號", 
            "hours": "11:00–18:00 (週二公休)",
            "desc": "隱藏在大溝頂舊鐵道旁的台式關東煮小攤！提供炭烤香腸、烤黑輪片與現煮熱湯，價格親民實惠，帶有濃濃的老高雄懷舊氛圍。",
            "parking_car": "河川街路邊停車格",
            "parking_scooter": "店家門口機車停放區",
            "parking_bike": "YouBike 2.0 輕軌文武聖殿站",
            "transit": "輕軌文武聖殿站步行約 5 分鐘"
        }
    ],
    "左營區": [
        {
            "name": "寬來順早餐店", 
            "type": "果貿眷村傳統早餐", 
            "address": "高雄市左營區中華一路5-14號", 
            "hours": "04:00–12:00 (週一公休)",
            "desc": "果貿社區內超人氣排隊早餐！現烤酥脆燒餅夾油條、多汁飽滿的小籠包與酸辣鹹豆漿，用最道地的眷村美味開啟一天。",
            "parking_car": "果貿社區圓環內公有路邊收費停車格",
            "parking_scooter": "果貿社區圓環內劃線機車停車格",
            "parking_bike": "YouBike 2.0 果貿社區站",
            "transit": "建議搭乘紅35/218號公車至『果貿社區站』"
        },
        {
            "name": "劉家酸菜白肉鍋", 
            "type": "正宗眷村酸菜白肉鍋", 
            "address": "高雄市左營區介壽路9號", 
            "hours": "11:00–22:30",
            "desc": "左營軍港旁享負盛名的眷村火鍋！使用傳統酸菜自然發酵的酸爽湯頭，搭配帶皮五花豬肉與現做蔥油餅、刀削麵，聚餐首選。",
            "parking_car": "中興堂前專屬大型收費停車場",
            "parking_scooter": "中興堂廣場機車停車區",
            "parking_bike": "YouBike 2.0 介壽路口站",
            "transit": "台鐵左營舊城站轉乘計程車約 5 分鐘"
        },
        {
            "name": "三牛牛肉麵", 
            "type": "大份量奔牛麵/牛肉麵", 
            "address": "高雄市左營區勝利路85號", 
            "hours": "11:00–20:30",
            "desc": "蓮池潭風景區旁的名店！主打超大塊厚實牛肉與大份量麵條，清燉與紅燒湯頭皆十分濃郁，小菜選擇極為豐富。",
            "parking_car": "勝利路公有收費停車場、蓮池潭旅遊服務中心停車場",
            "parking_scooter": "店家門口及勝利路路邊機車位",
            "parking_bike": "YouBike 2.0 蓮池潭（勝利路）站",
            "transit": "台鐵左營舊城站步行約 10 分鐘"
        },
        {
            "name": "正宗鴨肉飯", 
            "type": "裕誠路鴨肉飯/當歸鴨", 
            "address": "高雄市左營區裕誠路245號", 
            "hours": "11:00–21:00 (週五公休)",
            "desc": "榮獲多項美食推薦的人氣小吃！切片鴨肉鮮嫩多汁，鋪滿在淋上香噴噴鴨油的白飯上，再配上一碗溫補當歸鴨湯極為過癮。",
            "parking_car": "聯上停二收費停車場、河堤路路邊收費停車格",
            "parking_scooter": "裕誠路與富民路劃線機車格",
            "parking_bike": "YouBike 2.0 捷運巨蛋站（2號出口）站",
            "transit": "捷運巨蛋站 2 號出口步行約 6 分鐘"
        },
        {
            "name": "西安麵食館", 
            "type": "陝西皮帶麵/西域麵食", 
            "address": "高雄市左營區勝利路115-1號", 
            "hours": "10:30–20:00 (週三公休)",
            "desc": "主打超寬道地的陝西皮帶麵與蓋世牛肉麵！麵條 Q 彈有勁道，搭配香辣帶勁的清燉或紅燒湯頭，展現獨特的西域風采。",
            "parking_car": "蓮池潭公有收費停車場",
            "parking_scooter": "勝利路劃線機車格",
            "parking_bike": "YouBike 2.0 蓮池潭站",
            "transit": "台鐵左營舊城站步行約 8 分鐘"
        },
        {
            "name": "吉品高雄鹹酥雞", 
            "type": "蒜香鹹酥雞/深夜炸物", 
            "address": "高雄市左營區富民路351號", 
            "hours": "16:00–00:30",
            "desc": "裕誠商圈周邊的高人氣宵夜選擇！炸物酥脆不油膩，招牌無骨鹽酥雞與香脆三角骨配上九層塔與蒜片，刷上特製醬汁非常涮嘴。",
            "parking_car": "富民路路邊停車格、安吉街收費停車場",
            "parking_scooter": "富民路機車位",
            "parking_bike": "YouBike 2.0 捷運巨蛋站",
            "transit": "捷運巨蛋站 2 號出口步行約 4 分鐘"
        },
        {
            "name": "金獅湖菜鹹湯圓", 
            "type": "客家鹹湯圓/古早味", 
            "address": "高雄市左營區辛亥路201號", 
            "hours": "10:00–19:30",
            "desc": "傳承多年的客家傳統鹹湯圓！手作純米外皮 Q 軟厚實，包裹鹹香鮮美肉餡，搭配茼蒿與紅蔥頭湯頭，充滿溫暖的家鄉味。",
            "parking_car": "辛亥路沿線收費停車格",
            "parking_scooter": "辛亥路劃線機車格",
            "parking_bike": "YouBike 2.0 辛亥裕誠路口站",
            "transit": "捷運巨蛋站步行約 10 分鐘"
        }
    ],
    "楠梓區": [
        {
            "name": "楊寶寶蒸餃總店", 
            "type": "平價湯包/牛肉捲餅", 
            "address": "高雄市楠梓區朝明路106號", 
            "hours": "11:00–01:00",
            "desc": "被譽為北高雄平價版鼎泰豐！現包現蒸的豬肉與牛肉蒸餃皮薄餡多、湯汁滿溢，還有金黃酥脆的牛肉捲餅，是楠梓超強排隊名店。",
            "parking_car": "朝明路特約收費停車場、楠梓車站前公有停車場",
            "parking_scooter": "店家門口及朝明路兩側機車格",
            "parking_bike": "YouBike 2.0 楠梓火車站",
            "transit": "台鐵楠梓火車站步行約 6 分鐘"
        },
        {
            "name": "桂林酥脆肉圓", 
            "type": "低溫油炸酥皮肉圓", 
            "address": "高雄市楠梓區桂林街58號", 
            "hours": "10:30–18:00 (週日公休)",
            "desc": "獨特的低溫油炸酥皮肉圓！外皮炸至金黃酥脆爽口、內餡筍丁與肉塊紮實，淋上店家特調甜辣醬，口感極具層次。",
            "parking_car": "楠梓火車站周邊路邊停車格",
            "parking_scooter": "桂林街路邊劃線機車格",
            "parking_bike": "YouBike 2.0 楠梓火車站",
            "transit": "台鐵楠梓火車站步行約 5 分鐘"
        },
        {
            "name": "右昌肉圓", 
            "type": "右昌清蒸肉圓/四神湯", 
            "address": "高雄市楠梓區右昌街261號", 
            "hours": "06:00–17:00",
            "desc": "右昌在地飄香多年的清蒸肉圓！外皮軟 Q 清爽不油膩，搭配特製肉餡與甘甜醬汁，銅板價格是在地人最愛的台式下午點心。",
            "parking_car": "右昌街路邊停車格",
            "parking_scooter": "右昌街兩側劃線機車格",
            "parking_bike": "YouBike 2.0 右昌森林公園站",
            "transit": "捷運油廠國小站轉乘公車約 5 分鐘"
        },
        {
            "name": "楠梓坑鴨肉飯", 
            "type": "楠梓舊街鴨肉飯/當歸湯", 
            "address": "高雄市楠梓區楠梓路212號", 
            "hours": "10:30–20:00 (週日公休)",
            "desc": "楠梓舊街傳統古早味鴨肉專賣！鴨肉去骨軟嫩，鴨油飯香氣四溢令人垂涎三尺，配上一碗當歸鴨血湯更是不可錯過的懷舊滋味。",
            "parking_car": "楠梓路公有停車格",
            "parking_scooter": "店家門口劃線機車格",
            "parking_bike": "YouBike 2.0 楠梓國小站",
            "transit": "台鐵楠梓火車站步行約 8 分鐘"
        },
        {
            "name": "港都金棧黑輪", 
            "type": "炭烤黑輪/關東煮", 
            "address": "高雄市楠梓區後昌路801號", 
            "hours": "15:00–22:30 (週二公休)",
            "desc": "後勁/後昌路一帶的人氣下午茶與宵夜！現烤香酥黑輪片外酥內 Q，配上熱騰騰的免費關東煮高湯，價格十分平易近人。",
            "parking_car": "後昌路路邊公有停車格",
            "parking_scooter": "店家門口機車位",
            "parking_bike": "YouBike 2.0 捷運油廠國小站",
            "transit": "捷運油廠國小站 1 號出口步行約 6 分鐘"
        },
        {
            "name": "楠梓羊肉羹", 
            "type": "蒜香羊肉羹/炒麵", 
            "address": "高雄市楠梓區楠梓新路190號", 
            "hours": "11:00–21:00 (週日公休)",
            "desc": "楠梓火車站周邊老字號小吃！勾芡適中的羹湯帶有獨特蒜香與柴魚香，羊肉鮮嫩無腥味，加點九層塔與烏醋提味更是絕配。",
            "parking_car": "楠梓火車站前公有停車場",
            "parking_scooter": "楠梓新路劃線機車格",
            "parking_bike": "YouBike 2.0 楠梓火車站",
            "transit": "台鐵楠梓火車站步行約 3 分鐘"
        }
    ],
    "三民區": [
        {
            "name": "廖家黑輪", 
            "type": "三民市場炭烤黑輪/關東煮", 
            "address": "高雄市三民區三民街191號", 
            "hours": "10:30–21:30",
            "desc": "三民市場內紅翻天的炭烤黑輪攤！使用手工魚漿製作，現烤至微微焦香再刷上甜鹹特製醬汁，外酥內 Q，配關東煮湯超級過癮。",
            "parking_car": "中華三路平面收費停車場、河北二路路邊停車格",
            "parking_scooter": "中華三路或自強一路口機車格",
            "parking_bike": "YouBike 2.0 三民市場站",
            "transit": "高雄車站轉乘公車或步行約 12 分鐘"
        },
        {
            "name": "鴨肉和", 
            "type": "建國路鴨肉飯/當歸鴨", 
            "address": "高雄市三民區建國三路395-1號", 
            "hours": "10:30–20:30 (週一公休)",
            "desc": "建國路上傳承數十年的古早味鴨肉店！招牌鴨肉飯淋上香濃鴨油與切塊鴨肉，肉質滑嫩甘甜，搭配當歸鴨湯是高雄老饕的最愛。",
            "parking_car": "建國三路路邊公有收費停車格",
            "parking_scooter": "店家門口及建國三路劃線機車格",
            "parking_bike": "YouBike 2.0 三民區公所站",
            "transit": "捷運市議會站步行約 10 分鐘"
        },
        {
            "name": "黃家古早味八寶冰", 
            "type": "古早味刨冰/手工八寶冰", 
            "address": "高雄市三民區三民街152號", 
            "hours": "11:00–23:00",
            "desc": "三民市場極具代表性的老字號冰品店！豐富配料如芋頭、紅豆、湯圓等皆為每日手作熬煮，黑糖香氣濃郁消暑，甜而不膩。",
            "parking_car": "中華三路平面停車場、河北二路停車格",
            "parking_scooter": "三民街口劃線機車格",
            "parking_bike": "YouBike 2.0 三民市場站",
            "transit": "高雄車站步行約 12 分鐘"
        },
        {
            "name": "侯記蒸餃肉圓", 
            "type": "現蒸薄皮蒸餃/清蒸肉圓", 
            "address": "高雄市三民區自強一路238號", 
            "hours": "10:00–20:00",
            "desc": "自強路上熱門的傳統麵食小吃！現蒸薄皮蒸餃內餡鮮美多汁，搭配清蒸軟 Q 肉圓與酸辣湯，每一口都能感受到真材實料。",
            "parking_car": "河北二路與自強路口停車場",
            "parking_scooter": "自強一路劃線機車格",
            "parking_bike": "YouBike 2.0 三民市場站",
            "transit": "捷運市議會站步行約 9 分鐘"
        },
        {
            "name": "澎湖陳情感燒麻糬", 
            "type": "熱燒麻糬/花生芝麻粉", 
            "address": "高雄市三民區三民街122號", 
            "hours": "12:30–23:00",
            "desc": "熱騰騰滾水中浮起的 Q 彈燒麻糬！沾上厚厚一層花生粉或芝麻粉，香甜軟糯不黏牙，冬夏皆宜的台式傳統甜點經典。",
            "parking_car": "中華三路平面收費停車場",
            "parking_scooter": "三民街口劃線機車格",
            "parking_bike": "YouBike 2.0 三民市場站",
            "transit": "高雄車站步行約 11 分鐘"
        },
        {
            "name": "老周冷熱飲", 
            "type": "燒麻糬八寶冰/冷熱飲", 
            "address": "高雄市三民區三民街126號", 
            "hours": "10:00–00:00",
            "desc": "三民市場內近百年的冷熱飲老店！招牌燒麻糬搭配刨冰、八寶冰與米糕粥，一口冰一口熱麻糬的「冷熱交替」吃法最為著名。",
            "parking_car": "河北二路路邊停車格",
            "parking_scooter": "三民街周邊機車位",
            "parking_bike": "YouBike 2.0 三民市場站",
            "transit": "高雄車站步行約 11 分鐘"
        }
    ],
    "新興區": [
        {
            "name": "老江紅茶牛奶總店", 
            "type": "24h紅茶牛奶/火腿蛋吐司", 
            "address": "高雄市新興區南台路51號", 
            "hours": "24 小時營業",
            "desc": "高雄跨時代的 24 小時傳奇美食！經典紅茶牛奶採用古法高山紅茶搭配純鮮乳，配上一份半熟火腿蛋吐司，是深夜不二首選。",
            "parking_car": "美麗島捷運站轉乘停車場、中正四路路邊收費停車格",
            "parking_scooter": "南台路與中正路口劃線機車位",
            "parking_bike": "YouBike 2.0 捷運美麗島站（1號出口）站",
            "transit": "捷運美麗島站 1 號出口步行約 2 分鐘"
        },
        {
            "name": "汕頭泉成沙茶火鍋", 
            "type": "八十年秘製沙茶火鍋", 
            "address": "高雄市新興區中山一路176號", 
            "hours": "11:00–01:00",
            "desc": "創立於 1943 年的高雄火鍋指標！獨門秘製扁魚湯頭香氣四溢，特製沙茶醬沾上鮮嫩溫體牛肉，連許多名人明星都親自造訪。",
            "parking_car": "美麗島站地下收費停車場、中正三路收費停車格",
            "parking_scooter": "中山一路與中正路口劃線機車格",
            "parking_bike": "YouBike 2.0 捷運美麗島站（1號出口）站",
            "transit": "捷運美麗島站 1 號出口步行約 1 分鐘"
        },
        {
            "name": "大圓環雞肉飯", 
            "type": "美麗島站古早味雞肉飯", 
            "address": "高雄市新興區中山一路1號", 
            "hours": "10:00–19:00 (週三公休)",
            "desc": "美麗島站 1 號出口旁的老牌雞肉飯！撕成絲狀的雞肉口感嫩軟，淋上香噴噴古早味雞油與醬汁，再配上一碗蛤仔排骨湯非常滿足。",
            "parking_car": "美麗島捷運站轉乘停車場",
            "parking_scooter": "美麗島站 1 號出口機車格",
            "parking_bike": "YouBike 2.0 捷運美麗島站",
            "transit": "捷運美麗島站 1 號出口直達"
        },
        {
            "name": "聰明鸭肉店", 
            "type": "煙燻鴨肉/鴨肉冬粉", 
            "address": "高雄市新興區復興二路201號", 
            "hours": "11:00–21:00 (週二公休)",
            "desc": "傳承數十年的老字號鴨肉名店！煙燻鴨肉香氣撲鼻且肉質紮實多汁，搭配鴨肉冬粉與特製切盤小菜，是新興區口碑極佳的古早味。",
            "parking_car": "復興二路路邊公有停車格",
            "parking_scooter": "復興二路與青年路口機車位",
            "parking_bike": "YouBike 2.0 青年復興路口站",
            "transit": "捷運信義國小站步行約 10 分鐘"
        },
        {
            "name": "原鄉牛肉麵", 
            "type": "站前濃郁紅燒牛肉麵", 
            "address": "高雄市新興區林森一路272-1號", 
            "hours": "11:30–20:00 (週一公休)",
            "desc": "高雄火車站周邊超高評價牛肉麵！湯頭濃郁卻不油膩，半筋半肉牛肉塊軟嫩入味且切得厚實，搭配店家特製炒酸菜滋味絕佳。",
            "parking_car": "林森一路路邊停車格、建國二路收費停車場",
            "parking_scooter": "林森一路沿線機車格",
            "parking_bike": "YouBike 2.0 高雄車站",
            "transit": "高雄車站步行約 5 分鐘"
        },
        {
            "name": "阿英排骨飯", 
            "type": "富華市街排骨便當", 
            "address": "高雄市新興區富華市街80號", 
            "hours": "10:30–14:00, 16:30–20:00 (週六公休)",
            "desc": "深受上班族與在地人喜愛的古早味排骨便當！現炸排骨醃製入味且金黃多汁，搭配三樣配菜與古早味酸菜，是飽足實惠的選擇。",
            "parking_car": "七賢一路路邊停車格",
            "parking_scooter": "富華市街兩側劃線機車格",
            "parking_bike": "YouBike 2.0 捷運美麗島站",
            "transit": "捷運美麗島站 6 號出口步行約 6 分鐘"
        }
    ],
    "前鎮區": [
        {
            "name": "輝哥牛肉湯", 
            "type": "光華夜市溫體牛肉湯", 
            "address": "高雄市前鎮區光華二路438號", 
            "hours": "17:00–01:00 (週一公休)",
            "desc": "光華夜市超人氣溫體牛肉湯！每天新鮮現切牛肉淋上高溫鮮甜高湯，肉質粉嫩甘甜，搭配一碗牛肉炒飯是深夜最療癒的宵夜。",
            "parking_car": "廣西路收費停車場、光華二路路邊公有停車格",
            "parking_scooter": "光華夜市劃線機車格",
            "parking_bike": "YouBike 2.0 光華國小站",
            "transit": "搭乘公車至『光華夜市站』"
        },
        {
            "name": "朱爺爺QQ蛋地瓜球", 
            "type": "勞工公園銅板地瓜球", 
            "address": "高雄市前鎮區復興三路129-8號", 
            "hours": "12:30–19:00 (週一公休)",
            "desc": "勞工公園旁超佛心的銅板價地瓜球！現炸地瓜球一顆只要超低銅板價，口感外酥內 Q 香氣十足，總是吸引滿滿排隊人潮。",
            "parking_car": "復興三路路邊收費停車格",
            "parking_scooter": "勞工公園周邊劃線機車格",
            "parking_bike": "YouBike 2.0 捷運獅甲站",
            "transit": "捷運獅甲站 3 號出口步行約 3 三分鐘"
        },
        {
            "name": "前鎮肉圓", 
            "type": "草衙古早味清蒸肉圓", 
            "address": "高雄市前鎮區鎮州路82號", 
            "hours": "06:00–13:00",
            "desc": "前鎮草衙地區隱藏版的古早味早點！清蒸肉圓皮薄餡多、肉質鮮美，淋上特製蒜蓉甘甜醬汁，是在地居民從小吃到大的家鄉味。",
            "parking_car": "鎮州路路邊停車格",
            "parking_scooter": "店家門口機車位",
            "parking_bike": "YouBike 2.0 輕軌前鎮之星站",
            "transit": "輕軌前鎮之星站步行約 8 分鐘"
        },
        {
            "name": "林家水餃麵食館", 
            "type": "光華夜市水餃麵食", 
            "address": "高雄市前鎮區光華二路388號", 
            "hours": "11:00–20:30",
            "desc": "光華美食街上實惠飽足的麵食館！手包水餃內餡紮實多汁，酸辣湯與牛肉麵湯頭濃郁，是在地人解決午晚餐的人氣首選。",
            "parking_car": "光華二路路邊停車格",
            "parking_scooter": "光華夜市機車位",
            "parking_bike": "YouBike 2.0 光華國小站",
            "transit": "搭乘公車至『光華夜市站』"
        },
        {
            "name": "約翰隨手港飲", 
            "type": "港式絲襪奶茶/菠蘿油", 
            "address": "高雄市前鎮區光華二路356號", 
            "hours": "11:00–21:00",
            "desc": "光華夜市獨具特色的港式手搖飲與點心攤！提供道地凍絲襪奶茶、凍檸茶與現烤冰火菠蘿油，逛夜市隨手帶上一份非常合適。",
            "parking_car": "廣西路收費停車場",
            "parking_scooter": "光華二路劃線機車格",
            "parking_bike": "YouBike 2.0 光華國小站",
            "transit": "搭乘公車至『光華夜市站』"
        },
        {
            "name": "獅甲綠豆湯", 
            "type": "傳統古法綠豆湯/薏仁湯", 
            "address": "高雄市前鎮區中山二路162號", 
            "hours": "10:00–22:00 (週日公休)",
            "desc": "捷運獅甲站旁古法熬煮甜湯！綠豆熬至鬆軟綿密且保留粒粒口感，甜度適中涼爽解熱，是前鎮區歷史悠久的經典消暑點心。",
            "parking_car": "中山二路路邊收費停車格",
            "parking_scooter": "中山二路劃線機車格",
            "parking_bike": "YouBike 2.0 捷運獅甲站",
            "transit": "捷運獅甲站 1 號出口步行約 4 分鐘"
        }
    ],
    "鳳山區": [
        {
            "name": "中華街夜市鴨肉麵", 
            "type": "捷運鳳山站鴨肉麵/當歸湯", 
            "address": "高雄市鳳山區中華街28號", 
            "hours": "11:00–20:30",
            "desc": "鳳山捷運站出口中華街夜市必吃首選！鮮切鴨肉肉質軟嫩，鴨油麵香氣逼人，搭配當歸湯底清甜甘美，是在地經典古早味。",
            "parking_car": "捷運鳳山站轉乘地下/平面停車場、曹公路收費停車場",
            "parking_scooter": "中華街口與光遠路劃線機車位",
            "parking_bike": "YouBike 2.0 捷運鳳山站（2號出口）站",
            "transit": "捷運鳳山站 2 號出口步行約 1 分鐘"
        },
        {
            "name": "鳳山咸米苔目", 
            "type": "古早味咸米苔目/黑白切", 
            "address": "高雄市鳳山區維新路10號", 
            "hours": "06:30–21:00",
            "desc": "維新路上傳承多年的鹹米苔目名店！純米製作的米苔目 Q 彈有勁，大骨高湯加上香噴噴油蔥酥與肉片，呈現道地古早風味。",
            "parking_car": "維新路公有路邊停車格、鳳山公有停車場",
            "parking_scooter": "維新路與光明路劃線機車格",
            "parking_bike": "YouBike 2.0 鳳山國小站",
            "transit": "捷運大東站 2 號出口步行約 8 分鐘"
        },
        {
            "name": "永小白糖糕", 
            "type": "現炸白糖糕/芝麻球", 
            "address": "高雄市鳳山區光遠路308號", 
            "hours": "11:00–18:00 (週休二日)",
            "desc": "鳳山老字號的古早味炸白糖糕與芝麻球！外層炸得金黃酥脆，內層綿密軟糯，裹上白糖或芝麻粉，是極具代表性的台式點心。",
            "parking_car": "光遠路路邊停車格、大東文化藝術中心停車場",
            "parking_scooter": "光遠路兩側機車格",
            "parking_bike": "YouBike 2.0 捷運大東站",
            "transit": "捷運大東站 1 號出口步行約 3 分鐘"
        },
        {
            "name": "老張簡家草仔粿", 
            "type": "客家手作草仔粿/紅龜粿", 
            "address": "高雄市鳳山區信義街11號", 
            "hours": "07:00–13:00 (週一公休)",
            "desc": "隱藏在鳳山第一市場內的客家傳統米食！手作草仔粿外皮 Q 彈自帶草香，餡料包滿香炒蘿蔔絲與香菇肉燥，讓人回味無窮。",
            "parking_car": "曹公路收費停車場",
            "parking_scooter": "鳳山第一市場周邊機車格",
            "parking_bike": "YouBike 2.0 捷運鳳山站",
            "transit": "捷運鳳山站 2 號出口步行約 4 分鐘"
        },
        {
            "name": "鳳山老店水餃", 
            "type": "中山夜市薄皮爆汁水餃", 
            "address": "高雄市鳳山區中山路146-2號", 
            "hours": "11:00–20:00 (週二公休)",
            "desc": "中山夜市商圈傳承多年的水餃老店！皮薄餡多且高麗菜鮮甜爆汁，沾上獨門蒜頭醬油，配上一碗酸辣湯，簡單美味。",
            "parking_car": "曹公路收費停車場",
            "parking_scooter": "中山路劃線機車格",
            "parking_bike": "YouBike 2.0 捷運鳳山站",
            "transit": "捷運鳳山站 2 號出口步行約 5 分鐘"
        },
        {
            "name": "李家肉圓", 
            "type": "瑞興路清蒸肉圓/早點", 
            "address": "高雄市鳳山區瑞興路64號", 
            "hours": "05:00–13:00 (週四公休)",
            "desc": "鳳山在地人清晨就排隊的清蒸肉圓！米漿外皮 Q 軟厚實，內餡鮮肉多汁，銅板價格美味實惠，是極具代表性的台式早餐。",
            "parking_car": "瑞興路路邊停車格",
            "parking_scooter": "店家門口機車位",
            "parking_bike": "YouBike 2.0 捷運大東站",
            "transit": "捷運大東站 2 號出口步行約 10 分鐘"
        }
    ],
    "苓雅區": [
        {
            "name": "老店柏弘肉燥飯", 
            "type": "米其林必比登肉燥飯", 
            "address": "高雄市苓雅區青年二路167號", 
            "hours": "17:00–02:00 (週二公休)",
            "desc": "榮獲米其林必比登推薦的深夜肉燥飯名店！滷至金黃膠質滿滿的切丁豬肉，肥而不膩，淋在粒粒分明的白飯上極其幸福。",
            "parking_car": "青年二路路邊公有停車格、成功一路停車場",
            "parking_scooter": "青年二路沿線劃線機車格",
            "parking_bike": "YouBike 2.0 青年成功路口站",
            "transit": "輕軌光榮碼頭站步行約 8 分鐘"
        },
        {
            "name": "南豐肉燥飯", 
            "type": "自強夜市爌肉飯/肉燥飯", 
            "address": "高雄市苓雅區自強三路139號", 
            "hours": "09:00–00:00",
            "desc": "自強夜市內數十年如一日的超人氣肉燥飯！招牌控肉飯給予一整塊滷得透軟綿密的五花肉，醬香濃郁，搭配酸菜非常完美。",
            "parking_car": "自強三路路邊停車格、四維四路停車場",
            "parking_scooter": "自強夜市機車位",
            "parking_bike": "YouBike 2.0 苓雅國小站",
            "transit": "捷運三多商圈站 7 號出口步行約 8 分鐘"
        },
        {
            "name": "正牌白糖糕", 
            "type": "自強夜市銅板白糖糕/花生芝麻", 
            "address": "高雄市苓雅區自強三路41號", 
            "hours": "12:30–21:30",
            "desc": "自強夜市必吃銅板傳統甜點！外層酥脆、內裡如糯米般外香內軟，提供花生與芝麻兩種經典口味，熱騰騰現炸最好吃。",
            "parking_car": "青年二路收費停車場",
            "parking_scooter": "青年路與自強路口劃線機車格",
            "parking_bike": "YouBike 2.0 青年成功路口站",
            "transit": "捷運三多商圈站步行約 10 分鐘"
        },
        {
            "name": "黃家牛肉麵", 
            "type": "興中夜市紅燒牛肉麵/沙茶牛肉", 
            "address": "高雄市苓雅區興中一路206號", 
            "hours": "11:00–15:00, 17:00–20:00 (週二公休)",
            "desc": "興中夜市商圈口碑極佳的牛肉麵專賣！紅燒湯頭甘甜濃郁，半筋半肉牛肉塊軟嫩入味，店內的沙茶牛肉熱炒也是老饕必點。",
            "parking_car": "忠孝二路與興中一路口停車格",
            "parking_scooter": "興中一路劃線機車格",
            "parking_bike": "YouBike 2.0 捷運三多商圈站",
            "transit": "捷運三多商圈站 6 號出口步行約 6 分鐘"
        },
        {
            "name": "油條黃鹹酥雞/宵夜", 
            "type": "酥炸香脆油條/深夜鹹酥雞", 
            "address": "高雄市苓雅區自強三路104號", 
            "hours": "18:00–01:30",
            "desc": "自強夜市特色宵夜炸物攤！將金黃油條炸至極致香酥再撒上特製胡椒粉，搭配鹹酥雞、魷魚與九層塔，是夜貓子的誘人宵夜。",
            "parking_car": "四維四路收費停車場",
            "parking_scooter": "自強夜市劃線機車格",
            "parking_bike": "YouBike 2.0 苓雅國小站",
            "transit": "捷運三多商圈站 7 號出口步行約 9 分鐘"
        }
    ]
}

# ==========================================
# 3. 資料庫：景點與文創場域
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

    st.header("🎯 選擇探索類別：")
    category = st.radio(
        "選擇類別", 
        ["🍜 在地美食小吃 ", "🏛️ 熱門景點/文創商店"],
        label_visibility="collapsed"
    )
    
    db = KAOHSIUNG_FOODS if "美食" in category else KAOHSIUNG_ATTRACTIONS
    selected_district = st.selectbox("📍 選擇區域商圈", list(db.keys()))
    
    with st.expander("📌 查看當前分組清單", expanded=False):
        for item in db[selected_district]:
            st.markdown(f"- **{item['name']}** ({item['type']})")
    
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

def pick_next_item(current_db, district, current_item=None):
    candidates = current_db.get(district, [])
    if not candidates:
        return None
    if current_item and len(candidates) > 1:
        candidates = [x for x in candidates if x["name"] != current_item["name"]]
    return random.choice(candidates)

# ==========================================
# 5. 主畫面呈現
# ==========================================
if generate_btn:
    current_db = KAOHSIUNG_FOODS if "美食" in category else KAOHSIUNG_ATTRACTIONS
    selected_item = pick_next_item(current_db, selected_district)

    st.session_state["current_item"] = selected_item
    st.session_state["current_district"] = selected_district
    st.session_state["chat_history"] = []

if "current_item" in st.session_state:
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
            current_db = KAOHSIUNG_FOODS if "美食" in category else KAOHSIUNG_ATTRACTIONS
            next_item = pick_next_item(current_db, selected_district, st.session_state.get("current_item"))
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

    with col2:
        # 僅在此處加上 margin-top 修正，向上拉平對齊左側的 caption
        st.markdown(f"<h3 style='margin-top: -12px; margin-bottom: 4px; font-weight: bold;'>探索目標：{item['name']}</h3>", unsafe_allow_html=True)
        st.caption(f"📍 行政區劃：{district}")
        
        # 動態取得 item['desc']，如果沒有介紹則顯示備用預設文字
        item_desc = item.get('desc', f"歡迎來到【{item['name']}】！這裡代表著高雄港都豐富的文化與特色，非常適合親自來走走體驗。")
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
                    import requests
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
    st.markdown('<div class="main-title">高雄 50 家美食 × 50 個景點隨機導覽系統</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">【高雄商圈振興專案】精選在地美食與特色景點，精準導流實體人潮！</div>', unsafe_allow_html=True)

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

    if quick_col1.button("🎨 駁二藝術特區", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_ATTRACTIONS["港灣與文創區"][0]
        st.session_state["current_district"] = "港灣與文創區"
        st.session_state["chat_history"] = []
        st.rerun()

    if quick_col2.button("🍜 鹽埕鴨肉珍", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_FOODS["鹽埕區"][0]
        st.session_state["current_district"] = "鹽埕區"
        st.session_state["chat_history"] = []
        st.rerun()

    if quick_col3.button("🐲 蓮池潭龍虎塔", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_ATTRACTIONS["自然景觀與園區"][0]
        st.session_state["current_district"] = "左營區"
        st.session_state["chat_history"] = []
        st.rerun()

    if quick_col4.button("🧋 樺達奶茶總店", use_container_width=True):
        st.session_state["current_item"] = KAOHSIUNG_FOODS["鹽埕區"][1]
        st.session_state["current_district"] = "鹽埕區"
        st.session_state["chat_history"] = []
        st.rerun()