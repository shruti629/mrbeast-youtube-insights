import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="MrBeast YouTube Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("data/youtube_clustered_data.csv")

rt= load_data()

st.title("📊 MrBeast YouTube Channel Analytics Dashboard")

# Show basic stats
st.subheader("📌 Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Videos", len(rt))
col2.metric("Total Views", f"{rt['Views'].sum():,}")
col3.metric("Total Likes", f"{rt['Likes'].sum():,}")
col4.metric("Total Comments", f"{rt['Comments'].sum():,}")

# Show raw data
with st.expander("🧾 See Raw Data"):
    st.dataframe(rt)

# Plot 1: Views vs Likes
st.subheader("🔥 Views vs Likes")
fig1, ax1 = plt.subplots()
sns.scatterplot(data=rt, x="Views", y="Likes", hue="Cluster", palette="tab10", ax=ax1)
plt.xscale("log")
plt.yscale("log")
st.pyplot(fig1)

# Plot 2: Cluster distribution
st.subheader("🎯 Cluster Distribution")
fig2, ax2 = plt.subplots()
sns.countplot(data=rt, x="Cluster", palette="Set2", ax=ax2)
st.pyplot(fig2)

# Plot 3: Uploads over time
st.subheader("📅 Upload Trend Over Time")
rt['UploadDate'] = pd.to_datetime(rt['UploadDate'])
rt['YearMonth'] = rt['UploadDate'].dt.to_period('M').astype(str)
monthly = rt.groupby('YearMonth').size().reset_index(name='Uploads')

fig3, ax3 = plt.subplots()
sns.lineplot(data=monthly, x='YearMonth', y='Uploads', marker='o', ax=ax3)
plt.xticks(rotation=45)
st.pyplot(fig3)

# Plot 4: Engagement per cluster
st.subheader("📈 Engagement by Cluster")
engage_df = rt.groupby('Cluster')[['Views', 'Likes', 'Comments']].mean().reset_index()

fig4, ax4 = plt.subplots()
engage_df.plot(kind='bar', x='Cluster', ax=ax4)
plt.title("Avg Engagement per Cluster")
st.pyplot(fig4)

st.markdown("💡 *Built with Streamlit. Data collected using YouTube Data API.*")
