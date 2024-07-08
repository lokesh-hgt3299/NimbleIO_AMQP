from celery import Celery, group, chord

import os, sys, requests
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.variable import daily_sales_domain, root, mongo_client
from utils.email_client import get_attachments
from services.aws import upload_to_s3

db = mongo_client["daily_sales"]

app = Celery(__name__, broker="amqp://guest:guest@localhost//", backend='redis://localhost:6379/0')

@app.task()
def process_email(email: dict):
    email_id = email["id"]
    body: dict = email.get("body", {})
    body_html: str = body.get("content", "")

    _from = email.get("from")

    receivedDateTime = datetime.strptime(
        email.get("receivedDateTime"), "%Y-%m-%dT%H:%M:%SZ"
    )

    to_mail: str = None

    for entry in email.get("ccRecipients", []) + email.get("toRecipients", []):
        mail: str = entry["emailAddress"]["address"]
        if daily_sales_domain in mail:
            to_mail = mail
            break

    if to_mail and email["hasAttachments"]:
        res = requests.get("http://localhost:8001/bill_automation/get_token")
        token = res.json()
        attachments = get_attachments(email_id=email_id, token=token, mail="info@sendhours.com")
        
        client, pms = os.path.splitext(to_mail.split("@")[0])

        doc = {
            "receivedDateTime": receivedDateTime,
            "attachments": attachments,
            "_from": _from["emailAddress"]["address"],
            "to_mail": to_mail,
            "client": client,
            "pms": pms.replace(".", ""),
            "type": "mail",
            "body": body_html,
            "microsoft_id": email_id,
        }

        process_resource_and_files.delay(doc)


# The function for handling both email and uploaded files.
@app.task()
def process_resource_and_files(doc: dict):
    receivedDateTime: datetime = doc.get("receivedDateTime")
    _from: str = doc.get("_from")
    to_mail: str = doc.get("to_mail")
    client: str = doc.get("client")
    pms: str = doc.get("pms")
    doc_type: str = doc.get("type")
    body: str = doc.get("body")
    microsoft_id: str = doc.get("microsoft_id", None)
    attachments: list = doc.get("attachments")

    email_table = file_table = {
        "from": _from,
        "to": to_mail,
        "body": body,
        "timestamp": receivedDateTime,
        "client": client,
        "property": pms,
        "type": doc_type,
        "microsoft_id": microsoft_id,
    }

    email_doc = email_table.copy()
    file_table['email_table_id'] = db['email_table'].insert_one(email_doc).inserted_id

    filepath = f"{root}/{"daily_sales"}/{client}/{pms}"

    tasks = []

    for f in attachments:
        content_bytes = f['content_bytes']
        filename = f['filename']
        key = f"{filepath}/{filename}"

        file_table["source_filename"] = f['source_filename']
        file_table["s3_key"] = key

        file_doc = file_table.copy()
        file_table_id = db['file_table'].insert_one(file_doc).inserted_id
        file_table_id = str(file_table_id)

        t1 = extract_date_and_facility_id.delay(content_bytes, file_table_id)
        t2 = extract_dataFrames.delay(content_bytes, file_table_id)
        

# Task 1: Extract Date and Facility ID
@app.task
def extract_date_and_facility_id(content_bytes, file_table_id):
    # Implementation to extract date and facility id
    date, facility_id = None, None
    return date, facility_id, file_table_id

# Task 2: Extract DataFrames
@app.task
def extract_dataFrames(content_bytes, file_table_id):
    # Implementation to extract dataFrames
    dataFrames = {}
    return dataFrames, file_table_id


@app.task
def check_and_validation(results):
    print(results)
