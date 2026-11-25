
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib

from pathlib import Path
from core.query_pipeline import ask_database
from core.sql_explainer import explain_sql
from core.insight_engine import generate_insights
from core.what_if_analysis import run_what_if

CHART_COLORS = [
    "#2563EB",
    "#7C3AED",
    "#0891B2",
    "#059669",
    "#EA580C",
    "#DC2626",
    "#DB2777",
]


# --------------------------------------------------
# PATHS AND CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DB = BASE_DIR / "data" / "college.db"
UPLOAD_DIR = BASE_DIR / "data" / "user_uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="QueryMind | Data Workspace",
    page_icon="Q",
    layout="wide"
)


# --------------------------------------------------
# PROFESSIONAL LIGHT THEME
# --------------------------------------------------

st.markdown("""

<style>

/* ===== MAIN BACKGROUND ===== */

.stApp {
    background-color: #0B1730;
    color: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.block-container {
    max-width: 1200px;
    padding: 5rem 2.5rem 3rem !important;
    margin-top: 0 !important;
}

/* HEADER */

header[data-testid="stHeader"] {
    background-color: #0B1730 !important;
    height: 3.5rem !important;
    z-index: 999;
}

div[data-testid="stToolbar"] {
    background-color: #0B1730 !important;
}

section[data-testid="stMain"] {
    background-color: #0B1730 !important;
}

/* TEXT */

h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

p, label, li,
.stMarkdown,
.stText,
[data-testid="stCaptionContainer"] {
    color: #D8E9FF !important;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background-color: #102344;
    border-right: 1px solid #28528A;
    width: 260px !important;
    min-width: 260px !important;
    max-width: 260px !important;
}

/* BRAND */

.brand-label {
    color: #75B5FF !important;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

/* METRIC CARDS */

div[data-testid="stMetric"] {
    background-color: #17345B;
    border: 1px solid #28528A;
    border-radius: 10px;
    padding: 16px 18px;
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] * {
    color: #D8E9FF !important;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] * {
    color: #FFFFFF !important;
}

/* TEXT INPUTS */

.stTextInput input,
.stTextArea textarea {
    background-color: #102849 !important;
    color: #FFFFFF !important;
    border: 1px solid #477CB8 !important;
    border-radius: 8px !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #B8D4F0 !important;
    opacity: 1 !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border: 1px solid #4595FF !important;
    box-shadow: 0 0 0 1px #4595FF !important;
}

/* SELECT BOXES */

div[data-baseweb="select"] > div {
    background-color: #102849 !important;
    border: 1px solid #477CB8 !important;
    color: #FFFFFF !important;
}

div[data-baseweb="select"] * {
    color: #FFFFFF !important;
}

ul[data-testid="stSelectboxVirtualDropdown"] {
    background-color: #17345B !important;
}

[role="option"] {
    background-color: #17345B !important;
    color: #FFFFFF !important;
}

/* BUTTONS */

div.stButton > button,
div.stDownloadButton > button {
    background-color: #2878E8 !important;
    color: #FFFFFF !important;
    border: 1px solid #4595FF !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    min-height: 42px;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    background-color: #4595FF !important;
    border-color: #75B5FF !important;
    color: #FFFFFF !important;
}

/* FILE UPLOADER */

div[data-testid="stFileUploader"] {
    background-color: #17345B !important;
    border: 1px dashed #75B5FF !important;
    border-radius: 9px;
    padding: 12px;
}

div[data-testid="stFileUploader"] * {
    color: #FFFFFF !important;
}

/* DATA TABLES */

div[data-testid="stDataFrame"] {
    background-color: #102849 !important;
    border: 1px solid #28528A !important;
    border-radius: 9px;
    overflow: hidden;
}

/* SQL CODE AND RESULTS */

div[data-testid="stCode"],
pre,
code {
    color: #FFFFFF !important;
}

/* ALERTS */

div[data-testid="stAlert"] {
    background-color: #17345B !important;
    border: 1px solid #477CB8 !important;
    border-radius: 8px;
}

div[data-testid="stAlert"] * {
    color: #FFFFFF !important;
}

/* EXPANDERS */

div[data-testid="stExpander"] {
    background-color: #17345B;
    border: 1px solid #28528A;
    border-radius: 8px;
}

div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary * {
    color: #FFFFFF !important;
}

/* CHECKBOXES AND RADIO BUTTONS */

.stCheckbox label,
.stRadio label {
    color: #FFFFFF !important;
}

/* DIVIDERS */

hr {
    border-color: #28528A !important;
}

/* RESPONSIVE */

@media (max-width: 768px) {
    .block-container {
        padding: 1rem;
    }

    h1 {
        font-size: 1.7rem !important;
    }
}

</style>

""", unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {
    "db_path": str(SAMPLE_DB.resolve()),
    "db_name": "Sample college database",
    "query_history": [],
    "clarification_question": None,
    "original_question": None,
    "last_sql": None,
    "last_result": None,
    "last_status": None,
    "last_question": None,
    "performance": None,
    "conversation_history": [],
    "conversation_db_path": str(SAMPLE_DB.resolve()),
    "pending_clarification": None,
    "sql_explanation": None,
    "ai_insights": None,
    "what_if_result": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------

def validate_database(db_path):
    try:
        connection = sqlite3.connect(
            Path(db_path).resolve().as_uri() + "?mode=ro",
            uri=True
        )

        cursor = connection.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """)

        tables = cursor.fetchall()
        connection.close()

        return len(tables) > 0

    except Exception:
        return False


def get_connection(db_path):
    return sqlite3.connect(
        Path(db_path).resolve().as_uri() + "?mode=ro",
        uri=True
    )


def get_tables(db_path):
    connection = get_connection(db_path)

    try:
        query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """

        tables = pd.read_sql_query(query, connection)

        return tables["name"].tolist()

    finally:
        connection.close()


def get_table_data(db_path, table_name):
    connection = get_connection(db_path)

    try:
        safe_name = table_name.replace('"', '""')

        data = pd.read_sql_query(
            f'SELECT * FROM "{safe_name}" LIMIT 100',
            connection
        )

        return data

    finally:
        connection.close()


def get_total_rows(db_path, tables):
    connection = get_connection(db_path)

    try:
        total = 0

        for table in tables:
            safe_name = table.replace('"', '""')

            cursor = connection.cursor()
            cursor.execute(f'SELECT COUNT(*) FROM "{safe_name}"')

            total += cursor.fetchone()[0]

        return total

    finally:
        connection.close()


# --------------------------------------------------
# RESULT ANALYSIS AND CHART HELPERS
# --------------------------------------------------

def explain_result(data):
    """Generate a quick explanation without another Gemini call."""

    if data.empty:
        return "The query returned no records."

    rows, columns = data.shape

    explanation = [
        f"Your query returned **{rows:,} rows** across **{columns} columns**."
    ]

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        exclude="number"
    ).columns.tolist()

    if numeric_columns:
        for column in numeric_columns[:2]:
            values = pd.to_numeric(
                data[column], errors="coerce"
            ).dropna()

            if not values.empty:
                explanation.append(
                    f"**{column}:** minimum {values.min():,.2f}, "
                    f"maximum {values.max():,.2f}, "
                    f"average {values.mean():,.2f}."
                )

    if categorical_columns:
        column = categorical_columns[0]
        counts = data[column].value_counts()

        if not counts.empty:
            explanation.append(
                f"**Most frequent {column}:** "
                f"{counts.index[0]} ({counts.iloc[0]} records)."
            )

    return "\n\n".join(explanation)


def detect_date_columns(data):
    """Identify columns containing date-like values."""

    date_columns = []

    for column in data.columns:
        name = str(column).lower()

        if any(word in name for word in ["date", "time", "year"]):
            parsed = pd.to_datetime(
                data[column], errors="coerce"
            )

            if parsed.notna().sum() >= max(1, len(data) * 0.5):
                date_columns.append(column)

    return date_columns


def choose_chart(data):
    """Choose a suitable default chart based on result columns."""

    numeric = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical = data.select_dtypes(
        exclude="number"
    ).columns.tolist()

    dates = detect_date_columns(data)

    if not numeric:
        return None, None, None

    if dates:
        return "Line", dates[0], numeric[0]

    if categorical:
        category = categorical[0]

        if data[category].nunique() <= 8:
            return "Pie", category, numeric[0]

        return "Bar", category, numeric[0]

    if len(numeric) >= 2:
        return "Scatter", numeric[0], numeric[1]

    return "Histogram", numeric[0], None


def create_chart(data, chart_type, x_column, y_column):

    if chart_type == "Bar":
        fig = px.bar(
            data,
            x=x_column,
            y=y_column,
            title=f"{y_column} by {x_column}",
            template="plotly_white",
            color_discrete_sequence=CHART_COLORS
        )

    elif chart_type == "Line":
        fig = px.line(
            data,
            x=x_column,
            y=y_column,
            title=f"{y_column} over {x_column}",
            markers=True,
            template="plotly_white",
            color_discrete_sequence=CHART_COLORS
        )

    elif chart_type == "Pie":
        fig = px.pie(
            data,
            names=x_column,
            values=y_column,
            title=f"{y_column} distribution",
            template="plotly_white",
            color_discrete_sequence=CHART_COLORS
        )

    elif chart_type == "Scatter":
        fig = px.scatter(
            data,
            x=x_column,
            y=y_column,
            title=f"{y_column} vs {x_column}",
            template="plotly_white",
            color_discrete_sequence=CHART_COLORS
        )

    elif chart_type == "Histogram":
        fig = px.histogram(
            data,
            x=x_column,
            title=f"Distribution of {x_column}",
            template="plotly_white",
            color_discrete_sequence=CHART_COLORS
        )

    else:
        return None

    fig.update_layout(
        font=dict(color="#1E293B"),
        title_font=dict(size=20, color="#0F172A"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        xaxis=dict(
            title_font=dict(color="#334155"),
            tickfont=dict(color="#334155"),
            gridcolor="#E2E8F0"
        ),
        yaxis=dict(
            title_font=dict(color="#334155"),
            tickfont=dict(color="#334155"),
            gridcolor="#E2E8F0"
        )
    )

    return fig


# --------------------------------------------------
# UPLOAD DATABASE
# --------------------------------------------------

st.sidebar.markdown(
    '<div class="brand-label">QUERYMIND</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown("## Database workspace")

st.sidebar.caption(
    "Connect your own SQLite database to start exploring."
)

uploaded_file = st.sidebar.file_uploader(
    "Upload a SQLite database",
    type=["db", "sqlite", "sqlite3"]
)

if uploaded_file is not None:

    file_bytes = uploaded_file.getvalue()

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    extension = Path(uploaded_file.name).suffix.lower()

    uploaded_path = UPLOAD_DIR / f"{file_hash}{extension}"

    if not uploaded_path.exists():
        uploaded_path.write_bytes(file_bytes)

    if validate_database(uploaded_path):

        st.session_state.db_path = str(uploaded_path.resolve())
        st.session_state.db_name = uploaded_file.name

    else:
        st.sidebar.error(
            "Invalid database or no tables found."
        )

        st.session_state.db_path = str(SAMPLE_DB.resolve())
        st.session_state.db_name = "Sample college database"


# --------------------------------------------------
# ACTIVE DATABASE AND DATABASE-SWITCH RESET
# --------------------------------------------------

db_path = st.session_state.db_path

if st.session_state.conversation_db_path != db_path:

    st.session_state.conversation_history = []
    st.session_state.query_history = []
    st.session_state.clarification_question = None
    st.session_state.original_question = None
    st.session_state.pending_clarification = None
    st.session_state.last_sql = None
    st.session_state.last_result = None
    st.session_state.last_status = None
    st.session_state.last_question = None
    st.session_state.performance = None
    st.session_state.sql_explanation = None
    st.session_state.ai_insights = None
    st.session_state.what_if_result = None
    st.session_state.conversation_db_path = db_path


if not Path(db_path).exists():
    db_path = str(SAMPLE_DB.resolve())
    st.session_state.db_path = db_path
    st.session_state.db_name = "Sample college database"


if not validate_database(db_path):
    st.error("The selected database could not be opened.")
    st.stop()


try:
    tables = get_tables(db_path)
    total_rows = get_total_rows(db_path, tables)

except Exception as error:
    st.error(f"Database error: {error}")
    st.stop()


st.sidebar.success(
    f"Connected: {st.session_state.db_name}"
)

st.sidebar.caption(
    f"{len(tables)} tables | {total_rows:,} records"
)


if st.sidebar.button("Use sample database", use_container_width=True):

    st.session_state.db_path = str(SAMPLE_DB.resolve())
    st.session_state.db_name = "Sample college database"

    st.session_state.conversation_history = []
    st.session_state.query_history = []
    st.session_state.clarification_question = None
    st.session_state.original_question = None
    st.session_state.pending_clarification = None
    st.session_state.last_result = None
    st.session_state.last_sql = None
    st.session_state.last_status = None
    st.session_state.last_question = None
    st.session_state.performance = None
    st.session_state.sql_explanation = None
    st.session_state.ai_insights = None
    st.session_state.what_if_result = None
    st.rerun()


# --------------------------------------------------
# QUERY HISTORY
# --------------------------------------------------

st.sidebar.divider()

st.sidebar.markdown("### Query history")

if st.session_state.query_history:

    for item in reversed(st.session_state.query_history[-8:]):

        st.sidebar.caption(item)

else:
    st.sidebar.caption("Your previous queries will appear here.")

    st.sidebar.divider()


if st.sidebar.button(
    "Clear conversation",
    use_container_width=True,
    key="clear_conversation"
):

    st.session_state.conversation_history = []
    st.session_state.query_history = []

    st.session_state.clarification_question = None
    st.session_state.original_question = None

    st.session_state.last_sql = None
    st.session_state.last_result = None
    st.session_state.last_status = None
    st.session_state.last_question = None
    st.session_state.pending_clarification = None
    st.session_state.performance = None
    st.session_state.sql_explanation = None
    st.session_state.ai_insights = None
    st.session_state.what_if_result = None
    st.rerun()


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.markdown(
    '<div class="brand-label">DATA WORKSPACE</div>',
    unsafe_allow_html=True
)

st.title("QueryMind")

st.markdown(
    "Explore your database using natural language. "
    "Generate SQL, retrieve results and discover insights."
)

st.divider()


# --------------------------------------------------
# DASHBOARD METRICS
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Database status", "Connected")

with col2:
    st.metric("Total tables", len(tables))

with col3:
    st.metric("Total records", f"{total_rows:,}")


st.divider()


# --------------------------------------------------
# ASK YOUR DATABASE
# --------------------------------------------------

st.subheader("Ask your database")

st.caption(
    "Describe what you want to find. QueryMind will translate "
    "your question into SQL."
)

question = st.text_input(
    "Your question",
    placeholder="Example: Show the top 5 departments by employee count",
    key="main_question"
)

generate_button = st.button(
    "Generate SQL",
    type="primary",
    use_container_width=True
)


# --------------------------------------------------
# QUERY GENERATION
# --------------------------------------------------

if generate_button:

    if not question.strip():

        st.warning("Please enter a question first.")

    else:

        st.session_state.clarification_question = None
        st.session_state.last_result = None
        st.session_state.last_sql = None
        st.session_state.sql_explanation = None
        st.session_state.ai_insights = None
        st.session_state.what_if_result = None
        st.session_state.original_question = question
        st.session_state.last_question = question

        try:

            with st.spinner("Understanding your question..."):

                response = ask_database(
                    question,
                    db_path,
                    st.session_state.conversation_history
                )

            st.session_state.last_status = response["status"]

            if response["status"] == "clarification":

                clarification_question = response["clarification_question"]

                st.session_state.clarification_question = clarification_question

                # Store the user's question
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": question
                })

                # Store QueryMind's clarification
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": clarification_question
                })

            else:

                st.session_state.last_sql = response["sql"]
                st.session_state.last_result = response["result"]

                # Store conversation
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": question
                })

                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": f"Generated SQL:\n{response['sql']}"
                })

                st.session_state.query_history.append(question)

        except Exception as error:

            st.error(str(error))


