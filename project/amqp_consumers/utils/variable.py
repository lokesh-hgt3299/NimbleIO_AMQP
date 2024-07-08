from os import getenv
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

daily_sales_queue = "daily_sales"
bill_automation_queue = "bill_automation"
exchange = "nimble_io"
amqp_uri = "localhost"

root = getenv("root")
daily_sales_domain = getenv("daily_sales_domain")

mongo_client = MongoClient(getenv("mongodb_uri"))
