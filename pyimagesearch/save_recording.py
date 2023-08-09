# from . import TempImage
import pyodbc
import os, uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


server = 'security-system-server.database.windows.net'
database = 'SecuritySystemDatabase'
username = 'Paraon'
password = '{Adelinold001}'   
driver= '{ODBC Driver 17 for SQL Server}'



# def upload_image(image: TempImage):
#     pass


def save_captured_image(captured_image):
    pass

if __name__ == '__main__':
    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT TOP 3 name, collation_name FROM sys.databases")
            row = cursor.fetchone()
            while row:
                print (str(row[0]) + " " + str(row[1]))
                row = cursor.fetchone()


    blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=securitysystemstorage;AccountKey=7ENAUfNSruW7o8f32a04TjZiY+HbjSca1bNXhfBwQLOMDPYxmF6cLf0CQnSUUQnIlJz6dwNJebq3+AStFCffdA==;EndpointSuffix=core.windows.net"
    container_name = "captures"

    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)

    local_path = "./data"

    local_file_name = str(uuid.uuid4()) + ".txt"
    upload_file_path = os.path.join(local_path, local_file_name)

    file = open(file=upload_file_path, mode='w')
    file.write("Hello, World!")
    file.close()

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)
    with open(file=upload_file_path, mode="rb") as data:
        blob_client.upload_blob(data)

    print("\nListing blobs...")

    # List the blobs in the container
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        print("\t" + blob.name)

    # Download the blob to a local file
    # Add 'DOWNLOAD' before the .txt extension so you can see both files in the data directory
    download_file_path = os.path.join(local_path, str.replace(local_file_name ,'.txt', 'DOWNLOAD.txt'))
    container_client = blob_service_client.get_container_client(container= container_name) 
    print("\nDownloading blob to \n\t" + download_file_path)

    with open(file=download_file_path, mode="wb") as download_file:
        download_file.write(container_client.download_blob(local_file_name).readall())