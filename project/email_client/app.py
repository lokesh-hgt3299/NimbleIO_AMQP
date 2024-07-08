from fastapi import FastAPI, APIRouter, Request, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from msal import ConfidentialClientApplication

import threading, requests
from os import getenv
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import Any, Dict

load_dotenv()

app = FastAPI()
bill_automation = APIRouter(prefix="/bill_automation")
daily_sales = APIRouter(prefix="/daily_sales")

scopes = ["https://graph.microsoft.com/.default"]
microsoft_url = "https://graph.microsoft.com/v1.0"

publish_url = "https://bb66-103-140-18-66.ngrok-free.app"

email_client_url = publish_url


def acquire_token(client_id, client_secret, tenant_id):
    app = ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )
    token_response = app.acquire_token_for_client(scopes=scopes)
    access_token = token_response.get("access_token")
    return access_token


def get_expiry_dt():
    #! Note: Maximum expirationDateTime is under 3 days.
    #! From microsoft documentation 4230 Minutes for mail resource. More than this it gives BadRequest.
    # * Recommended expirationDateTime is one day or 1410 minutes

    currentTime = datetime.now(timezone.utc)
    expireTime = currentTime + timedelta(minutes=1)
    return expireTime.astimezone().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def update_tokens():
    global bill_automation_token, daily_sales_token

    bill_automation_token = acquire_token(
        client_id=getenv("BILL_AUTOMATION_CLIENT_ID"),
        client_secret=getenv("BILL_AUTOMATION_CLIENT_SECRET"),
        tenant_id=getenv("BILL_AUTOMATION_TENANT_ID"),
    )

    daily_sales_token = acquire_token(
        client_id=getenv("DAILY_SALES_CLIENT_ID"),
        client_secret=getenv("DAILY_SALES_CLIENT_SECRET"),
        tenant_id=getenv("DAILY_SALES_TENANT_ID"),
    )

    """The default lifetime of an access token is variable. 
    When issued, an access token's default lifetime is assigned a random value ranging between 60-90 minutes (75 minutes on average)"""
    # Schedule the next update after 50 minutes
    threading.Timer(3000, update_tokens).start()  # 3000 seconds = 50 minutes


update_tokens()


def create_subscription(mail: str, folder: str, token: str, endpoint: str):
    payload = {
        "changeType": "updated",
        "notificationUrl": f"{publish_url}/{endpoint}/notification/",
        "lifecycleNotificationUrl": f"{email_client_url}/lifecycleNotification/",
        "resource": f"users/{mail}/mailFolders('{folder}')/messages",
        "expirationDateTime": get_expiry_dt(),
    }
    print(payload)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    return requests.post(
        url=f"{microsoft_url}/subscriptions",
        headers=headers,
        json=payload,
    )


def get_subscriptions(token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    return requests.get(
        url=f"{microsoft_url}/subscriptions",
        headers=headers,
    )


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


# ------------------- Bill Automation


@bill_automation.get("/get_token")
def get_token():
    return bill_automation_token


@bill_automation.get("/create_subscription/inbox")
def subscription():
    mail = "info@sendhours.com"
    folder = "inbox"
    response = create_subscription(
        mail,
        folder,
        bill_automation_token,
        "bill_automation",
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@bill_automation.get("/get_subscriptions")
def get_subscription():
    response = get_subscriptions(bill_automation_token)
    return JSONResponse(content=response.json(), status_code=response.status_code)


# ------------------- Daily Sales


@daily_sales.get("/get_token")
def get_token():
    return daily_sales_token


@daily_sales.get("/create_subscription/inbox")
def subscription():
    mail = "info@papillonlms.net"
    folder = "inbox"
    response = create_subscription(
        mail,
        folder,
        bill_automation_token,
        "daily_sales",
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@daily_sales.get("/get_subscriptions")
def get_subscription():
    response = get_subscriptions(daily_sales_token)
    return JSONResponse(content=response.json(), status_code=response.status_code)


# Include routers in the main app
app.include_router(bill_automation)
app.include_router(daily_sales)
