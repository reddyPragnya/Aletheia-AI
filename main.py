import streamlit as st
import feedparser
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from datetime import datetime

# --- 🔑 API KEY SETUP ---
GOOGLE_API_KEY = "YOUR-GOOGLE-API-KEY"  # REPLACE WITH YOUR ACTUAL KEY

# --- CONFIGURATION ---
st.set_page_config(page_title="Aletheia AI", layout="wide", page_icon="🗞")

# --- 🎨 3D & GLASSMORPHISM CSS ---
glass_css = """
<style>
    /* 1. ANIMATED BACKGROUND */
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #141E30);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: #ffffff;
    }

    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    /* 2. GLASSMORPHISM CARD (THE MIRROR EFFECT) */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    /* 3. 3D HOVER EFFECT */
    .glass-card:hover {
        transform: translateY(-5px) scale(1.01);
        box-shadow: 0 15px 45px 0 rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.4);
    }

    /* 4. CUSTOM BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 50px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(118, 75, 162, 0.6);
    }

    /* 5. INPUT FIELDS Styling */
    .stTextInput input, .stTextArea textarea {
        background: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px;
    }
    
    /* 6. METRICS & ALERTS */
    div[data-testid="stMetricValue"] {
        text-shadow: 0 0 10px rgba(255,255,255,0.5);
    }
    
    /* TEXT COLORS */
    h1, h2, h3, p, label {
        color: #eeeeee !important;
    }
    
    .subtitle {
        color: #aaaaaa;
        font-size: 0.9em;
    }
</style>
"""
st.markdown(glass_css, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

@st.cache_data(ttl=300)
def fetch_feed(topic):
    formatted_topic = topic.replace(" ", "%20")
    rss_url = f"https://news.google.com/rss/search?q={formatted_topic}&hl=en-US&gl=US&ceid=US:en"
    return feedparser.parse(rss_url).entries[:6]

def analyze_and_generate(article, model_name):
    if not GOOGLE_API_KEY:
        st.error("Google API Key is missing.")
        return None

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.4,
    )

    template = """
    You are an AI News Analyst and Editor.
    
    ARTICLE DATA:
    Title: {title}
    Source: {source}
    Snippet: {snippet}

    TASKS:
    1. Categorize: Choose ONE from [Politics, Technology, Sports, Business, Health, Entertainment, Science].
    2. Sentiment: Analyze the tone (Positive, Negative, or Neutral).
    3. Fact Check: Assess credibility (0-100%) based on source reputation and snippet logic.
    4. Blog Post: Write a 100-word blog summary.
    5. Social Post: Write a punchy tweet with hashtags.

    OUTPUT FORMAT:
    Return valid JSON only. No markdown formatting.
    {{
        "category": "...",
        "sentiment": "...",
        "truth_score": 85,
        "fact_check_reason": "...",
        "blog_draft": "...",
        "social_draft": "..."
    }}
    """

    prompt = PromptTemplate(
        input_variables=["title", "source", "snippet"],
        template=template,
    )

    try:
        response = llm.invoke(prompt.format(
            title=article.title,
            source=article.source.title,
            snippet=article.summary
        ))
        
        # --- FIX STARTS HERE ---
        # 1. Extract the content
        content = response.content
        
        # 2. Use Regex to find the JSON object (everything between the first { and last })
        match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if match:
            clean_json_str = match.group(0)
            return json.loads(clean_json_str)
        else:
            # Fallback if no JSON structure is found
            st.error("AI did not return valid JSON. Raw output below:")
            st.code(content)
            return None
        # --- FIX ENDS HERE ---

    except Exception as e:
        st.error(f"AI Processing Error: {e}")
        return None
    
# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🗞 Aletheia AI")
    st.markdown("Automated Categorization, Verification & Drafting.")
    
    st.divider()
    model = st.selectbox("AI Model", ["gemini-2.5-flash", "gemini-2.5-pro"])
    auto_process = st.checkbox("Auto-Process All", value=False)
    
    # Stylized Info Box
    st.markdown("""
    <div style="background: rgba(255,215,0,0.1); border-left: 3px solid gold; padding: 10px; border-radius: 5px; font-size: 0.8em;">
        <b>Note:</b> Fact Checking is AI-estimated based on source credibility.
    </div>
    """, unsafe_allow_html=True)

# --- MAIN PAGE ---
st.title("News Intelligence Dashboard")

# Search Bar with unique styling container
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Search Topic", "Artificial Intelligence")
    with col2:
        st.write("") # Spacer
        st.write("") # Spacer
        if st.button("🔍 Fetch News", use_container_width=True):
            st.session_state['articles'] = fetch_feed(topic)
            st.rerun()

# --- DASHBOARD LOGIC ---
if 'articles' in st.session_state:
    articles = st.session_state['articles']
    
    st.markdown(f"### 📥 Incoming Feed: <span style='color:#764ba2'>{topic.title()}</span>", unsafe_allow_html=True)
    
    # We use HTML injection for the Grid to apply the 'glass-card' class 
    # but keep Streamlit buttons for functionality.
    for i, article in enumerate(articles):
        
        # Opening the 3D Glass Container
        st.markdown(f"""
        <div class="glass-card">
            <h3>{article.title}</h3>
            <p class="subtitle">{article.source.title} • {article.published}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # The button sits slightly outside the HTML block to retain Python logic
        col_act1, col_act2 = st.columns([0.85, 0.15])
        with col_act2:
            process_key = f"proc_{i}"
            if st.button("⚡ Analyze", key=process_key, use_container_width=True):
                st.session_state['active_article'] = article
                st.rerun()
        
    # --- EDITOR INTERFACE ---
    if 'active_article' in st.session_state:
        target = st.session_state['active_article']
        
        st.markdown("---")
        st.markdown("## 📝 Editor Studio")
        
        with st.spinner("🔮 AI is gazing into the data..."):
            if 'current_analysis' not in st.session_state or st.session_state.get('current_url') != target.link:
                result = analyze_and_generate(target, model)
                st.session_state['current_analysis'] = result
                st.session_state['current_url'] = target.link
            
            data = st.session_state['current_analysis']

        if data:
            # 1. NLP INSIGHTS (WRAPPED IN GLASS)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.caption("CATEGORY")
                st.markdown(f"{data.get('category', 'N/A')}")
            with m2:
                st.caption("SENTIMENT")
                sent = data.get("sentiment", "Neutral")
                color = "#00ff00" if sent=="Positive" else "#ff0000" if sent=="Negative" else "#ffff00"
                st.markdown(f"<span style='color:{color}; font-weight:bold'>{sent}</span>", unsafe_allow_html=True)
            with m3:
                st.metric("Credibility Score", f"{data.get('truth_score', 0)}%")
            with m4:
                st.caption("AI ANALYSIS")
                st.write(data.get("fact_check_reason", "No data"))
            st.markdown('</div>', unsafe_allow_html=True)

            # 2. EDITING FORM (WRAPPED IN GLASS)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            with st.form("editor_form"):
                st.markdown("#### Review & Edit Content")
                
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("📄 Blog / Website Draft**")
                    edited_blog = st.text_area("Blog Content", value=data.get("blog_draft", ""), height=300)
                
                with col_right:
                    st.markdown("🐦 Social Media Post**")
                    edited_social = st.text_area("Caption", value=data.get("social_draft", ""), height=150)
                    
                    st.markdown("⚙ Publishing Options**")
                    platform = st.multiselect("Publish to:", ["WordPress", "Twitter/X", "LinkedIn"], default=["Twitter/X"])

                st.write("")
                submitted = st.form_submit_button("🚀 Approve & Publish")
                
                if submitted:
                    st.balloons()
                    st.success(f"Published successfully to {', '.join(platform)}!")

            st.markdown('</div>', unsafe_allow_html=True)
