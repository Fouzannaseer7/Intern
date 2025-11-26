import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 🧩 Page Setup
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="centered")

st.title("🎬 Movie Recommendation System")
st.markdown("Discover movies similar to your favorites!")

# 📂 Load Dataset
def load_data():
    try:
        df = pd.read_csv("movies.csv", encoding="latin1")
    except UnicodeDecodeError:
        df = pd.read_csv("movies.csv", encoding="utf-8", errors="ignore")

    # Ensure required columns exist
    expected_cols = {"Title", "Genre", "Overview"}
    if not expected_cols.issubset(df.columns):
        st.error("❌ CSV must contain columns: Title, Genre, and Overview")
        st.stop()

    # Fill missing values
    df['Genre'] = df['Genre'].fillna("")
    df['Overview'] = df['Overview'].fillna("")

    # Combine into one text field
    df['Combined'] = df['Genre'] + " " + df['Overview']

    # Remove empty text rows
    df = df[df['Combined'].str.strip() != ""]

    if df.empty:
        st.error("❌ Dataset is empty or has invalid text data.")
        st.stop()

    return df


# 🔍 Prepare Model
def create_model(df):
    vectorizer = TfidfVectorizer(stop_words='english')

    # Validate input
    if df['Combined'].isnull().all() or df['Combined'].str.strip().eq('').all():
        st.error("❌ No valid text found in dataset. Check your CSV.")
        st.stop()

    tfidf_matrix = vectorizer.fit_transform(df['Combined'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    return vectorizer, cosine_sim


# 🎥 Recommendation Function
def recommend_movie(title, df, cosine_sim):
    if title not in df['Title'].values:
        return None

    idx = df.index[df['Title'] == title][0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    top_movies = sim_scores[1:6]
    return df.iloc[[i for i, _ in top_movies]][['Title', 'Genre', 'Overview']]


# 🚀 Main App
df = load_data()
vectorizer, cosine_sim = create_model(df)

movie_list = df['Title'].tolist()
selected_movie = st.selectbox("🎞️ Select a movie:", movie_list)

if st.button("Get Recommendations"):
    recs = recommend_movie(selected_movie, df, cosine_sim)
    if recs is not None and not recs.empty:
        st.success(f"Movies similar to **{selected_movie}**:")
        for _, row in recs.iterrows():
            st.subheader(f"🎬 {row['Title']} ({row['Genre']})")
            st.write(row['Overview'])
            st.markdown("---")
    else:
        st.error("No recommendations found.")
