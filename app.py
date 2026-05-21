  
import streamlit as st
from openai import OpenAI
import json
import math
import requests
import pandas as pd
import os
# ================= 0. 🌟 终极 UI 美化魔法 =================
st.set_page_config(page_title="智能外卖助手", page_icon="🍱", layout="centered")
# 注入高级 CSS 样式
custom_css = """
<style>
    /* 隐藏原厂水印 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 苹果风渐变色大标题 */
    .gradient-title {
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF904B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        font-weight: 900;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ================= 1. 核心配置区（🌟 安全升级版） =================
# 我们不再把密码写死在代码里，而是让程序去云端的“保险箱”里拿！
try:
    MY_API_KEY = st.secrets["DEEPSEEK_KEY"]
    GAODE_KEY = st.secrets["GAODE_KEY"]
except:
    st.error("⚠️ 找不到 API Key！如果你在本地运行，请检查配置；如果在云端，请配置 Secrets。")
    st.stop() # 找不到密码就停止运行

client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")

# ================= 2. 真实高德定位系统 =================
def get_location_by_address(address, shops_data):
    if not GAODE_KEY:
        if shops_data and len(shops_data) > 0:
            st.toast("⚠️ 未配置高德Key，使用表格第一家店附近作为模拟位置。")
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
        st.error("高德地图开小差了，正在使用备用定位...")
    
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

# ================= 3. 接入真实 Excel 数据 =================
@st.cache_data 
def load_shops_data():
    if os.path.exists("shops.xlsx"):
        df = pd.read_excel("shops.xlsx")
        df = df.fillna("") 
        return df.to_dict('records')
    else:
        # 保底数据
        return [
            {"店名": "张小生麻辣烫", "评分": 4.8, "价格": 25, "标签": "重口味,加香菜", "纬度": 39.9050, "经度": 116.4080, "菜单": "招牌麻辣烫, 炸肉丸, 冰红茶"},
            {"店名": "沙县小吃", "评分": 3.9, "价格": 15, "标签": "清淡,鸭腿饭", "纬度": 39.9160, "经度": 116.4010, "菜单": "鸭腿饭, 飘香拌面, 乌鸡汤"},
            {"店名": "塔斯汀中国汉堡", "评分": 4.6, "价格": 28, "标签": "快餐,微辣", "纬度": 39.9080, "经度": 116.4050, "菜单": "香辣鸡腿堡, 粗薯条, 可乐"}
        ]

ALL_SHOPS = load_shops_data()
# ================= 4. 🌟 全新排版：界面与小账本 =================
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {"spice_preference": "未知", "dislikes": [], "favorites": []}

# --- 主页头部：炫酷标题 ---
st.markdown('<div class="gradient-title">智能外卖助手</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">✨ 越用越懂你的 AI 饭搭子 ✨</div>', unsafe_allow_html=True)

# --- 主页 C 位：吃货画像数据看板 ---
# 我们用 st.columns 把屏幕分成两半，用 st.metric 做成高级的数据卡片！
st.write("### 👤 你的专属吃货画像")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="🌶️ 辣度偏好", value=st.session_state.user_profile['spice_preference'])
with col2:
    dislikes_str = ', '.join(st.session_state.user_profile['dislikes']) if st.session_state.user_profile['dislikes'] else '无'
    st.metric(label="🚫 坚决不吃", value=dislikes_str)
st.divider()

# --- 侧边栏：降级为设置中心 ---
with st.sidebar:
    # 加一个可爱的随机机器人头像
    st.image("https://api.dicebear.com/7.x/bottts/svg?seed=Felix&backgroundColor=FF4B4B", width=150)
    st.header("⚙️ 点餐设置")
    
    user_address = st.text_input("📍 你的位置：", value="北京市天安门", help="建议带上城市名，定位更准哦！")
    user_lat, user_lon = get_location_by_address(user_address, ALL_SHOPS)
    
    if GAODE_KEY != "你的高德KEY填在这里":
        st.success("✅ 高德地图已连接")
    st.caption(f"🌍 坐标：{user_lat:.4f}, {user_lon:.4f}")
    
    max_distance = st.slider("🛵 最远配送距离 (公里)", min_value=0.5, max_value=10.0, value=3.0, step=0.5)

# ================= 5. 智能漏斗：筛选真实商家 =================
available_shops_text = ""
for shop in ALL_SHOPS:
    dist = calculate_distance(user_lat, user_lon, shop["纬度"], shop["经度"])
    if dist <= max_distance:
        time_est = estimate_time(dist)
        menu_info = shop.get("菜单", "暂无详细菜单") 
        # 🌟 微调：获取评分，并拼接到文本里
        rating_info = shop.get("评分", "暂无评分")
        available_shops_text += f"- 【{shop['店名']}】: 评分{rating_info}，人均{shop['价格']}元。标签：{shop['标签']}。距离：{dist}公里，预计配送：{time_est}分钟。菜单：{menu_info}\n"

if not available_shops_text:
    available_shops_text = "抱歉，你设置的范围内没有找到商家，请扩大搜索距离或更改地址。"

with st.expander(f"👀 查看【{user_address}】附近的真实商家与菜单"):
    st.text(available_shops_text)

# ================= 6. 大脑开始工作 =================
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("点餐要求 或 吐槽反馈（比如：我不吃香菜，想吃点带汤的）")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.status("🧠 助手正在疯狂运转中...", expanded=True) as status:
        st.write("🕵️‍♂️ 第一步：更新你的口味账本...")
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
            
        st.write("📝 第二步：正在为你精心搭配菜品...")
        
        # 🌟 核心修改：强调高分优先，按人均算预算，不再纠结单品价格
        recommend_prompt = f"""
        你是一个超级懂吃、幽默俏皮、极具网感的大学生饭搭子。
        用户当前位置：【{user_address}】。
        附近可选的【商家及菜单】：
        {available_shops_text}
        
        用户的口味账本：{json.dumps(st.session_state.user_profile, ensure_ascii=False)}
        用户现在的需求是：“{user_input}”
        
        ⚠️ 必须严格遵守以下设定：
        1. 【高分优先，宁缺毋滥】：精挑细选 最多 3 家 最符合要求的店。在满足口味和预算的前提下，**优先推荐评分存在且较高的店铺**！
        2. 【预算与点菜】：如果用户有预算限制，请参考店铺的【人均价格】来判断是否合适。直接从菜单里挑出具体的菜品推荐给TA（不需要计算单品价格，只提人均即可）。
        3. 【俏皮金句】：为每家店写一句极其轻松、幽默的推荐语。可以顺便夸一下这家店的评分（比如：“这家高达4.8分，跟着群众吃绝对不踩雷！”）。
        4. 【贴心细节】：顺嘴提一句距离和大概多久送到。如果有忌口，记得邀功。
        5. 【排版自然】：拒绝冷冰冰的1234列表，多用emoji，像微信聊天一样。
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
            status.update(label="✨ 菜品搭配完成！", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ 哎呀，出错了", state="error")
            final_answer = f"推荐失败了：{e}"

    st.session_state.chat_history.append({"role": "assistant", "content": final_answer})
    st.rerun()

