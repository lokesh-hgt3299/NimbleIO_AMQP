import pika
from utils.variable import amqp_uri, exchange, bill_automation_queue, daily_sales_queue


def setup_rabbitmq():
    # Connection parameters
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=amqp_uri))
    channel = connection.channel()

    # Declare the exchange as direct
    channel.exchange_declare(exchange=exchange, exchange_type="direct")

    # Declare the queues
    channel.queue_declare(queue=bill_automation_queue)
    channel.queue_declare(queue=daily_sales_queue)

    # Bind the queues to the exchange with specific routing keys
    channel.queue_bind(
        exchange=exchange,
        queue=bill_automation_queue,
        routing_key=bill_automation_queue,
    )
    channel.queue_bind(
        exchange=exchange,
        queue=daily_sales_queue,
        routing_key=daily_sales_queue,
    )

    # Close the connection
    connection.close()
