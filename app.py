  
import streamlit as st
from openai import OpenAI
import json
import math
import requests
import pandas as pd
import os
import base64

# ================= 0. 🎀 页面基础配置 =================
st.set_page_config(page_title="乌萨奇食堂", page_icon="🐰", layout="centered")

if 'page_state' not in st.session_state:
    st.session_state.page_state = "welcome"

# 🌟 修复图片路径问题的神器：获取当前代码所在的绝对路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_base64_image(file_name):
    try:
        # 拼接绝对路径，确保 100% 能找到图片
        file_path = os.path.join(CURRENT_DIR, file_name)
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        return None

# 加载两张图片
chef_base64 = get_base64_image("chef.jpg")
bg_base64 = get_base64_image("bg.jpg")

# ================= 1. 🎨 动态 CSS 魔法 =================
# 基础 CSS（去灰边框、改字体）
base_css = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;} /* 隐藏顶部自带的灰色装饰条 */
    
    html, body, [class*="css"] {
        font-family: 'PingFang SC', 'Microsoft YaHei', 'Comic Sans MS', sans-serif;
    }

    /* 去掉侧边栏的灰色边框，加上半透明毛玻璃效果 */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-right: none !important; 
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
    }

    /* 聊天输入框去灰边，变可爱 */
    [data-testid="stChatInput"] {
        border: 2px solid #87CEFA !important; /* 换成小八的蓝色 */
        border-radius: 20px !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
    }

    /* 聊天气泡美化 */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 20px;
        padding: 10px 20px;
        margin-bottom: 15px;
        border: 2px dashed #87CEFA; /* 蓝色虚线 */
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* 数据看板卡片美化 */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 20px;
        padding: 15px;
        border: 3px solid #FFE4B5; /* 奶黄色边框 */
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    /* 展开框 (Expander) 去灰边 */
    [data-testid="stExpander"] {
        border: 2px solid #FFE4B5 !important;
        border-radius: 15px !important;
        background: rgba(255, 255, 255, 0.8) !important;
    }
</style>
"""

# 封面专属 CSS
welcome_css = """
<style>
    .stApp {
        background: linear-gradient(180deg, #FFF6D9 0%, #FFF0F5 100%);
    }
    .welcome-container {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; height: 80vh; text-align: center;
    }
    .chef-img {
        width: 280px; border-radius: 50%; border: 6px solid #FFF;
        box-shadow: 0 8px 25px rgba(255, 180, 162, 0.4);
        margin-bottom: 20px; animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
        100% { transform: translateY(0px); }
    }
    .stButton>button {
        background-color: #FFB6C1 !important; color: white !important;
        border-radius: 30px !important; padding: 10px 30px !important;
        border: 4px solid #FFF !important; font-size: 1.2em !important;
        font-weight: bold !important; transition: all 0.3s !important;
        box-shadow: 0 4px 15px rgba(255, 182, 193, 0.5) !important;
    }
    .stButton>button:hover {
        transform: scale(1.05) !important; background-color: #FF69B4 !important;
    }
</style>
"""

# 主页面专属 CSS (使用小八打饭背景图)
main_css = f"""
<style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* 为了防止背景图太花看不清字，给主内容区加一个半透明白色垫底 */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.65);
        border-radius: 30px;
        padding: 2rem;
        margin-top: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }}
    .cute-title {{
        text-align: center; color: #4682B4; /* 钢蓝色，呼应小八的帽子 */
        font-size: 2.5em; font-weight: 900; margin-bottom: 5px;
        text-shadow: 2px 2px 0px #FFF;
    }}
    .cute-subtitle {{
        text-align: center; color: #FF8C00; /* 橘色，呼应炸鸡腿 */
        font-size: 1.1em; font-weight: bold; margin-bottom: 30px;
        text-shadow: 1px 1px 0px #FFF;
    }}
