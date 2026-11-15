
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# Database path
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "college.db"

# Page configuration
st.set_page_config(
    page_title="QueryMind",
    page_icon="🧠",
    layout="wide"
)

# Connect to database
def get_connection():
    return sqlite3.connect(DB_PATH)

# Fetch database tables
def get_tables():
    conn = get_connection()
    query = """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name NOT LIKE 'sqlite_%'
    """
    tables = pd.read_sql_query(query, conn)
    conn.close()
    return tables["name"].tolist()

# Fetch table data
def get_table_data(table_name):
    conn = get_connection()
    data = pd.read_sql_query(
        f'SELECT * FROM "{table_name}" LIMIT 10',
        conn
    )
    conn.close()
    return data


# -------------------------
# APPLICATION INTERFACE
# -------------------------

st.title("🧠 QueryMind")
st.subheader("Your AI-powered Data Assistant")

st.write(
    "Ask questions about your database in plain English. "
    "QueryMind will convert your questions into SQL."
)

st.divider()

# Sidebar
st.sidebar.title("Database Explorer")
st.sidebar.success("Database Connected")

tables = get_tables()

st.sidebar.write("Available Tables")

for table in tables:
    st.sidebar.write(f"📋 {table}")

# Main dashboard
st.header("Explore Your Data")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Database Tables", len(tables))

with col2:
    conn = get_connection()
    count = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM students", conn
    ).iloc[0]["total"]
    conn.close()
    st.metric("Total Students", count)

with col3:
    st.metric("AI Status", "Not Connected")

st.divider()

# Question input
st.header("Ask Your Database")

question = st.text_area(
    "Enter your question:",
    placeholder="Example: Show the top 5 students by marks",
    height=100
)

if st.button("Generate SQL", type="primary"):
    if question.strip():
        st.info(
            "Your question has been received. "
            "AI integration is our next development step."
        )
    else:
        st.warning("Please enter a question first.")

st.divider()

# Database preview
st.header("Database Preview")

selected_table = st.selectbox(
    "Select a table to preview:",
    tables
)

if selected_table:
    st.dataframe(
        get_table_data(selected_table),
        use_container_width=True
    )

st.caption("QueryMind | Text-to-SQL Project")
