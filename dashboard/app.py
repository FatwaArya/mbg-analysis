import streamlit as st
import pandas as pd

st.set_page_config(page_title="MBG Discourse Analysis", page_icon="🍱", layout="wide")

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["dashboard_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Dashboard Password", type="password",
                      on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Dashboard Password", type="password",
                      on_change=password_entered, key="password")
        st.error("Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

st.title("🍱 MBG Program - Public Discourse Analysis")
st.caption("Makan Bergizi Gratis - Twitter/X Discourse Study 2025-2026")

@st.cache_data
def load_summary():
    return pd.read_csv("data/analysis/paper_statistics_summary.csv").iloc[0]

try:
    s = load_summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tweets", f"{int(s['total_tweets']):,}")
    c2.metric("Positive", f"{s['pct_positive']}%")
    c3.metric("Negative", f"{s['pct_negative']}%")
    c4.metric("Topics Found", f"{int(s['n_topics'])}")
    st.caption(f"Dataset: {s['date_from']} -> {s['date_to']}")
except Exception:
    st.info("Run full analysis pipeline first to populate dashboard.")

st.markdown("---")
st.markdown("""
Navigate using the sidebar:
- **Sentiment** — trends over time
- **Topics** — theme clusters
- **Engagement** — likes, RT, reply patterns
- **Explorer** — browse individual tweets
""")
