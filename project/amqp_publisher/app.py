import emit
from fastapi import FastAPI, Response, BackgroundTasks, Request
import pika

from fastapi.responses import JSONResponse
from typing import Dict, Any

from utils.variable import amqp_uri, exchange, bill_automation_queue, daily_sales_queue

emit.setup_rabbitmq()

app = FastAPI()


class Bg_Tasks:
    @staticmethod
    def add_to_queue(queue: str, message: str):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=amqp_uri))
        channel = connection.channel()
        channel.basic_publish(exchange=exchange, routing_key=queue, body=message)

        connection.close()


@app.post("/bill_automation/notification/")
def handle_notification(
    request: Request,
    background_tasks: BackgroundTasks,
    data: Dict[Any, Any] | None = None,
):
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        return Response(
            content=validation_token, status_code=200, media_type="text/plain"
        )
    else:
        resource = data["value"][0]["resource"]
        background_tasks.add_task(
            Bg_Tasks.add_to_queue,
            bill_automation_queue,
            resource,
        )
    return JSONResponse(content="", status_code=200, media_type="text/plain")


@app.post("/daily_sales/notification/")
def handle_notification(
    request: Request,
    background_tasks: BackgroundTasks,
    data: Dict[Any, Any] | None = None,
):
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        return Response(
            content=validation_token, status_code=200, media_type="text/plain"
        )
    else:
        resource = data["value"][0]["resource"]
        background_tasks.add_task(
            Bg_Tasks.add_to_queue,
            daily_sales_queue,
            resource,
        )
    return JSONResponse(content="", status_code=200, media_type="text/plain")


@app.post("/lifecycleNotification/")
def handle_lifecycleNotification(
    request: Request,
    background_tasks: BackgroundTasks,
    data: Dict[Any, Any] | None = None,
):
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        return Response(
            content=validation_token, status_code=200, media_type="text/plain"
        )
    else:
        subscriptionId = data["value"][0]["subscriptionId"]
        print(subscriptionId)
        # background_tasks.add_task(Bg_Tasks.subscription_renewal, subscriptionId)
    return JSONResponse(content="", status_code=200, media_type="text/plain")
