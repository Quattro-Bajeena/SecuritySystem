from infrastructure.tempimage import TempImage
import pyodbc
import os, uuid
import cv2
from datetime import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, BlobType

driver= None
database_connection = None
blob_container = None
configuration = None

def connection_setup(config):
    global configuration
    configuration = config

    print("Connection setup")
    global database_connection, blob_container
    server = config["database_server"]
    database = config["database_name"]
    username = config["username"]
    password = config["password"]
    driver = config["database_driver"]


    database_connection = pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
    print("Conenected to database")

    blob_connection_string = config["blob_connection_string"]
    blob_container_name = config["blob_container_name"]
    
    blob_service = BlobServiceClient.from_connection_string(blob_connection_string)
    blob_container = blob_service.get_container_client(container= blob_container_name) 
    print("Conenected to blob storage")



def upload_image(frame):
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d_%H-%M-%S_")

    img_path = date_time + str(uuid.uuid4()) + ".jpg"

    cv2.imwrite(img_path, frame)

    with open(file=img_path, mode="rb") as data:
        blob_container.upload_blob(img_path, data)


    with database_connection.cursor() as cursor:
        sql = f"INSERT INTO MovementCapture (Date, Type, FileName) VALUES ('{now}', 0, '{img_path}')"
        cursor.execute(sql)

    print("[UPLOAD]")

    os.remove(img_path)



def save_captured_image(captured_image_data):
    pass

if __name__ == '__main__':
    server = 'security-system-server.database.windows.net'
    database = 'SecuritySystemDatabase'
    username = 'Paraon'
    password = 'Adelinold001' 

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