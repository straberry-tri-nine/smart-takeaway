  
import streamlit as st
from openai import OpenAI
import json
import math
import requests
import pandas as pd
import os
import base64

# ================= 0. 🎀 吉伊卡哇风格 UI 配置 =================
st.set_page_config(page_title="乌萨奇食堂", page_icon="🐰", layout="centered")

# 初始化页面状态（控制是显示封面还是主程序）
if 'page_state' not in st.session_state:
    st.session_state.page_state = "welcome"

# 读取本地图片并转换为 Base64，方便在 CSS 和 HTML 中使用
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

# 尝试读取你保存的图片
img_base64 = get_base64_of_bin_file("chef.jpg")
img_html = f'<img src="data:image/jpeg;base64,{img_base64}" class="chef-img">' if img_base64 else '<div style="padding:50px; background:white; border-radius:50%;">图片未找到，请确保图片名为 chef.jpg</div>'

custom_css = """
<style>
    /* 隐藏原厂水印 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 全局字体：圆润感 */
    html, body, [class*="css"] {
        font-family: 'PingFang SC', 'Microsoft YaHei', 'Comic Sans MS', sans-serif;
    }

    /* 背景：提取了图片中的奶黄色，渐变到淡淡的樱花粉 */
    .stApp {
        background: linear-gradient(180deg, #FFF6D9 0%, #FFF0F5 100%);
    }

    /* ================= 封面专属样式 ================= */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 80vh;
        text-align: center;
    }
    
    .chef-img {
        width: 280px;
        border-radius: 50%;
        border: 6px solid #FFF;
        box-shadow: 0 8px 25px rgba(255, 180, 162, 0.4);
        margin-bottom: 20px;
        /* 添加可爱的上下浮动动画 */
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
        100% { transform: translateY(0px); }
    }

    /* 可爱的按钮样式 */
    .stButton>button {
        background-color: #FF85A1 !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 10px 30px !important;
        border: 4px solid #FFF !important;
        font-size: 1.2em !important;
        font-weight: bold !important;
        transition: all 0.3s !important;
        box-shadow: 0 4px 15px rgba(255, 133, 161, 0.4) !important;
    }
    .stButton>button:hover {
        transform: scale(1.05) !important;
        background-color: #FF5C8D !important;
    }

    /* ================= 主界面组件美化 ================= */
    /* 数据看板美化：圆润的白底卡片 */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 25px;
        padding: 15px;
        border: 3px dashed #FFD1DC; /* 粉色虚线边框，超可爱 */
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    
    /* 聊天气泡美化 */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 20px;
        padding: 10px 20px;
        margin-bottom: 15px;
        border: 2px solid #FFE4E1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }

    /* 标题样式 */
    .cute-title {
        text-align: center;
        color: #FF7A9A;
        font-size: 2.5em;
        font-weight: 900;
        margin-bottom: 5px;
        text-shadow: 2px 2px 0px #FFF;
    }
    .cute-subtitle {
        text-align: center;
        color: #FFA07A;
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: 30px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ================= 1. 欢迎封面拦截逻辑 =================
if st.session_state.page_state == "welcome":
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    
    # 显示浮动的厨师图片
    st.markdown(img_html, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #FF7A9A; font-size: 2.8em; text-shadow: 2px 2px 0px #FFF;'>今天也要好好吃饭哦！</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #FF9EBB; font-size: 1.2em; font-weight: bold;'>我是你的专属 AI 饭搭子 ✨</p>", unsafe_allow_html=True)
    
    st.write("") # 占位空行
    
    # 点击按钮进入主界面
    if st.button("🍽️ 点我开始点餐！"):
        st.session_state.page_state = "main"
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop() # 拦截后续代码，直到状态改变

# ================= 2. 核心配置区 (以下为原业务逻辑) =================
try:
    MY_API_KEY = st.secrets["DEEPSEEK_KEY"]
    GAODE_KEY = st.secrets["GAODE_KEY"]
except:
    st.error("⚠️ 找不到 API Key！请检查配置。")
    st.stop() 

client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")

def get_location_by_address(address, shops_data):
    if not GAODE_KEY or GAODE_KEY == "你的高德KEY填在这里":
        if shops_data and len(shops_data) > 0:
            return shops_data[0]["纬度"] + 0.005, shops_data[0]["经度"] + 0.005
        return 39.9042, 116.4074 
    try:
        url = f"https://restapi.amap.com/v3/geocode/geo?address={address}&key={GAODE_KEY}"
        response = requests.get(url).json()
        if response['status'] == '1' and len(response['geocodes']) > 0:
            location_str = response['geocodes'][0]['location']
            lon, lat = map(float, location_str.split(','))
            return lat, lon 
    except Exception as e:
        pass
    if shops_data: return shops_data[0]["纬度"] + 0.005, shops_data[0]["经度"] + 0.005
    return 39.9042, 116.4074 

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def estimate_time(distance_km):
    return int(15 + (distance_km * 10))

@st.cache_data 
def load_shops_data():
    if os.path.exists("shops.xlsx"):
        df = pd.read_excel("shops.xlsx")
        df = df.fillna("") 
        return df.to_dict('records')
    else:
        return [
            {"店名": "张小生麻辣烫", "评分": 4.8, "价格": 25, "标签": "重口味,加香菜", "纬度": 39.9050, "经度": 116.4080, "菜单": "招牌麻辣烫, 炸肉丸, 冰红茶"},
            {"店名": "沙县小吃", "评分": 3.9, "价格": 15, "标签": "清淡,鸭腿饭", "纬度": 39.9160, "经度": 116.4010, "菜单": "鸭腿饭, 飘香拌面, 乌鸡汤"}
        ]

ALL_SHOPS = load_shops_data()

# ================= 3. 主界面排版 =================
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {"spice_preference": "未知", "dislikes": [], "favorites": []}

st.markdown('<div class="cute-title">🍲 乌萨奇食堂</div>', unsafe_allow_html=True)
st.markdown('<div class="cute-subtitle">越用越懂你的 AI 饭搭子</div>', unsafe_allow_html=True)

st.write("### 🐾 你的专属口味卡片")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="🌶️ 辣度偏好", value=st.session_state.user_profile['spice_preference'])
with col2:
    dislikes_str = ', '.join(st.session_state.user_profile['dislikes']) if st.session_state.user_profile['dislikes'] else '无'
    st.metric(label="🚫 坚决不吃", value=dislikes_str)
st.write("") 
st.divider()

with st.sidebar:
    st.image("https://api.dicebear.com/7.x/bottts/svg?seed=Mimi&backgroundColor=FFB6C1", width=150)
    st.header("⚙️ 点餐设置")
    
    user_address = st.text_input("📍 你的位置：", value="北京市海淀区北京科技大学")
    user_lat, user_lon = get_location_by_address(user_address, ALL_SHOPS)
    
    if GAODE_KEY != "你的高德KEY填在这里":
        st.success("✅ 魔法雷达已开启")
    
    max_distance = st.slider("🛵 最远配送距离 (公里)", min_value=0.5, max_value=3.0, value=1.5, step=0.5)

available_shops_text = ""
for shop in ALL_SHOPS:
    dist = calculate_distance(user_lat, user_lon, shop["纬度"], shop["经度"])
    if dist <= max_distance:
        time_est = estimate_time(dist)
        menu_info = shop.get("菜单", "暂无详细菜单") 
        rating_info = shop.get("评分", "暂无评分")
        available_shops_text += f"- 【{shop['店名']}】: 评分{rating_info}，人均{shop['价格']}元。标签：{shop['标签']}。距离：{dist}公里，预计配送：{time_est}分钟。菜单：{menu_info}\n"

if not available_shops_text:
    available_shops_text = "呜呜，附近没有找到好吃的，要不要走远一点看看？"

with st.expander(f"👀 偷看【{user_address}】附近的菜单"):
    st.text(available_shops_text)

# ================= 4. 聊天与 AI 逻辑 =================
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("想吃点什么呀？（比如：想吃点热乎的，不要辣）")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.status("🐾 小八正在帮你找好吃的...", expanded=True) as status:
        st.write("📝 记下你的口味啦...")
        profile_update_prompt = f"""
        当前账本：{json.dumps(st.session_state.user_profile, ensure_ascii=False)}
        用户说："{user_input}"
        请提取辣度偏好或忌口，返回更新后的 JSON。不涉及则原样返回。只返回JSON！
        """
        try:
            update_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": profile_update_prompt}],
                response_format={"type": "json_object"} 
            )
            st.session_state.user_profile = json.loads(update_response.choices[0].message.content)
        except:
            pass 
            
        st.write("🍳 正在翻看菜单...")
        recommend_prompt = f"""
        你是一个超级懂吃、幽默俏皮、极具网感的大学生饭搭子，说话风格像可爱的吉伊卡哇角色。
        用户当前位置：【{user_address}】。
        附近可选的【商家及菜单】：
        {available_shops_text}
        
        用户的口味账本：{json.dumps(st.session_state.user_profile, ensure_ascii=False)}
        用户现在的需求是：“{user_input}”
        
        ⚠️ 必须严格遵守以下设定：
        1. 【高分优先，宁缺毋滥】：精挑细选 最多 3 家最符合要求的店。
        2. 【预算与点菜】：直接从菜单里挑出具体的菜品推荐给TA。
        3. 【俏皮金句】：模仿吉伊卡哇中角色的语气，多用颜文字和可爱的语气词（如：捏、呀、哦）。
        4. 【贴心细节】：顺嘴提一句距离和大概多久送到。如果有忌口，记得邀功。
        """

        try:
            recommend_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": recommend_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            final_answer = recommend_response.choices[0].message.content
            status.update(label="✨ 找到啦！快看看合不合胃口！", state="complete", expanded=False)
            st.balloons() 
            
        except Exception as e:
            status.update(label="❌ 哎呀，出错了", state="error")
            final_answer = f"呜呜，推荐失败了，错误信息：{e}"

    st.session_state.chat_history.append({"role": "assistant", "content": final_answer})
    st.rerun()
