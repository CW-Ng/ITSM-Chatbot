import streamlit as st
import pandas as pd
import tempfile

# Setup ephemeral database once per session
if "chroma_dir" not in st.session_state:
    st.session_state.chroma_dir = tempfile.mkdtemp()

from logics.collection_handler import viewAllIssues, addMultipleIssues,queryCollection,addIssue

# ---------------------------
# Streamlit UI
# ---------------------------


# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="wide",
    page_title="ITSM RAG Bot"
)
# endregion <--------- Streamlit App Configuration --------->

# -----------------------------
# HARD-CODED USERS (username: password + role)
# -----------------------------
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}

# -----------------------------
# FUNCTION TO HIDE SIDEBAR
# -----------------------------
def hide_sidebar():
    hide_style = """
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)

# -----------------------------
# LOGIN PAGE
# -----------------------------
def login_page():
    hide_sidebar()  # Hide sidebar on login page
    st.title("🔐 Login")
    st.write("Enter your credentials to access the dashboard.")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.success(f"Login successful! Welcome {username}")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")


# ---------------------------
# Start of UI Page
# ---------------------------


# ---------------------------
# Add Single Issue-Resolution Pair
# ---------------------------
def addIssue_page():
    if st.session_state.role != "admin":
        st.error("⛔ Access denied: Admins only.")
        return

    st.subheader("Add an ITSM Issue and Resolution")
    issue = st.text_input("Issue")
    resolution = st.text_area("Resolution")
    if st.button("Add to KB"):
        if not issue or not resolution:
            st.warning("Please enter both Issue and Resolution")
        else:
            addIssue(issue,resolution)
            st.success("✅ Issue-Resolution pair added to knowledge base!")

# -----------------------------
# Bulk Upload CSV
# -----------------------------
def uploadCSV_page():
    if st.session_state.role != "admin":
        st.error("⛔ Access denied: Admins only.")
        return

    st.subheader("Bulk Upload Issue-Resolution CSV")
    uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"])
    
    if uploaded_csv:
        df = pd.read_csv(uploaded_csv)
        if 'issue' not in df.columns or 'resolution' not in df.columns:
            st.error("CSV must have 'issue' and 'resolution' columns")
        else:
            st.info(f"Processing {len(df)} entries...")
            addMultipleIssues(df) 
            st.success(f"✅ Added {len(df)} issue-resolution pairs to persistent KB!")

# -----------------------------
# View All 
# -----------------------------
def viewAll_page():
    st.subheader("View All Issue-Resolution Pairs")
    list_of_pairs = viewAllIssues()
    if len(list_of_pairs) > 0:
        df = pd.DataFrame(list_of_pairs)
        df
    else:
        st.info("No issue-resolution pairs stored yet.")


# ---------------------------
# 4. LLM-based Q&A (RAG)
# ---------------------------
def askQns_page():
    st.subheader("Tell me about your issue")
    user_question = st.text_input("Question")
    if user_question:
        results, answer = queryCollection (user_question)
        if not results["documents"]:
            st.warning("No relevant issues found.")
        else:
            st.subheader("💡 Answer")
            st.write(answer)
            st.write("### 📚 Context Used")
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                st.write(f"- `{doc}`")

# -----------------------------
# HOME PAGE
# -----------------------------
def home_page():
    st.title("🤖 ITSM RAG Bot")
    st.write(f"Welcome **{st.session_state.username}**!")

    # Sidebar
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

    # Manual page navigation
    pages = ["Tell me about your issue"]
    pages.append("View all issues and resolutions")
    if st.session_state.role == "admin":
        pages.append("Add new ITSM issue with resolution")
        pages.append("Upload CSV")
        
    page = st.sidebar.radio("Go to page:", pages)

    # Page content
    if page == "Tell me about your issue":
        askQns_page()
    elif page == "View all issues and resolutions":
        viewAll_page()
    elif page == "Add new ITSM issue with resolution":
        addIssue_page()
    elif page == "Upload CSV":
        uploadCSV_page()


# ---------------------------
# End of UI Page
# ---------------------------

# -----------------------------
# MAIN APP CONTROL
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    home_page()
else:
    login_page()