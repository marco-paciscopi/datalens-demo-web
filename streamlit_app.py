import logging

import streamlit as st
from benedict import benedict
from streamlit.runtime.uploaded_file_manager import UploadedFile

from sanitize import sanitize_dict
from utils import (
    call_authorization,
    call_bill_api,
    call_doc_api,
    images_to_display,
    read_image,
)


# === RESIDENTIAL CUSTOMERS SCHEMA ===
RESI_COMMON_FIELDS_SCHEMA = {
    "name": "Name :bust_in_silhouette:",
    "surname": "Surname :busts_in_silhouette:",
    "odonym_meter_address": "Address (odonym) :house:",
    "number_meter_address": "Address (street number) :house:",
    "cap_meter_address": "Postal Code :postbox:",
    "city_meter_address": "City :cityscape:",
    "province_meter_address": "Province :mountain:",
    "fiscal_code": "Fiscal Code :female-detective:",
    "commodity": "Commodity Type :electric_plug:",
    "start_of_delivery": "Start of Delivery :rocket:",
}

RESI_GAS_FIELDS_SCHEMA = {
    "pdr": "PDR :pushpin:",
    "use_type": "Gas usage type :diya_lamp:",
    "gas_total_annual_consumption": "Total annual gas consumption :fire:",
}

RESI_POWER_FIELDS_SCHEMA = {
    "pod": "POD :round_pushpin:",
    "engaged_power": "Engaged power :electric_plug:",
    "power_total_annual_consumption": "Total annual power consumption :bulb:",
    "power_F1_annual_consumption": "Power F1 annual consumption :sunny:",
    "power_F2_annual_consumption": "Power F2 annual consumption :partly_sunny:",
    "power_F3_annual_consumption": "Power F3 annual consumption :new_moon:",
}

# === MICROBUSINESS CUSTOMERS SCHEMA ===
MB_COMMON_FIELDS_SCHEMA = {
    "company_name": "Company Name :office:",
    "odonym_meter_address": "Meter Address (odonym) :house:",
    "number_meter_address": "Meter Address (street number) :house:",
    "cap_meter_address": "Meter Postal Code :postbox:",
    "city_meter_address": "Meter City :cityscape:",
    "province_meter_address": "Meter Province :mountain:",
    "odonym_legal_address": "Legal Address (odonym) :bank:",
    "number_legal_address": "Legal Address (street number) :bank:",
    "cap_legal_address": "Legal Postal Code :mailbox:",
    "city_legal_address": "Legal City :cityscape:",
    "province_legal_address": "Legal Province :mountain:",
    "fiscal_code": "Fiscal Code :female-detective:",
    #"vat_number": "VAT Number :receipt:",
    "commodity": "Commodity Type :electric_plug:",
}

MB_GAS_FIELDS_SCHEMA = {
    "pdr": "PDR :pushpin:",
    "use_type": "Gas usage type :diya_lamp:",
    "gas_total_annual_consumption": "Total annual gas consumption :fire:",
}

MB_POWER_FIELDS_SCHEMA = {
    "pod": "POD :round_pushpin:",
    "engaged_power": "Engaged power :electric_plug:",
    "available_power": "Available power :zap:",
    "supply_voltage": "Supply voltage :high_voltage:",
    "power_total_annual_consumption": "Total annual power consumption :bulb:",
    "power_F1_annual_consumption": "Power F1 annual consumption :sunny:",
    "power_F2_annual_consumption": "Power F2 annual consumption :partly_sunny:",
    "power_F3_annual_consumption": "Power F3 annual consumption :new_moon:",
}


# Get the correct field mapping based on customer type and commodity
def get_field_mapping(customer_type, commodity):
    field_mapping = {}
    if customer_type.lower() == "residenziale":
        field_mapping.update(RESI_COMMON_FIELDS_SCHEMA)
        if commodity in ["gas", "dual"]:
            field_mapping.update(RESI_GAS_FIELDS_SCHEMA)
        if commodity in ["luce", "dual"]:
            field_mapping.update(RESI_POWER_FIELDS_SCHEMA)
    elif customer_type.lower() == "microbusiness":
        field_mapping.update(MB_COMMON_FIELDS_SCHEMA)
        if commodity in ["gas", "dual"]:
            field_mapping.update(MB_GAS_FIELDS_SCHEMA)
        if commodity in ["luce", "dual"]:
            field_mapping.update(MB_POWER_FIELDS_SCHEMA)
    return field_mapping


