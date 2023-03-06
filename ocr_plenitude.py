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


# Open a pdf file with fitz library
def open_pdf(file):
    # Open the file
    doc = fitz.open(file)

    # Get the first page
    page = doc.loadPage(0)

    # Get the page text
    text = page.getText()

    # Return the text
    return text


def call_api(file, api, api_key):

    # Encode the file in binary
    # binary_pdf = file.getvalue().encode('utf-8')
    with open('test.pdf', "rb") as f:
        file_content = f.read()

    # The format of each instance should conform to the deployed model's prediction input schema.
    encoded_content = base64.b64encode(file_content).decode("utf-8")
    

    # Create a dictionary with the file     
    #data = {'file': binary_pdf}
    data = {'file': encoded_content}


    # Call the api with the file and the api key
    r = requests.post(api, data=data, params={'key': api_key}, headers={'Content-Type': 'application/pdf',
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
    response = call_api(file=my_upload, api=api_url, api_key=api_key)
