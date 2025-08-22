import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk import word_tokenize, ngrams
from nltk.stem import WordNetLemmatizer
import os

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---- Sidebar Navigation ----
def navigation_guide(current_page: str):
    pages = [
        "Expected Outcomes",
        "📑 Analysis",
        "📊 EDA",
        "⚙️ Data Process",
        "📈 Modelling",
        "📖 Interpretation",
        "🚀 Deployment"
    ]
    with st.sidebar:
        st.markdown("## 📌 Navigation Guide")
        for page in pages:
            if page == current_page:
                st.markdown(f"🔵 **{page}**")  # highlight active
            else:
                st.markdown(page)

# Call navigation for this page
navigation_guide("📑 Analysis")

# ---- Page Content ----
st.title("📑 Analysis")

st.markdown("### 🔄 Scenario Comparison")
with st.expander("ℹ️ Description", expanded=False):
    st.write("""
    Scenario analysis evaluates how investment outcomes change under 
    alternative future states, such as optimistic, baseline, and 
    pessimistic conditions. This technique supports robust planning by 
    illustrating potential deviations from the central forecast.
    """)

# --- Define Scenarios ---
years = np.arange(2025, 2046)
baseline = np.cumprod([1.05]*len(years)) * 100
optimistic = np.cumprod([1.08]*len(years)) * 100
pessimistic = np.cumprod([1.03]*len(years)) * 100

df_scen = pd.DataFrame({
    "Year": years.astype(int),
    "Baseline (5%)": baseline,
    "Optimistic (8%)": optimistic,
    "Pessimistic (3%)": pessimistic
})

# --- Chart ---
fig, ax = plt.subplots()
ax.plot(df_scen["Year"], df_scen["Baseline (5%)"], label="Baseline (5%)", color="blue")
ax.plot(df_scen["Year"], df_scen["Optimistic (8%)"], label="Optimistic (8%)", color="green")
ax.plot(df_scen["Year"], df_scen["Pessimistic (3%)"], label="Pessimistic (3%)", color="red")
ax.set_xlabel("Year")
ax.set_ylabel("Index Value (Relative Growth)")
ax.set_title("Scenario Comparison")
ax.legend()
st.pyplot(fig)

# --- Download ---
csv = df_scen.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Scenario Results (CSV)",
    data=csv,
    file_name="scenario_analysis.csv",
    mime="text/csv"
)



# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="EDA & Forum Scraper", layout="wide")

# ----------------------------
# Download required NLTK data
# ----------------------------
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

# ----------------------------
# Load EDA Data
# ----------------------------
@st.cache_data
def load_data(path: str = "data.csv"):
    if not os.path.exists(path):
        return None, f"File not found: {path}"
    try:
        df = pd.read_csv(path)
        return df, None
    except Exception as e:
        return None, f"Error reading {path}: {e}"

# ----------------------------
# Reddit Scraper (No API)
# ----------------------------
@st.cache_data(show_spinner=False)
def scrape_reddit_no_api(query="rent vs buy", subreddit="MalaysianPF", limit=20):
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&limit={limit}&sort=new"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as e:
        return pd.DataFrame([{"error": f"Network error: {e}"}])

    if r.status_code != 200:
        return pd.DataFrame([{"error": f"Failed to fetch Reddit data: HTTP {r.status_code}"}])

    data = r.json()
    posts = []
    for post in data.get("data", {}).get("children", []):
        p = post.get("data", {})
        posts.append({
            "platform": "Reddit",
            "subreddit": subreddit,
            "title": p.get("title"),
            "url": "https://reddit.com" + str(p.get("permalink", "")),
            "content": (p.get("selftext") or "")[:300]
        })
    return pd.DataFrame(posts)

# ----------------------------
# Text Preprocessing
# ----------------------------
def preprocess_text(text_series: pd.Series):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    all_tokens = []
    for text in text_series.dropna().astype(str):
        tokens = word_tokenize(text.lower())
        tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalpha() and t not in stop_words]
        all_tokens.extend(tokens)
    return all_tokens