# --------------------------------------------------
# CLARIFICATION WORKFLOW
# --------------------------------------------------

if st.session_state.clarification_question:

    st.info("QueryMind needs a little clarification.")

    st.markdown(
        f"**{st.session_state.clarification_question}**"
    )

    clarification = st.text_input(
        "Your clarification",
        placeholder="Type your answer here...",
        key="clarification_input"
    )

    if st.button("Submit clarification"):

        if not clarification.strip():

            st.warning("Please enter your clarification.")

        else:

            combined_question = (
                f"{st.session_state.original_question}\n"
                f"User clarification: {clarification}"
            )

            try:

                with st.spinner("Processing your clarification..."):

                    response = ask_database(
                        combined_question,
                        db_path,
                        st.session_state.conversation_history
                    )

                # Store user's clarification
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": clarification
                })

                if response["status"] == "clarification":

                    st.session_state.clarification_question = (
                        response["clarification_question"]
                    )

                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": response["clarification_question"]
                    })

                else:

                    st.session_state.clarification_question = None

                    st.session_state.last_sql = response["sql"]
                    st.session_state.last_result = response["result"]
                    st.session_state.last_question = combined_question
                    st.session_state.sql_explanation = None
                    st.session_state.ai_insights = None
                    st.session_state.what_if_result = None
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": f"Generated SQL:\n{response['sql']}"
                    })

                    st.session_state.query_history.append(
                        combined_question
                    )

                    st.rerun()

            except Exception as error:

                st.error(str(error))


