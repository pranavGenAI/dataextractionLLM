import streamlit as st
import PIL.Image
import google.generativeai as genai
import time
import hashlib
import json
# Set page title, icon, and dark theme
st.set_page_config(page_title="Insurance Data Extraction", page_icon=">", layout="wide")
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

# Configure Google Generative AI with the API key
#GOOGLE_API_KEY = st.secrets['GEMINI_API_KEY']
GOOGLE_API_KEY = "AIzaSyB1_DTxu2nGB-Av4lwcnFHJaFoshZMCbDM"
genai.configure(api_key=GOOGLE_API_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Define users and hashed passwords for simplicity
users = {
    "ankur.d.shrivastav": hash_password("ankur123"),
    "sashank.vaibhav.allu": hash_password("sashank123"),
    "shivananda.mallya": hash_password("shiv123"),
    "pranav.baviskar": hash_password("pranav123")
}

def login():
    col1, col2= st.columns([0.3, 0.7])  # Create three columns with equal width
    with col1:  # Center the input fields in the middle column
        st.title("Login")
        st.write("Username")
        username = st.text_input("",  label_visibility="collapsed")
        st.write("Password")
        password = st.text_input("", type="password",  label_visibility="collapsed")
        
        if st.button("Sign in"):
            hashed_password = hash_password(password)
            if username in users and users[username] == hashed_password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.rerun()  # Refresh to show logged-in state
            else:
                st.error("Invalid username or password")

def logout():
    # Clear session state on logout
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Logged out successfully!")
    st.rerun()  # Refresh to show logged-out state

# Path to the logo image
logo_url = "https://www.vgen.it/wp-content/uploads/2021/04/logo-accenture-ludo.png"

def generate_content(image):
    max_retries = 10
    delay = 10
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Initialize the GenerativeModel
            print("Model definition")
            model = genai.GenerativeModel('gemini-1.5-pro')
            prompt = """You have been given invoice document as input. Perform the following validations:
            1. Check if invoice date is within COVID period (Jan 2020 to July 2023) if the document is invoice
            2. Check if the department in To is NYS department of health
            3. Extract vendor name
            4. Validate if contractor signature is present
            5. Validate if officer signature is present 
            6. Extract contract start and end date
            """
            # Generate content using the image
            print("Model generate")
            response = model.generate_content([prompt, image], stream=True)
            response.resolve()
            print("Response text", response.text)
            return response.text  # Return generated text
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                st.error(f"Error generating content: Server not available. Please try again after sometime")
            time.sleep(delay)
    
    # Return None if all retries fail
    return None
def main():
    st.title("Invoice Processing")
    col1, col2, col3 = st.columns([4, 1, 4])  # Create three columns

    with col1:
        # Place tabs within col1
        tabs = st.tabs(["Document", "System"])

        # Document tab
        with tabs[0]:  # Only within Document tab
            generated_text = ""
            uploaded_images = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, label_visibility="collapsed")  
            st.markdown(
                """
                <style>
                .st-emotion-cache-fis6aj.e1b2p2ww10 {
                    background-color: #F0F0F0;
                    color: black;                
                }
                body {
                    background-color: white;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Display uploaded images and data extraction button
            if uploaded_images:
                for uploaded_image in uploaded_images:
                    # Convert uploaded image to PIL image object
                    image = PIL.Image.open(uploaded_image)

                    # Button label based on number of images
                    button_label = f"Extract data {uploaded_images.index(uploaded_image) + 1}" if len(uploaded_images) > 1 else "Extract data"

                    # Extract data button and result display
                    if st.button(button_label):
                        with st.spinner("Evaluating..."):
                            generated_text = generate_content(image)  # Generate content from image

                    st.image(uploaded_image, caption="", use_column_width=True)

        # System tab
        with tabs[1]:  # System tab content
            st.write("System tab content goes here.")

    # Display extraction result in col3, separate from col1
    with col3:
        # Display generated text if available
        if generated_text:
            st.markdown(
                f"""
                <div class="generated-text-box">
                    <h3>Extraction Result:</h3>
                    <p>{generated_text}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("***")


if __name__ == "__main__":
    if st.session_state.logged_in:
        col1, col2, col3 = st.columns([10, 10, 1.5])
        with col3:
            if st.button("Logout"):
                logout()
        main()
    else:
        login()



# Custom CSS for the header and logo
# Custom CSS for the header and logo
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Graphik:wght@400;700&display=swap');

    body {
        background-color: #f0f0f0;
        color: black;
        font-family: 'Graphik', sans-serif;
    }
    .main {
        background-color: #f0f0f0;
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
        margin-right: 20px;  /* Space between logo and next item */
    }
    .header-content {
        display: flex;
        align-items: center;
    }
    .header-right {
        display: flex;
        align-items: center;
    }

    h1 {
        color: black;
        margin: 0;
        padding: 0;
    }

    .generated-text-box {
        border: 3px solid #A020F0; /* Thick border */
        padding: 20px;  
        border-radius: 10px; /* Rounded corners */
        color: black; /* Text color */
        background-color: #FFFFFF; /* Background color matching theme */
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Adding the logo and other elements in the header
st.markdown(
    f"""
    <header tabindex="-1" data-testid="stHeader" class="st-emotion-cache-12fmjuu ezrtsby2">
        <div data-testid="stDecoration" id="stDecoration" class="st-emotion-cache-1dp5vir ezrtsby1"></div>
        <div class="header-content">
            <!-- Add the logo here -->
            <img src="https://www.vgen.it/wp-content/uploads/2021/04/logo-accenture-ludo.png" class="logo" alt="Logo">
        
    </header>

    """,
    unsafe_allow_html=True
)
