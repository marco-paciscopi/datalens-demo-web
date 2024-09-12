import logging
import textwrap
from typing import Tuple

import fitz
import requests
from PIL import Image


def read_image(image_path: str) -> bytes:
    image_bytes = Image.open(image_path)

    return image_bytes


def pdf_to_images(file_bytes: bytes) -> list[bytes]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    # Iterate over each page and convert it to an image
    image_list = [
        doc.load_page(n).get_pixmap().pil_tobytes(format="JPEG")
        for n, _ in enumerate(doc.pages())
    ]

    doc.close()

    return image_list


def images_to_display(content_type: str, file_bytes: bytes) -> list[bytes]:
    # display image
    images_to_display = []
    match content_type:
        case "application/pdf":
            images_to_display = pdf_to_images(file_bytes)
        case "image/jpeg" | "image/png":
            images_to_display.append(file_bytes)

    return images_to_display


def call_authorization(
    url: str, client_id: str, client_secret: str, grant_type: str
) -> str:
    # Call the api with the file and the api key
    r = requests.post(
        url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        params={"grant_type": grant_type},
        data={"client_id": client_id, "client_secret": client_secret},
        verify=False,
    )

    return r.json()["access_token"]


def print_roundtrip(response, *args, **kwargs):
    format_headers = lambda d: "\n".join(f"{k}: {v}" for k, v in d.items())  # noqa: E731
    logging.info(
        textwrap.dedent(
            """
        ---------------- request ----------------
        {req.method} {req.url}
        {reqhdrs}
        

        ---------------- response ----------------
        {res.status_code} {res.reason} {res.url}
        {reshdrs}

        {res.text}
    """
        ).format(
            req=response.request,
            res=response,
            reqhdrs=format_headers(response.request.headers),
            reshdrs=format_headers(response.headers),
        )
        # avoid since it's too big{req.body}
    )


def call_bill_api(
    file_bytes: bytes,
    file_content_type: str,
    url: str,
    api_key: str,
    params: dict,
    headers: dict,
    access_token: str,
) -> requests.Response:
    headers = {
        "x-api-key": api_key,
        "Content-Type": file_content_type,
        "Authorization": f"Bearer {access_token}",
        **headers,
    }

    # Call the api with the file and the api key
    r = requests.post(
        url,
        data=file_bytes,
        headers=headers,
        params=params,
        hooks={"response": print_roundtrip},
    )

    return r


def call_doc_api(
    file_list: list[Tuple[str, bytes, str]],
    url: str,
    api_key: str,
    params: dict,
    headers: dict,
    access_token: str,
) -> requests.Response:
    headers = {
        "x-api-key": api_key,
        "Authorization": f"Bearer {access_token}",
        **headers,
    }

    # Call the api with the file and the api key
    r = requests.post(
        url,
        files=[
            ("files", (file["name"], file["bytes"], file["content_type"]))
            for file in file_list
        ],
        headers=headers,
        params=params,
        hooks={"response": print_roundtrip},
    )

    return r