# --------------------------------------------------
# SQL OUTPUT AND AI EXPLANATION
# --------------------------------------------------

if st.session_state.last_sql:

    st.divider()

    st.subheader("Generated SQL")

    st.code(
        st.session_state.last_sql,
        language="sql"
    )

    # --------------------------------------------------
    # AI SQL EXPLANATION
    # --------------------------------------------------

    st.subheader("SQL Explanation & Breakdown")

    st.caption(
        "Understand how QueryMind's generated SQL query works."
    )

    if st.button(
        "Explain this SQL",
        type="primary",
        use_container_width=True,
        key="explain_sql_button"
    ):

        try:

            with st.spinner("Analyzing your SQL query..."):

                st.session_state.sql_explanation = explain_sql(
                    st.session_state.last_question or "",
                    st.session_state.last_sql
                )

        except Exception as error:

            st.session_state.sql_explanation = None

            st.session_state.ai_insights = None

            st.session_state.what_if_result = None
            st.error(
                f"Could not generate SQL explanation: {error}"
            )

    explanation = st.session_state.sql_explanation

    if explanation:

        st.markdown("### 1. Query Overview")
        st.write(explanation["overview"])

        st.divider()

        st.markdown("### 2. Clause-by-Clause Breakdown")

        for clause in explanation["clauses"]:

            with st.expander(
                clause["name"],
                expanded=True
            ):

                st.write(clause["explanation"])

        if explanation["functions"]:

            st.divider()
            st.markdown("### 3. SQL Functions")

            for function in explanation["functions"]:

                st.markdown(f"**{function['name']}**")
                st.write(function["explanation"])

        st.divider()
        st.markdown("### 4. Query Execution Flow")

        for index, step in enumerate(
            explanation["execution_flow"],
            start=1
        ):

            st.markdown(f"**Step {index}:** {step}")

        st.divider()
        st.markdown("### 5. How This Answers Your Question")
        st.write(explanation["how_it_answers"])