def get_top_ngrams(tokens, n=1, top_k=10):
    if n == 1:
        c = Counter(tokens)
    else:
        c = Counter(ngrams(tokens, n))
    return c.most_common(top_k)

# ----------------------------
# Streamlit Layout
# ----------------------------
st.sidebar.title("🔍 Navigation")
page = st.sidebar.radio("Go to:", ["📊 EDA", "💬 Forum Scraper"])

# ----------------------------
# Page 1: EDA
# ----------------------------
if page == "📊 EDA":
    st.title("🔎 Exploratory Data Analysis (EDA)")

    df, err = load_data("data.csv")
    if err:
        st.error(err)
        st.stop()

    # Ensure Year is integer (consistent with Analysis/Expected Outcomes)
    if "Year" in df.columns:
        # Coerce to numeric first to avoid stray strings, then cast to int
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        # Optional: drop rows where Year couldn't be parsed
        if df["Year"].isna().any():
            df = df.dropna(subset=["Year"]).copy()
        df["Year"] = df["Year"].astype(int)
        df = df.reset_index(drop=True)

    # Data Preview
    st.subheader("📋 Data Preview")
    st.dataframe(df, use_container_width=True)

    # Summary Statistics
    st.subheader("📊 Summary Statistics")
    st.write(df.describe(include="all"))

    # Chart Selector
    st.subheader("📈 Visual Analysis")
    chart_type = st.selectbox(
        "Select a chart to display:",
        ["OPR vs Year", "EPF vs Year", "Price Growth vs Year", "Rent Yield vs Year", "Correlation Heatmap"]
    )

    if chart_type == "OPR vs Year" and "OPR_avg" in df.columns and "Year" in df.columns:
        fig, ax = plt.subplots()
        ax.plot(df["Year"], df["OPR_avg"], marker="o", label="OPR (%)", color="blue")
        ax.set_xlabel("Year"); ax.set_ylabel("OPR (%)")
        ax.set_title("Trend of OPR vs Year")
        ax.legend(); st.pyplot(fig)

    elif chart_type == "EPF vs Year" and "EPF" in df.columns and "Year" in df.columns:
        fig, ax = plt.subplots()
        ax.plot(df["Year"], df["EPF"], marker="s", label="EPF (%)", color="orange")
        ax.set_xlabel("Year"); ax.set_ylabel("EPF (%)")
        ax.set_title("Trend of EPF vs Year")
        ax.legend(); st.pyplot(fig)

    elif chart_type == "Price Growth vs Year" and "PriceGrowth" in df.columns and "Year" in df.columns:
        fig, ax = plt.subplots()
        ax.plot(df["Year"], df["PriceGrowth"], marker="^", label="Price Growth (%)", color="green")
        ax.set_xlabel("Year"); ax.set_ylabel("Price Growth (%)")
        ax.set_title("Trend of Price Growth vs Year")
        ax.legend(); st.pyplot(fig)

    elif chart_type == "Rent Yield vs Year" and "RentYield" in df.columns and "Year" in df.columns:
        fig, ax = plt.subplots()
        ax.plot(df["Year"], df["RentYield"], marker="d", label="Rental Yield (%)", color="purple")
        ax.set_xlabel("Year"); ax.set_ylabel("Rental Yield (%)")
        ax.set_title("Trend of Rental Yield vs Year")
        ax.legend(); st.pyplot(fig)

    elif chart_type == "Correlation Heatmap":
        st.write("### Correlation Matrix")
        corr = df.corr(numeric_only=True)
        st.dataframe(corr.style.background_gradient(cmap="Blues"), use_container_width=True)

    # Download
    st.subheader("⬇️ Download Data")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Dataset (CSV)", data=csv, file_name="EDA_data.csv", mime="text/csv")