def process_single_upload(file_upload: UploadedFile) -> dict:
    # Process file type
    file_extension = file_upload.name.split(".")[-1].lower()
    if file_extension == "pdf":
        file_content_type = "application/pdf"
    elif file_extension in ["jpeg", "jpg"]:
        file_content_type = "image/jpeg"
    elif file_extension == "png":
        file_content_type = "image/png"
    else:
        file_content_type = "application/octet-stream"

    # Process file content
    file_bytes = file_upload.getvalue()

    # Process file name
    file_name = file_upload.name

    return {"name": file_name, "bytes": file_bytes, "content_type": file_content_type}


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
        "accept_multiple_files": True,
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
        "accept_multiple_files": False,
    },
}

invoice_commodity = ["gas", "luce", "dual"]
invoice_language = ["it", "es"]
favicon_bytes = read_image("assets/favicon.ico")
st.set_page_config(
    layout="wide", page_title="DataLens Demo Web", page_icon=favicon_bytes
)

st.write("# Check document with the DataLens solution :mag_right:")

st.sidebar.write("## Configure Request :gear:")

# Create two columns with streamlit function st.columns
col1, col2 = st.columns(2)

# Select which API to use

selected_api = "invoices"
selected_config = apis[selected_api]

# If invoices add params
params = {}
headers = {}
if selected_api == "invoices":
    # Customer type is still configurable.
    selected_customer_type = st.sidebar.radio("Select customer type:", ["residenziale", "microbusiness"])
    print(selected_customer_type)

    selected_commodity = invoice_commodity[0]
    selected_language = invoice_language[0]
    params = {"commodity": selected_commodity, "customer_type": selected_customer_type}
    headers = {"language": selected_language}
print(params)
# Upload the file to send with the request
file_upload = st.sidebar.file_uploader(
    "Choose a file:",
    type=["pdf", "jpeg", "jpg", "png"],
    accept_multiple_files=selected_config["accept_multiple_files"],
)
if file_upload is not None:
    # Process uploads
    if not isinstance(file_upload, list):
        file_upload = [file_upload]
    file_upload = [process_single_upload(file_upload=fu) for fu in file_upload]

    # Display the uploaded files
    col1.write("## Uploaded documents")

    for file in file_upload:
        col1.write(f"Document \"{file['name']}\" ({file['content_type']})")

        # Display images
        for image_bytes in images_to_display(
            content_type=file["content_type"], file_bytes=file["bytes"]
        ):
            col1.image(image_bytes, clamp=False, channels="RGB", output_format="auto")


# Add a button to call the api
call_api_button = st.sidebar.button("Call the API")

# Call the api when the button is clicked
if call_api_button:
    if not file_upload or len(file_upload) == 0:
        st.error("Please upload at least one file before calling the API.")
    else:
        logging.info(f"Calling the API {selected_api}")

        access_token = call_authorization(
            url=st.secrets["AUTH_URL"],
            client_id=st.secrets["AUTH_CLIENT_ID"],
            client_secret=st.secrets["AUTH_CLIENT_SECRET"],
            grant_type="client_credentials",
        )

        if selected_api == "invoices":
            response = call_bill_api(
                file_bytes=file_upload[0]["bytes"],
                file_content_type=file_upload[0]["content_type"],
                url=selected_config["url"],
                api_key=api_key,
                data=params,
                headers=headers,
                access_token=access_token,
            )
        elif selected_api == "id":
            response = call_doc_api(
                file_list=file_upload,
                url=selected_config["url"],
                api_key=api_key,
                data=params,
                headers=headers,
                access_token=access_token,
            )

        col2.write("## Response")
        try:
            data = sanitize_dict(response.json())

            # Pretty print response
            output_data = benedict(data, keypath_separator=".")

            if selected_api == 'id':
                for f_name, f_desc in selected_config["response_fields"].items():
                    col2.write(f"#### {f_desc}")
                    col2.write(output_data[f_name])
            else:
                # Always display the section header
                col2.write(f"### Fields for {selected_customer_type}")
                extracted_fields = output_data.get('extracted_fields', {})

                field_mapping = get_field_mapping(selected_customer_type, selected_commodity)
                any_field_displayed = False
                for field_name, display_name in field_mapping.items():
                    if field_name in extracted_fields:
                        value = extracted_fields[field_name]
                        if value is not None and value != "":
                            pretty_name = display_name if display_name else field_name.replace('_', ' ').capitalize()
                            col2.write(f"#### {pretty_name}")
                            col2.write(value)
                            any_field_displayed = True
                if not any_field_displayed:
                    col2.write("No fields to display.")


            # Print raw json response
            col2.write(f"### Raw response content (status {response.status_code}):")
            col2.write(f"Response time: {response.elapsed.total_seconds()}s")
            col2.json(data, expanded=True)
        except Exception:
            # Print raw json response
            col2.write(f"### Raw response content (status {response.status_code}):")
            col2.write(f"Response time: {response.elapsed.total_seconds()}s")
            col2.write(sanitize_dict(response.text))
