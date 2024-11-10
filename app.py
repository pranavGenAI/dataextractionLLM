import streamlit as st
import PIL.Image
import google.generativeai as genai
import time
import hashlib
import json
from uuid import uuid4  # To generate unique IDs for each case

# Set page title, icon, and dark theme
st.set_page_config(page_title="State Release Data Extraction", page_icon=">", layout="wide")

# CSS for styling
st.markdown(
    """
    <style>
    .stButton button {
        background: linear-gradient(120deg,#FF007F, #A020F0 100%) !important;
        color: white !important;
    }
    body {
        color: white;
        background-color: #1E1E1E;
    }
    .stTextInput, .stSelectbox, .stTextArea, .stFileUploader {
        color: white;
        background-color: #2E2E2E;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "document_queue" not in st.session_state:
    st.session_state.document_queue = {}
if "validated_queue" not in st.session_state:
    st.session_state.validated_queue = {}

# Configure Google Generative AI with the API key
# GOOGLE_API_KEY = st.secrets['GEMINI_API_KEY']
GOOGLE_API_KEY = "AIzaSyCiPGxwD04JwxifewrYiqzufyd25VjKBkw"
genai.configure(api_key=GOOGLE_API_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Define users and hashed passwords
users = {
    "ankur.d.shrivastav": hash_password("ankur123"),
    "sashank.vaibhav.allu": hash_password("sashank123"),
    "shivananda.mallya": hash_password("shiv123"),
    "pranav.baviskar": hash_password("pranav123")
}

def login():
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        st.title("Login")
        username = st.text_input("Username", label_visibility="collapsed")
        password = st.text_input("Password", type="password", label_visibility="collapsed")
        
        if st.button("Sign in"):
            hashed_password = hash_password(password)
            if username in users and users[username] == hashed_password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Logged out successfully!")
    st.rerun()

# Function to generate content from the image using Generative AI
def generate_content(image):
    max_retries = 10
    delay = 10
    retry_count = 0
    while retry_count < max_retries:
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            prompt = """extract all information in Marathi """
            response = model.generate_content([prompt, image], stream=True)
            response.resolve()
            return response.text
        except Exception:
            retry_count += 1
            if retry_count == max_retries:
                st.error("Error generating content: Server not available. Please try again later.")
            time.sleep(delay)
    return None

def add_to_queue(image, extracted_data):
    # Generate a unique ID for each document
    unique_id = str(uuid4())
    # Add to document queue
    st.session_state.document_queue[unique_id] = {
        "image": image,
        "extracted_data": extracted_data
    }
    st.success(f"Document added to queue with ID: {unique_id}")

def main():
    st.title("State Release Data Extraction")

    # Create tabs for Document Queue and Validated Queue
    tab1, tab2 = st.tabs(["Document Queue", "Validated Queue"])

    # Document Queue tab
    with tab1:
        st.subheader("Upload Document")
        uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

        if uploaded_image:
            image = PIL.Image.open(uploaded_image)
            if st.button("Extract and Add to Queue"):
                with st.spinner("Extracting data..."):
                    extracted_data = generate_content(image)
                    if extracted_data:
                        st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
                        st.text(extracted_data)
                        add_to_queue(image, extracted_data)
                    else:
                        st.error("Failed to extract data. Please try again.")

        st.subheader("Document Queue")
        for doc_id, doc_info in st.session_state.document_queue.items():
            if st.button(f"View Document {doc_id}"):
                st.image(doc_info["image"], caption=f"Document ID: {doc_id}", use_column_width=True)
                st.text(doc_info["extracted_data"])

    # Validated Queue tab
    with tab2:
        st.subheader("Validated Documents")
        if st.session_state.validated_queue:
            for doc_id, doc_info in st.session_state.validated_queue.items():
                if st.button(f"View Validated Document {doc_id}"):
                    st.image(doc_info["image"], caption=f"Validated Document ID: {doc_id}", use_column_width=True)
                    st.text(doc_info["extracted_data"])
        else:
            st.write("No validated documents available.")

if __name__ == "__main__":
    if st.session_state.logged_in:
        col1, col2, col3 = st.columns([10, 10, 1.5])
        with col3:
            if st.button("Logout"):
                logout()
        main()
    else:
        login()

# Custom CSS for header and layout
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Graphik:wght@400;700&display=swap');

    body {
        background-color: #f0f0f0;
        color: black;
        font-family: 'Graphik', sans-serif;
    }
    .stApp {
        background-color: #f0f0f0;
    }
    header {
        background-color: #660094 !important;
        padding: 10px 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .logo {
        height: 30px;
        width: auto;
    }
    .generated-text-box {
        border: 3px solid #A020F0;
        padding: 20px;
        border-radius: 10px;
        background-color: #FFFFFF;
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header with logo
st.markdown(
    """
    <header tabindex="-1" data-testid="stHeader">
        <div class="header-content">
            <img src="https://www.vgen.it/wp-content/uploads/2021/04/logo-accenture-ludo.png" class="logo" alt="Logo">
        </div>
    </header>
    """,
    unsafe_allow_html=True
)
