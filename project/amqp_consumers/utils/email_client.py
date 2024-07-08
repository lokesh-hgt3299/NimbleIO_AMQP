import requests, base64

microsoft_url = "https://graph.microsoft.com/v1.0"


def get_mail(resource, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    response = requests.get(
        url=f"{microsoft_url}/{resource}",
        headers=headers,
    )
    return response.json(), response.status_code


def get_attachments(email_id, token, mail):
    resource = f"users/{mail}/mailfolders/inbox/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    response = requests.get(
        url=f"{microsoft_url}/{resource}/{email_id}/attachments",
        headers=headers,
    )

    attachments = response.json()["value"]

    attachments_list = []

    for attachment in attachments:
        attachment_name = attachment["name"]

        if "contentBytes" in attachment:
            file_data = base64.b64decode(attachment["contentBytes"])
        else:
            res = requests.get(
                f"{microsoft_url}/{resource}/{email_id}/attachments/{attachment['id']}/$value",
                headers=headers,
            )
            file_data = res.content

        attachments_list.append(
            {
                "filename": attachment_name,
                "source_filename": attachment_name,
                "content_bytes": file_data,
            }
        )

    return attachments_list
