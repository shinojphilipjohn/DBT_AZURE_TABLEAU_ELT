from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import yaml 
from pathlib import Path

with open(file="credentials.yaml",mode="r")as f:
    cred=yaml.safe_load(f)


container_name=cred["blob"]["container"]
account_url=cred["blob"]["account_url"]
filepath= cred["filepath"]

def get_blob_service_client_token_credential():

    credential = DefaultAzureCredential()

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=credential)

    return blob_service_client



blob_client=get_blob_service_client_token_credential()
container_client=blob_client.get_container_client(container=container_name)

def upload_blob(filepath):
    for file in filepath.iterdir():
        with open(file,mode="rb") as data:
            container_blob=container_client.upload_blob(name=file.name,data=data,overwrite=True)
    print("All Files Uploaded Successfully!....")


filepath=Path(filepath)
upload_blob(filepath)

