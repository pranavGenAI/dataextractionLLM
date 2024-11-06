import streamlit as st
import PIL.Image
import google.generativeai as genai
import time
import hashlib
import json
import pandas as pd
from fuzzywuzzy import fuzz  # Import the fuzzy matching function
import re
# Set page title, icon, and dark theme
st.set_page_config(page_title="Invoice Data Processing", page_icon=">", layout="wide")
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
GOOGLE_API_KEY = "AIzaSyBJJfXHfC80NWtiKGA57aO2mGsT-aD9fhQ"
genai.configure(api_key=GOOGLE_API_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Define users and hashed passwords for simplicity
users = {
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
            prompt = """You have been given contract document as input. Perform the following validations:
            1. Contract Number 
            2. Check if date is within COVID period (Jan 2020 to July 2023) if the document is invoice
            3. Check if the department in To is NYS department of health
            4. Extract vendor name
            5. Validate if contractor signature is present
            6. Validate if officer signature is present 
            7. Extract Original contract start and end date
            8. Extract New contract start and end date
            9. Contract Value 

            Return a json with below keys: Contract Number, Within COVID: (Yes/No), Addressed to NYDOH: (Yes/No), Vendor/Merchant, Contractor Signature Present: (Yes/No), Officer Signature Present: (Yes/No), Original Contract Start Date, Original Contract End Date, New Contract Start Date, New Contract End Date, Contract Value
            If any of the above value is missing just return blank
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

def generate_compare_genAI(extracted_values, values_from_excel, keys_of_interest):
    model = genai.GenerativeModel('gemini-1.5-pro')
    # Format the prompt for the AI model to compare each key
    prompt = {
        "keys_of_interest": keys_of_interest,
        "extracted_values": extracted_values,
        "values_from_excel": values_from_excel
    }
    st.write(prompt)
    # Generate the comparison JSON response
    response = model.generate_content(f"""Compare the extracted values with values from Excel for each key in {prompt} and return a JSON with only 'Yes' or 'No' as values for each key. It may not be exact match. For Key 0 understand the input and if both are matching to some bit then return Yes. Response should only include json file in the format like:
        Example format:
        {{
            "Key1": "Yes",
            "Key2": "No",
            ...
        }} Make sure to return only the JSON, with no other text or explanation.""")
    # Clean the response
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        # Parse the cleaned response as JSON
        comparison_results = json.loads(cleaned_response)
        st.write(comparison_results)
        return comparison_results
    except json.JSONDecodeError:
        st.error(f"Invalid JSON returned by AI: {cleaned_response}")
        return {}

def main():
    st.title("Invoice Processing")
    st.markdown("")
    col1, col2, col3 = st.columns([4, 1, 4])  # Create three columns

    generated_text = ""

    with col1:
        # Place tabs within col1
        tabs = st.tabs(["📄 Document", "⚙️ System"])

        # Document tab
        with tabs[0]:
            uploaded_images = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, label_visibility="collapsed")

                        # Inject custom CSS to hide the element
            hide_css = """
            <style>
                .st-emotion-cache-fis6aj, .e1b2p2ww10 {
                    color: white !important;
                    background-color: white !important;
                }
            </style>
            """
            st.markdown(hide_css, unsafe_allow_html=True)
            
            # Display uploaded images and data extraction button
            if uploaded_images:
                for uploaded_image in uploaded_images:
                    image = PIL.Image.open(uploaded_image)
                    button_label = f"Extract data {uploaded_images.index(uploaded_image) + 1}" if len(uploaded_images) > 1 else "Extract data"

                    if st.button(button_label):
                        with st.spinner("Evaluating..."):
                            generated_text = generate_content(image)  # Generate content from image

                    st.image(uploaded_image, caption="", use_column_width=True)

        # System tab
        with tabs[1]:
            excel_file = "Invoice processing.xlsx"  # Ensure this file is in your working directory
            try:
                df = pd.read_excel(excel_file)  # Read the Excel file
                st.dataframe(df)  # Display the data as a table
            except Exception as e:
                st.error(f"Error reading the Excel file: {e}")

    # Display extraction result in col3, separate from col1
    with col3:
        if generated_text:
            try:
                # Extract and parse the JSON response
                json_str = generated_text.strip().split('\n', 1)[-1].replace("```json", "").replace("```", "").strip()
                extracted_data = json.loads(json_str)  # Use json.loads to parse

                # Display extracted data in bullet format
                st.markdown("### Extraction Result:")
                for key in ["Within COVID", "Addressed to NYDOH", "Contractor Signature Present", "Officer Signature Present"]:
                    if key in extracted_data:
                        st.markdown(f"- **{key}**: {extracted_data[key]}")  # Format each key-value pair as a bullet point

                # Extract contract number
                contract_number = extracted_data.get("Contract Number", "")

                # Find the row in the Excel DataFrame for the contract number
                if not df.empty and contract_number:
                    contract_row = df[df['Contract Number'] == contract_number]

                    if not contract_row.empty:
                        keys_of_interest = [
                            "Vendor/Merchant",
                            "Original Contract Start Date",
                            "Original Contract End Date",
                            "New Contract Start Date",
                            "New Contract End Date",
                            "Contract Value"
                        ]

                        # Extract values for the specified keys from the JSON and Excel DataFrame
                        values_from_excel = []
                        extracted_values = []

                        for key in keys_of_interest:
                            if key in extracted_data:
                                extracted_values.append(extracted_data[key])  # From extracted data
                            else:
                                extracted_values.append("")  # Placeholder if the key is not found

                            if key in contract_row.columns:
                                values_from_excel.append(contract_row.iloc[0][key])  # From Excel
                            else:
                                values_from_excel.append("")  # Placeholder if the key is not found

                        # Use the AI model to generate comparison results
                        comparison_results = generate_compare_genAI(extracted_values, values_from_excel, keys_of_interest)

                        # Initialize checkbox states in session_state if not already done
                        if 'checkbox_states' not in st.session_state:
                            st.session_state.checkbox_states = {key: (comparison_results.get(key, "No") == "Yes") for key in keys_of_interest}

                        # Add checkboxes directly to the DataFrame
                        editable_df = pd.DataFrame({
                            'Keys': keys_of_interest,
                            'Values from System': values_from_excel,
                            'Extracted Information': extracted_values
                        })

                        editable_df['Match'] = [
                            st.checkbox(f"Match for {key}", value=st.session_state.checkbox_states.get(key, False), key=f"checkbox_{key}") 
                            for key in keys_of_interest
                        ]

                        # # Update session state based on user input
                        # for key in keys_of_interest:
                        #     st.session_state.checkbox_states[key] = editable_df['Match'][keys_of_interest.index(key)]

                        # Display the DataFrame with checkboxes
                        st.dataframe(editable_df, use_container_width=True)

                    else:
                        st.warning(f"No data found for contract number: {contract_number}")
                else:
                    st.warning("Contract number not found in the Excel file.")

            except json.JSONDecodeError as e:
                st.error(f"Failed to parse generated text as JSON: {e}. Please check the output.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

                
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
