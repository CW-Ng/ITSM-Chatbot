import streamlit as st
import pandas as pd
import tempfile

# Setup ephemeral database once per session
if "chroma_dir" not in st.session_state:
    st.session_state.chroma_dir = tempfile.mkdtemp()

from logics.collection_handler import viewAllIssues, addMultipleIssues,queryCollection,addIssue,initCollection

load_csv = "./data/IT_Issues_50_1stLoad.csv"


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
# Query page
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

# ---------------------------
# About Us page
# ---------------------------
def abtUs_page():
    st.subheader("About Us")
    
    with st.expander("Project scope",True):
        st.write("This project involves developing and deploying an intelligent ITSM chatbot powered by Retrieval-Augmented Generation (RAG) technology. The RAG bot will leverage historical ticket data to provide accurate, contextually relevant responses to user query.")
    with st.expander("Objectives",True):
        st.write("The primary objective is to create an AI-powered RAG system that can intelligently search through vector database to provide precise answers to user queries. The bot will leverage on the power of large language models to ensure responses are accurate.")
    with st.expander("Data sources",True):
        st.write("For this PoC purpose, 50 common IT issue and their resolution was generated and imported into the database on first load.")
    with st.expander("Features",True):
        st.write("1. In the event where the Bot is unable to find suitable historical ticket in relation to the user query, the bot will leverage the power of LLM to provide recommended solution.")
        st.write("2. Admin will have the flexibility to bulk import a list of historical ticket data into the database or to insert single records")

        

# ---------------------------
# Methodology page
# ---------------------------
def showMethodology_page():
    st.subheader("Methodology")
    # Create some sample data
    load_data = {
        'Steps': ['1. Gather Resolved Tickets', '2. Convert to Code', '3. Store & Index'],
        'Action': ['Either export all resolved tickets into CSV file or enter manually using [Add new ITSM issue with resolution]', 'Create embeddings.', 'Store the vectors in a database.'],
        'Explaination': [
            'Provide data by either exporting resolved tickets into CSV file or manually entering each solution', 
            'Use the Embedding Model to generate a numerical vector for each "Issue" and "Resolution" text pair.', 
            'Load the numerical vectors into a Vector Database designed for high-speed similarity search, enabling instant matching of new questions to historical solutions.']
    }

    rag_data = {
        'Steps': ['1. New Query', '2. Instant Search', '3. Retrieve Context', '4. Generate Answer','5. Response to user'],
        'Action': ['An user submits asks a question.', 'Convert the query and search the index.', 'Select the best matches.','Prompt the LLM with context.','The LLM generates the final output.'],
        'Explaination': [
            'User input a query in the system', 
            'The system converts the query into a numerical vector. It then searches the Vector Database', 
            'The system finds the top 5 past tickets where it matches query', 
            'Using the top 5 tickets as context, the system will prompt the LLM for response', 
            'The system display the response from the LLM as well as the context (top 5 past tickets)']
    }

    df_load_data = pd.DataFrame(load_data)
    df_rag_data = pd.DataFrame(rag_data)
    with st.expander("Loading of data",False):
        st.write("When the application first start, a basic set of resolved tickets will automatically load into a temporary database.")
        st.write("Users can look at the existing data and search the knowledge base, but they cannot add any new records (tickets or solutions).")
        st.write("Admins are the only ones who can add new solutions. They have two ways to do this:")
        st.write("1. Use the [Add new ITSM issue with resolution] function to manually input a solution.")
        st.write("2. Upload a CSV file that contains only two columns: ""Issue"" and the corresponding ""Resolution"".")
        st.dataframe(df_load_data, hide_index=True)
    
    with st.expander("Query",False):
        st.write("User will enter their question in the system")
        st.write("The system will searches through the vector database to find top 5 tickets that resemble the question the most")
        st.write("Using the top 5 tickets as context, the system will craft the response back to the user")
        st.dataframe(df_rag_data, hide_index=True)
    with st.expander("Flow Chart",False):
        st.write("Process flow for application use cases")
        st.image('./images/FlowChart.png', caption='Flow Chart', width=760)
    
 

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
    pages.append("Methodology")
    pages.append("About Us")    
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
    elif page == "About Us":
        abtUs_page()
    elif page == "Methodology":
        showMethodology_page()
    


# ---------------------------
# End of UI Page
# ---------------------------

# -----------------------------
# MAIN APP CONTROL
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    initCollection(pd.read_csv(load_csv))
    home_page()
else:
    login_page()