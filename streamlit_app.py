import streamlit as st
from utils import images_to_display, call_api

# Load streamlit secrets. The secrets are stored in the .streamlit/secrets.toml file.
# To add a new variable, add it in the secrets.toml file and restart the streamlit server.
api_key = st.secrets["API_KEY"]
apis = {"id": st.secrets["API_URL_ID"], "invoices": st.secrets["API_URL_INVOICES"]}

st.set_page_config(layout="wide", page_title="Check OCR solutions")

st.write("# Check document with the selected OCR solution :mag_right:")
st.sidebar.write("## Configure Request :gear:")

# Create two columns with streamlit function st.columns
col1, col2 = st.columns(2)

# Select which API to use
selected_api = st.sidebar.radio("Select API:", apis.keys())

# Upload the file to send with the request
file_upload = st.sidebar.file_uploader("Choose a file:", type=["pdf", "jpeg", "jpg"])

if file_upload is not None:
    # Check file type
    file_extension = file_upload.name.split(".")[-1].lower()
    file_bytes = file_upload.getvalue()

    st.write("## Uploaded document")
    st.write(f"Document type: {file_extension}")

    # Display images
    for image_bytes in images_to_display(
        file_extension=file_extension, file_bytes=file_bytes
    ):
        st.image(image_bytes, clamp=False, channels="RGB", output_format="auto")


# Add a button to call the api
call_api_button = st.sidebar.button("Call the API")

# Call the api when the button is clicked
if call_api_button:
    response = call_api(
        file_bytes=file_upload,
        file_extension=file_extension,
        url=apis[selected_api],
        api_key=api_key,
    )

    st.write("## Response")
    st.write(f"Response time: {response.elapsed.total_seconds()}s")
    st.write(f"Response content (status {response.status_code}):")
    try:
        data = response.json()
        st.json(data, expanded=True)
    except Exception:
        st.write(response.text)