</style>
"""

# 根据当前状态注入不同的 CSS
st.markdown(base_css, unsafe_allow_html=True)
if st.session_state.page_state == "welcome":
    st.markdown(welcome_css, unsafe_allow_html=True)
else:
    st.markdown(main_css, unsafe_allow_html=True)


# ================= 2. 欢迎封面逻辑 =================
if st.session_state.page_state == "welcome":
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    
    if chef_base64:
        st.markdown(f'<img src="data:image/jpeg;base64,{chef_base64}" class="chef-img">', unsafe_allow_html=True)
    else:
        st.error("找不到 chef.jpg，请检查图片是否在代码同目录下！")
        
    st.markdown("<h1 style='color: #FF7A9A; font-size: 2.8em; text-shadow: 2px 2px 0px #FFF;'>今天也要好好吃饭哦！</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #FF9EBB; font-size: 1.2em; font-weight: bold;'>我是你的专属 AI 饭搭子 ✨</p>", unsafe_allow_html=True)
    st.write("") 
    
    if st.button("🍽️ 点我开始点餐！"):
        st.session_state.page_state = "main"
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop() 

# ================= 3. 核心业务逻辑 (后端保持不变) =================
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
    if os.path.exists(os.path.join(CURRENT_DIR, "shops.xlsx")):
        df = pd.read_excel(os.path.join(CURRENT_DIR, "shops.xlsx"))
        df = df.fillna("") 
        return df.to_dict('records')
    else:
        return [
            {"店名": "张小生麻辣烫", "评分": 4.8, "价格": 25, "标签": "重口味,加香菜", "纬度": 39.9050, "经度": 116.4080, "菜单": "招牌麻辣烫, 炸肉丸, 冰红茶"},
            {"店名": "沙县小吃", "评分": 3.9, "价格": 15, "标签": "清淡,鸭腿饭", "纬度": 39.9160, "经度": 116.4010, "菜单": "鸭腿饭, 飘香拌面, 乌鸡汤"}
        ]

ALL_SHOPS = load_shops_data()

# ================= 4. 主界面排版 =================
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {"spice_preference": "未知", "dislikes": [], "favorites": []}

st.markdown('<div class="cute-title">🍲 八氏营养套餐</div>', unsafe_allow_html=True)
st.markdown('<div class="cute-subtitle">小八亲自为你打饭！想吃什么尽管说~</div>', unsafe_allow_html=True)

st.write("### 🐾 你的专属口味卡片")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="🌶️ 辣度偏好", value=st.session_state.user_profile['spice_preference'])
with col2:
    dislikes_str = ', '.join(st.session_state.user_profile['dislikes']) if st.session_state.user_profile['dislikes'] else '无'
    st.metric(label="🚫 坚决不吃", value=dislikes_str)
st.write("") 

with st.sidebar:
    st.image("https://api.dicebear.com/7.x/bottts/svg?seed=Mimi&backgroundColor=87CEFA", width=150)
    st.header("⚙️ 点餐设置")
    
    user_address = st.text_input("📍 你的位置：", value="北京市天安门")
    user_lat, user_lon = get_location_by_address(user_address, ALL_SHOPS)
    
    if GAODE_KEY != "你的高德KEY填在这里":
        st.success("✅ 魔法雷达已开启")
    
    max_distance = st.slider("🛵 最远配送距离 (公里)", min_value=0.5, max_value=3.0, value=1.5,step=0.5)

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

# ================= 5. 聊天与 AI 逻辑 =================
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
        你是一个超级懂吃、幽默俏皮、极具网感的大学生饭搭子，说话风格像可爱的吉伊卡哇角色小八（哈奇）。
        用户当前位置：【{user_address}】。
        附近可选的【商家及菜单】：
        {available_shops_text}
        
        用户的口味账本：{json.dumps(st.session_state.user_profile, ensure_ascii=False)}
        用户现在的需求是：“{user_input}”
        
        ⚠️ 必须严格遵守以下设定：
        1. 【高分优先，宁缺毋滥】：精挑细选 最多 3 家 最符合要求的店。
        2. 【预算与点菜】：直接从菜单里挑出具体的菜品推荐给TA。
        3. 【俏皮金句】：模仿吉伊卡哇中角色说话的语气，多用颜文字和可爱的语气词（如：捏、呀、哦）。
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
