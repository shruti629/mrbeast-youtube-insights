import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans

# Page config
st.set_page_config(page_title="MrBeast YouTube Insights", layout="wide")
st.title("📊 MrBeast YouTube Channel Dashboard")

# --- Load data with cache ---
@st.cache_data
def load_data():
    df = pd.read_csv("src/data/youtube_channel_data_modified.csv")
    df.columns = df.columns.str.strip()
    df['Upload_Date'] = pd.to_datetime(df['Upload_Date'])
    return df

# --- Clustering function ---
@st.cache_data
def add_clusters(df, n_clusters=3):
    features = df[['Views', 'Likes', 'Comments']].copy().fillna(0)
    model = KMeans(n_clusters=n_clusters, random_state=42)
    df['Cluster'] = model.fit_predict(features)
    return df

# Load and cluster data
df = load_data()
df = add_clusters(df)

# --- Show raw data toggle ---
if st.checkbox("Show Raw Data"):
    st.write(df)

# --- Visual 1: Views vs Likes with clusters ---
st.subheader("📍 Views vs Likes")
fig1, ax1 = plt.subplots()
sns.scatterplot(data=df, x="Views", y="Likes", hue="Cluster", palette="Set2", ax=ax1)
ax1.set_title("Views vs Likes by Cluster")
st.pyplot(fig1)

# --- Visual 2: Cluster Distribution ---
st.subheader("🧠 Cluster Distribution of Videos")
fig2, ax2 = plt.subplots()
sns.countplot(data=df, x="Cluster", palette="Set3", ax=ax2)
ax2.set_title("Video Count per Cluster")
st.pyplot(fig2)

# --- Visual 3: Views Over Time ---
st.subheader("⏱️ Views Over Time")
df_sorted = df.sort_values("Upload_Date")
fig3, ax3 = plt.subplots()
ax3.plot(df_sorted["Upload_Date"], df_sorted["Views"], marker='o', linestyle='-')
ax3.set_xlabel("Upload_Date")
ax3.set_ylabel("Views")
ax3.set_title("Views Growth Over Time")
st.pyplot(fig3)

# --- Visual 4: Views per Video ---
st.subheader("🎬 Views Per Video")
fig4, ax4 = plt.subplots(figsize=(12, 6))
top_videos = df.sort_values("Views", ascending=False)
sns.barplot(data=top_videos, x="Title", y="Views", palette="viridis", ax=ax4)
plt.xticks(rotation=90)
ax4.set_title("Views per Video")
st.pyplot(fig4)

# --- Visual 5: Engagement Pie Chart ---
st.subheader("❤️ Engagement Distribution")
engagement_data = df[['Likes', 'Comments']].sum()
fig5, ax5 = plt.subplots()
ax5.pie(engagement_data, labels=engagement_data.index, autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
ax5.set_title("Total Engagement")
st.pyplot(fig5)

# --- Predict video performance (simple rule-based for now) ---
st.subheader("📈 Performance Prediction")
threshold = df["Views"].mean()
df["Performance"] = df["Views"].apply(lambda x: "High" if x >= threshold else "Low")

col1, col2 = st.columns(2)
with col1:
    st.metric("Average Views", f"{threshold:.0f}")
with col2:
    st.write("Prediction Rule: Views >= Avg → High | Else → Low")

st.dataframe(df[['Title', 'Views', 'Likes', 'Comments', 'Cluster', 'Performance']])


