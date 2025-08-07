import datetime
import json
import logging
import os
from azure.cosmos import CosmosClient
from azure.storage.filedatalake import DataLakeServiceClient
import azure.functions as func

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DB = os.environ["COSMOS_DB"]
COSMOS_CONTAINER = os.environ["COSMOS_CONTAINER"]
STORAGE_ACCOUNT_NAME = os.environ["STORAGE_ACCOUNT_NAME"]
STORAGE_ACCOUNT_KEY = os.environ["STORAGE_ACCOUNT_KEY"]
FILESYSTEM_NAME = os.environ["FILESYSTEM_NAME"]
ARCHIVE_ROOT_PATH = "archive"

def main(mytimer: func.TimerRequest) -> None:
    logging.info("Archival function started")
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    cutoff_ts = int(cutoff_date.timestamp())

    cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    db = cosmos_client.get_database_client(COSMOS_DB)
    container = db.get_container_client(COSMOS_CONTAINER)

    query = "SELECT * FROM c WHERE c._ts < @cutoff"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@cutoff", "value": cutoff_ts}],
        enable_cross_partition_query=True
    ))

    if not items:
        logging.info("No items found to archive.")
        return

    adls = DataLakeServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT_NAME}.dfs.core.windows.net",
        credential=STORAGE_ACCOUNT_KEY
    )
    fs_client = adls.get_file_system_client(FILESYSTEM_NAME)

    today = datetime.datetime.utcnow()
    path = f"{ARCHIVE_ROOT_PATH}/{today.year}/{today.month:02}/{today.day:02}/data.json"
    file_client = fs_client.get_file_client(path)

    data_str = json.dumps(items, indent=2)
    file_client.create_file()
    file_client.append_data(data=data_str, offset=0, length=len(data_str))
    file_client.flush_data(len(data_str))

    logging.info(f"{len(items)} records archived to ADLS path: {path}")