import pika
import os, sys, requests

from tasks import process_email

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.variable import bill_automation_queue, amqp_uri
from utils.email_client import get_mail


def callback(ch, method, properties, body: bytes):
    res = requests.get("http://localhost:8001/bill_automation/get_token")
    token = res.json()
    resource = body.decode()
    email, status = get_mail(resource, token)
    if status == 200:
        print(email["id"])
        process_email.delay(email=email)
    else:
        print("Error while initiate tasks", email)


# Connection parameters
connection = pika.BlockingConnection(pika.ConnectionParameters(host=amqp_uri))
channel = connection.channel()

# Declare the queue (ensuring it exists)
channel.queue_declare(queue=bill_automation_queue)

# Consume messages from the queue
channel.basic_consume(
    queue=bill_automation_queue,
    on_message_callback=callback,
    auto_ack=True,
)

print("Waiting for messages in daily_sales. To exit press CTRL+C")
channel.start_consuming()
