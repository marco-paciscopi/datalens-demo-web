import streamlit as st
from utils import images_to_display, call_api

# Load streamlit secrets. The secrets are stored in the .streamlit/secrets.toml file.
# To add a new variable, add it in the secrets.toml file and restart the streamlit server.
api_key = st.secrets["API_KEY"]
apis = {
    "id": {"url": st.secrets["API_URL_ID"], "response_fields": {}},
    "invoices": {
        "url": st.secrets["API_URL_INVOICES"],
        "response_fields": {
            "vendor": "Fornitore :sunrise:",
            "name": "Name :bust_in_silhouette:",
            "surname": "Surname :bust_in_silhouette:",
            "email": "Email :e-mail:",
            "meter_address": "Indirizzo :house_buildings:",
        },
    },
}

invoice_commodity = ["dual", "luce", "gas"]

st.set_page_config(layout="wide", page_title="Check OCR solutions")

st.write("# Check document with the selected OCR solution :mag_right:")
st.sidebar.write("## Configure Request :gear:")

# Create two columns with streamlit function st.columns
col1, col2 = st.columns(2)

# Select which API to use
selected_api = st.sidebar.radio("Select API:", apis.keys())
selected_config = apis[selected_api]

# If invoices add params
params = {}
if selected_api == "invoices":
    commodity = st.sidebar.radio("Select commodity type:", invoice_commodity)
    params = {"commodity": commodity}

# Upload the file to send with the request
file_upload = st.sidebar.file_uploader("Choose a file:", type=["pdf", "jpeg", "jpg"])

if file_upload is not None:
    # Check file type
    file_extension = file_upload.name.split(".")[-1].lower()
    file_bytes = file_upload.getvalue()

    col1.write("## Uploaded document")
    col1.write(f"Document type: {file_extension}")

    # Display images
    for image_bytes in images_to_display(
        file_extension=file_extension, file_bytes=file_bytes
    ):
        col1.image(image_bytes, clamp=False, channels="RGB", output_format="auto")


# Add a button to call the api
call_api_button = st.sidebar.button("Call the API")

# Call the api when the button is clicked
if call_api_button:
    response = call_api(
        file_bytes=file_upload,
        file_extension=file_extension,
        url=selected_config["url"],
        api_key=api_key,
        params=params
    )

    col2.write("## Response")
    try:
        data = response.json()

        # Pretty print response
        for f_name, f_desc in selected_config["response_fields"].items():
            col2.write(f"#### {f_desc}")
            col2.write(data[f_name])

        # Print raw json response
        col2.write(f"### Raw response content (status {response.status_code}):")
        col2.write(f"Response time: {response.elapsed.total_seconds()}s")
        col2.json(data, expanded=True)
    except Exception:
        # Print raw json response
        col2.write(f"### Raw response content (status {response.status_code}):")
        col2.write(f"Response time: {response.elapsed.total_seconds()}s")
        col2.write(response.text)
