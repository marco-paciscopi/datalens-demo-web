import logging
import streamlit as st
from benedict import benedict

from sanitize import sanitize_dict
from utils import call_api, call_authorization, images_to_display, read_image

# Load streamlit secrets. The secrets are stored in the .streamlit/secrets.toml file.
# To add a new variable, add it in the secrets.toml file and restart the streamlit server.
api_key = st.secrets["API_KEY"]
apis = {
    "id": {
        "url": st.secrets["API_URL_ID"],
        "response_fields": {
            "campi_documento.nome": "Name :bust_in_silhouette:",
            "campi_documento.cognome": "Surname :busts_in_silhouette:",
            "campi_documento.id_documento": "ID :information_source:",
            "campi_documento.data_scadenza": "Expiration date :calendar:",
            "tipo_documento": "Type of document :bookmark_tabs:",
            "dati_validi": "Document validity :white_check_mark:",
        },
    },
    "invoices": {
        "url": st.secrets["API_URL_INVOICES"],
        "response_fields": {
            "output_data.name": "Name :bust_in_silhouette:",
            "output_data.surname": "Surname :busts_in_silhouette:",
            "output_data.odonym_meter_address": "Address (odonym) :house:",
            "output_data.number_meter_address": "Address (street number) :house:",
            "output_data.cap_meter_address": "Postal Code :postbox:",
            "output_data.city_meter_address": "City :cityscape:",
            "output_data.province_meter_address": "Province :mountain:",
            "output_data.cod_fiscale": "Fiscal Code :female-detective:",
        },
    },
}

invoice_commodity = ["gas", "luce", "dual"]
favicon_bytes = read_image("assets/favicon.ico")
st.set_page_config(
    layout="wide", page_title="Check DataLens solutions", page_icon=favicon_bytes
)

st.write("# Check document with the selected DataLens solution :mag_right:")
# logo_bytes = read_image("assets/logo.png")
# st.sidebar.image(logo_bytes, clamp=False, channels="RGB", output_format="auto")
st.sidebar.write("## Configure Request :gear:")

# Create two columns with streamlit function st.columns
col1, col2 = st.columns(2)

# Select which API to use
selected_api = st.sidebar.radio("Select API:", ["id", "invoices"])
selected_config = apis[selected_api]

# If invoices add params
params = {}
if selected_api == "invoices":
    selected_commodity = st.sidebar.radio("Select commodity type:", invoice_commodity)
    params = {"commodity": selected_commodity}
    if selected_commodity == "dual":
        selected_config["response_fields"].update(
            {
                "output_data.PDR": "PDR :pushpin:",
                "output_data.POD": "POD :round_pushpin:",
                "output_data.use_type": "Tipo d'uso gas:diya_lamp:",
                "output_data.engaged_power": "Potenza Impegnata :electric_plug:",
                "output_data.gas_total_annual_consumption": "Consumo annuo totale gas :fire:",
                "output_data.power_total_annual_consumption": "Consumo annuo totale luce :bulb:",
            }
        )
    elif selected_commodity == "gas":
        selected_config["response_fields"].update(
            {
                "output_data.PDR": "PDR :pushpin:",
                "output_data.use_type": "Gas usage type :diya_lamp:",
                "output_data.gas_total_annual_consumption": "Total annual gas consumption :fire:",
            }
        )
    elif selected_commodity == "luce":
        selected_config["response_fields"].update(
            {
                "output_data.POD": "POD :round_pushpin:",
                "output_data.engaged_power": "Engaged power :electric_plug:",
                "output_data.power_total_annual_consumption": "Total annual power consumption :bulb:",
            }
        )

# Upload the file to send with the request
file_upload = st.sidebar.file_uploader(
    "Choose a file:", type=["pdf", "jpeg", "jpg", "png"]
)

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
    logging.info(f"Calling the API {selected_api} with format {file_extension}")
    access_token = call_authorization(
        url=st.secrets["AUTH_URL"],
        client_id=st.secrets["AUTH_CLIENT_ID"],
        client_secret=st.secrets["AUTH_CLIENT_SECRET"],
        grant_type="client_credentials",
    )

    response = call_api(
        file_bytes=file_upload,
        file_extension=file_extension,
        url=selected_config["url"],
        api_key=api_key,
        params=params,
        access_token=access_token,
    )

    col2.write("## Response")
    try:
        data = sanitize_dict(response.json())

        # Pretty print response
        output_data = benedict(data, keypath_separator=".")
        for f_name, f_desc in selected_config["response_fields"].items():
            col2.write(f"#### {f_desc}")
            col2.write(output_data[f_name])

        # Print raw json response
        col2.write(f"### Raw response content (status {response.status_code}):")
        col2.write(f"Response time: {response.elapsed.total_seconds()}s")
        col2.json(data, expanded=True)
    except Exception:
        # Print raw json response
        col2.write(f"### Raw response content (status {response.status_code}):")
        col2.write(f"Response time: {response.elapsed.total_seconds()}s")
        col2.write(sanitize_dict(response.text))
