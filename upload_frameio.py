import requests
import os

CLIENT_ID = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"
REFRESH_TOKEN = "SEU_REFRESH_TOKEN"
PARENT_ASSET_ID = "SEU_PARENT_ASSET_ID"

VIDEO_PATH = r"C:\frameio_test\teste.mp4"
VIDEO_NAME = "teste.mp4"


def get_access_token():
    url = "https://api.frame.io/v2/oauth/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    r = requests.post(url, data=payload)

    return r.json()["access_token"]


def create_asset(token):

    url = "https://api.frame.io/v2/assets"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "name": VIDEO_NAME,
        "parent_id": PARENT_ASSET_ID,
        "type": "file"
    }

    r = requests.post(url, headers=headers, json=payload)

    return r.json()


def upload_file(upload_url):

    with open(VIDEO_PATH, "rb") as f:
        requests.put(upload_url, data=f)


def finalize_upload(token, asset_id):

    url = f"https://api.frame.io/v2/assets/{asset_id}/complete"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    requests.post(url, headers=headers)


token = get_access_token()

asset = create_asset(token)

asset_id = asset["id"]
upload_url = asset["upload_url"]

upload_file(upload_url)

finalize_upload(token, asset_id)

print("UPLOAD FINALIZADO")
print("ASSET_ID:", asset_id)