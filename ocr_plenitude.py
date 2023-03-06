import os
import streamlit as st
import requests
import json
import base64
import shutil

# Load streamlit secrets. The secrets are stored in the .streamlit/secrets.toml file.
# To add a new variable, add it in the secrets.toml file and restart the streamlit server.
api_key = st.secrets["API_KEY"]
api_url = st.secrets["API_URL"]

def displayPDF(file):
    with col1:
        # Opening file from file path
        with open(file, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')

        # Embedding PDF in HTML
        pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'

        # Displaying File
        st.markdown(pdf_display, unsafe_allow_html=True)


st.set_page_config(layout="wide", page_title="Check identity document")

st.write("## Check identity document :mag_right:")
st.write(
    ":picture: Try uploading an image in pdf format"
)
st.sidebar.write("## Upload and download :gear:")


# Create two columns with streamlit function st.columns
col1, col2 = st.columns(2)

my_upload = st.sidebar.file_uploader("Upload an image", type=["pdf"])

# Save the uploaded file to disk
if my_upload is not None:
    # save the uploaded file to disk
    with open("uploaded_file.pdf", "wb") as buffer:
        shutil.copyfileobj(my_upload, buffer)
      
    displayPDF("uploaded_file.pdf")


def call_api(file, api, api_key):

    # Encode the file in binary
    # binary_pdf = file.getvalue().encode('utf-8')
    # with open('test.pdf', "rb") as f:
    #     file_content = f.read()
   

    # Create a dictionary with the file     
    #data = {'file': binary_pdf}
    data = {'file': file}


    # Call the api with the file and the api key
    r = requests.post(api, files=data, params={'key': api_key}, headers={'Content-Type': 'application/pdf',
                                                                        'Accept': '*/*',
                                                                        'Accept-Encoding': 'gzip, deflate, br',
                                                                        'Connection': 'keep-alive',
                                                                        'User-Agent': 'python-requests/2.25.1',
                                                                        'Content-Length': '0',
                                                                        'Host': 'real-time-ocr-gateway-3bcpgr34.ew.gateway.dev'})
    print(r.text)
    
    return r


# Add a button to call the api
call_api_button = st.sidebar.button("Call the API")

# Call the api when the button is clicked
if call_api_button:
    response = call_api(file=my_upload.read(), api=api_url, api_key=api_key)

    # Display the response in a form with streamlit function st.form
    # The form displays the response in text fields. 
    # Fields extracted from response are [nome, cognome, tipo_documento, id_documento, data_scadenza, motivazione, documento_valido]
    response = json.loads(response.text)
    nome = response['nome']
    cognome = response['cognome']
    tipo_documento = response['tipo_documento']
    id_documento = response['id_documento']
    data_scadenza = response['data_scadenza']
    motivazione = response['motivazione']
    documento_valido = response['documento_valido']

    # Display the response in a form with streamlit function st.form on the right column

    with st.form(key='my_form'):
        col2.write("## Response :mag_right:")
        col2.write("### Name :bust_in_silhouette:")
        col2.write(nome)
        col2.write("### Surname :bust_in_silhouette:")
        col2.write(cognome)
        col2.write("### Document type :page_facing_up:")
        col2.write(tipo_documento)
        col2.write("### Document id :page_facing_up:")
        col2.write(id_documento)
        col2.write("### Expiration date :page_facing_up:")
        col2.write(data_scadenza)
        col2.write("### Motivation :page_facing_up:")
        col2.write(motivazione)
        col2.write("### Document valid :page_facing_up:")
        col2.write(documento_valido)
        submit_button = st.form_submit_button(label='OK')

