from azure.identity import DefaultAzureCredential,AzureCliCredential
from azure.storage.blob import BlobServiceClient
import sqlalchemy as db
import yaml
import pandas as pd
import urllib
from mssql_python import connect
import struct
from datetime import datetime, timezone

print("............................................................")
print("............................................................")
print("............................................................")
print("")
print("")
print("")
print("        ___                         ________")
print("      __    __                          / /")
print("    ____________         ___           / /")
print("  __            __                    / /")
print(" __               __                ---------")
print("")
print("")
print("")
print("............................................................")
print("............................................................")
print("............................................................")
print("")
print("")
print("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print("Azure BLOB -> SQL DB Ingestion")
print("Staging Layer in Progress.......")
print("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print("")
print("")
print("Connecting to Blob Storage....")

with open(file="credentials.yaml",mode="r")as f:
    cred=yaml.safe_load(f)


container_name=cred["blob"]["container"]
account_url=cred["blob"]["account_url"]
driver_name=cred["database"]["driver_name"]
server_name=cred["database"]["server_name"]
database_name=cred["database"]["database_name"]
credential = DefaultAzureCredential()


def get_blob_service_client_token_credential():

    

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=credential)

    return blob_service_client

print("")
print("Connection secured!")
print("............................................................")

blob_client=get_blob_service_client_token_credential()
container_client=blob_client.get_container_client(container=container_name)

# for blob in blob_client.get_container_client(container=container_name).list_blobs():
#     print(blob["name"])

def get_engine():

    print("")
    
    print(f"Connecting to {database_name}....")
    connection_string = 'Driver={};Server={};Database={};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'.format(driver_name, server_name, database_name)

    params = urllib.parse.quote(connection_string)
    url = "mssql+pyodbc:///?odbc_connect={0}".format(params)
    print("Connected to DB Successfully!")
    print("............................................................")
    print("")
    return db.create_engine(url)

engine = get_engine() 


@db.event.listens_for(engine, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    """
        Called before the engine creates a new connection. Injects an EntraID token into the connection parameters.
    """
    print('Creating new token')

    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h

    cparams["attrs_before"] = {SQL_COPT_SS_ACCESS_TOKEN: token_struct}
    

def blob_file_download(engine):
    for blob in blob_client.get_container_client(container=container_name).list_blobs():
        print("............................................................")
        print("Downloading data from {}!".format(blob["name"]))
        print("")
        blob_client_v1 = blob_client.get_blob_client(container=container_name, blob=blob["name"])
        # stream = io.BytesIO()
        downloader = blob_client_v1.download_blob(max_concurrency=1, encoding='latin-1')
        blob_text = downloader
        df=pd.read_csv(blob_text)
        if blob["name"].find("_data")!=-1:
            file_name=blob["name"][:blob["name"].index("_data")]
        else:
            file_name=blob["name"][:blob["name"].index(".csv")]
        print("Uploading data from {} to {}!".format(blob["name"],database_name))
        df['loaded_at_timestamp']=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        df.to_sql(file_name,engine,if_exists="replace",chunksize=1000,schema="raw")
        print("")
        print("Upload complete!")
        print("Next......")
        print("............................................................")
        print("")
        print("")
        print("")
        print("")
        # break


# with engine.connect() as conn:
#     print("Connection Success!")
    
blob_file_download(engine)

print("")
print("Full Upload Complete!")
print("")
print("............................................................")
print("............................................................")
print("............................................................")