# --------------------------------------------------
# QUERY RESULTS, EXPLANATION AND VISUALIZATIONS
# --------------------------------------------------

if st.session_state.last_result is not None:

    result = st.session_state.last_result

    st.subheader("Query results")

    if result.empty:

        st.info("The query returned no records.")

    else:

        st.caption(f"{len(result):,} rows returned")

        # --------------------------------------------------
        # DISPLAY RESULTS
        # --------------------------------------------------

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------------------
        # CSV EXPORT
        # --------------------------------------------------

        csv_data = result.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download results as CSV",
            data=csv_data,
            file_name="querymind_results.csv",
            mime="text/csv",
            key="download_csv"
        )

        # --------------------------------------------------
        # RESULT EXPLANATION
        # --------------------------------------------------

        st.divider()
        st.subheader("Understanding your results")

        explanation = explain_result(result)

        st.markdown(explanation)

        # --------------------------------------------------
        # AI INSIGHT ENGINE
        # --------------------------------------------------

        st.divider()
        st.subheader("AI Insight Engine")

        st.caption(
            "Discover meaningful patterns, comparisons and unusual values "
            "in your query results."
        )

        if st.button(
            "Generate AI Insights",
            type="primary",
            use_container_width=True,
            key="generate_ai_insights"
        ):

            try:

                with st.spinner("Analysing your query results..."):

                    st.session_state.ai_insights = generate_insights(
                        st.session_state.last_question or "",
                        st.session_state.last_sql or "",
                        result
                    )

            except Exception as error:

                st.session_state.ai_insights = None

                st.session_state.what_if_result = None
                st.error(f"Could not generate AI insights: {error}")

        ai_insights = st.session_state.ai_insights

        if ai_insights:

            st.markdown("### Overall summary")
            st.write(ai_insights["overall_summary"])

            st.markdown("### Key findings")

            for index, insight in enumerate(ai_insights["insights"], start=1):

                with st.container(border=True):

                    st.markdown(f"**{index}. {insight['title']}**")

                    st.caption(insight["type"].replace("_", " ").title())

                    st.write(insight["observation"])

                    if insight.get("evidence"):
                        st.caption(f"Evidence: {insight['evidence']}")

                    if insight.get("recommendation"):
                        st.markdown("**Suggested action**")
                        st.write(insight["recommendation"])

            if ai_insights.get("caveats"):
                st.caption(f"Data limitations: {ai_insights['caveats']}")

        # --------------------------------------------------
        # WHAT-IF ANALYSIS
        # --------------------------------------------------

        st.divider()
        st.subheader("What-If Analysis")

        st.caption(
            "Test hypothetical changes on a copy of your query results. "
            "Your database and original query results will not be modified."
        )

        st.info(
            "For student-level scenarios, first run a query that returns "
            "one row per student and a numeric percentage column. "
            "For example: Show each student's overall attendance percentage."
        )

        what_if_scenario = st.text_area(
            "Describe your hypothetical scenario",
            placeholder=(
                "Example: What happens to average attendance if every student "
                "below 60% improves by 10 percentage points?"
            ),
            key="what_if_scenario_input",
            height=100
        )

        if st.button(
            "Run What-If Simulation",
            type="primary",
            use_container_width=True,
            key="run_what_if_simulation"
        ):

            try:

                with st.spinner("Simulating your scenario..."):

                    st.session_state.what_if_result = run_what_if(
                        what_if_scenario,
                        result
                    )

            except Exception as error:

                st.session_state.what_if_result = None
                st.error(f"Could not run the simulation: {error}")

        what_if_result = st.session_state.what_if_result

        if what_if_result:

            st.markdown("### Simulation results")
            st.write(what_if_result["interpretation"])

            metric_one, metric_two, metric_three = st.columns(3)

            metric_one.metric(
                "Original average",
                f"{what_if_result['original_average']:.2f}%"
            )

            metric_two.metric(
                "Simulated average",
                f"{what_if_result['simulated_average']:.2f}%",
                delta=f"{what_if_result['average_change']:+.2f} percentage points"
            )

            metric_three.metric(
                "Rows affected",
                f"{what_if_result['affected_rows']:,} / "
                f"{what_if_result['total_rows']:,}"
            )

            st.caption(
                "Simulation only. No database records were changed. "
                "The average is calculated over non-missing values in the selected result column."
            )

            with st.expander("View original vs simulated values"):

                st.dataframe(
                    what_if_result["comparison_data"],
                    use_container_width=True,
                    hide_index=True
                )

            with st.expander("View simulated dataset"):

                st.dataframe(
                    what_if_result["simulated_data"],
                    use_container_width=True,
                    hide_index=True
                )

        # --------------------------------------------------
        # AUTOMATIC VISUALIZATION
        # --------------------------------------------------

        st.divider()
        st.subheader("Data visualization")

        numeric_columns = result.select_dtypes(
            include="number"
        ).columns.tolist()

        if not numeric_columns:

            st.info(
                "No numeric columns were found. "
                "A chart cannot be generated for this result."
            )

        else:

            default_chart, default_x, default_y = choose_chart(result)

            chart_options = [
                "Bar",
                "Line",
                "Pie",
                "Scatter",
                "Histogram"
            ]

            st.caption(f"Suggested chart: {default_chart}")

            # Chart type selection
            chart_type = st.selectbox(
                "Chart type",
                chart_options,
                index=chart_options.index(default_chart),
                key="chart_type"
            )

            # Select available X-axis columns
            if chart_type in ["Scatter", "Histogram"]:
                x_options = numeric_columns
            else:
                x_options = result.columns.tolist()

            # X-axis selection
            x_index = (
                x_options.index(default_x)
                if default_x in x_options
                else 0
            )

            x_column = st.selectbox(
                "Select X-axis column",
                x_options,
                index=x_index,
                key="chart_x"
            )

            # Y-axis selection
            if chart_type == "Histogram":

                y_column = None

            else:

                y_options = [
                    col for col in numeric_columns
                    if col != x_column
                ]

                if not y_options:
                    y_options = numeric_columns

                y_index = (
                    y_options.index(default_y)
                    if default_y in y_options
                    else 0
                )

                y_column = st.selectbox(
                    "Select Y-axis / Value",
                    y_options,
                    index=y_index,
                    key="chart_y"
                )

            # --------------------------------------------------
            # CREATE AND DISPLAY CHART
            # --------------------------------------------------

            try:

                fig = create_chart(
                    result,
                    chart_type,
                    x_column,
                    y_column
                )

                if fig is not None:

                    fig.update_layout(
                        template="plotly_white",
                        plot_bgcolor="#F1F5F9",
                        paper_bgcolor="#FFFFFF",
                        font=dict(
                            family="Arial",
                            size=13,
                            color="#1E293B"
                        ),
                        title_font=dict(
                            size=21,
                            color="#0F172A"
                        ),
                        margin=dict(
                            l=40,
                            r=40,
                            t=70,
                            b=40
                        ),
                        xaxis=dict(
                            showgrid=True,
                            gridcolor="#CBD5E1",
                            zerolinecolor="#94A3B8"
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor="#CBD5E1",
                            zerolinecolor="#94A3B8"
                        )
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                    # --------------------------------------------------
                    # DOWNLOAD CHART AS PNG
                    # --------------------------------------------------

                    try:

                        image_bytes = fig.to_image(
                            format="png",
                            width=1200,
                            height=700,
                            scale=2
                        )

                        st.download_button(
                            "Download chart as PNG",
                            data=image_bytes,
                            file_name="querymind_chart.png",
                            mime="image/png",
                            key="download_chart"
                        )

                    except Exception as error:

                        st.warning(
                            f"PNG export unavailable: {error}"
                        )

            except Exception as error:

                st.error(
                    f"Could not generate chart: {error}"
                )


# --------------------------------------------------
# DATABASE EXPLORER
# --------------------------------------------------

st.divider()

st.subheader("Database explorer")

st.caption(
    "Browse tables and inspect their records."
)

selected_table = st.selectbox(
    "Select a table",
    tables
)

if selected_table:

    try:

        table_data = get_table_data(
            db_path,
            selected_table
        )

        st.caption(
            f"Previewing {selected_table} — first 100 records"
        )

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True
        )

    except Exception as error:

        st.error(f"Could not load table: {error}")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#8792a5; font-size:13px;">
        QueryMind · Natural Language Database Workspace
    </div>
    """,
    unsafe_allow_html=True
)