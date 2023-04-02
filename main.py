"""
Discord ChatGPT bot
"""
import os
import logging
from typing import Annotated, Optional, List

import json
import uvicorn

import requests
import openai
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel

PUBLIC_KEY = os.getenv("APPLICATION_PUBLIC_KEY")
openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")

verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))


class Channel(BaseModel):
    flags: int
    guild_id: str
    id: str
    last_message_id: str
    name: str
    nsfw: bool
    parent_id: str
    permissions: str
    position: int
    rate_limit_per_user: int
    topic: Optional[str]
    type: int


class Option(BaseModel):
    name: str
    type: int
    value: str


class Data(BaseModel):
    id: str
    name: str
    options: List[Option]
    type: int


class User(BaseModel):
    avatar: str
    avatar_decoration: Optional[str]
    discriminator: str
    display_name: Optional[str]
    global_name: Optional[str]
    id: str
    public_flags: int
    username: str


class Member(BaseModel):
    avatar: Optional[str]
    communication_disabled_until: Optional[str]
    deaf: bool
    flags: int
    is_pending: bool
    joined_at: str
    mute: bool
    nick: Optional[str]
    pending: bool
    permissions: str
    premium_since: Optional[str]
    roles: List[str]
    user: User


class Application(BaseModel):
    app_permissions: Optional[str]
    application_id: str
    channel: Optional[Channel]
    channel_id: Optional[str]
    data: Optional[Data]
    entitlement_sku_ids: Optional[List[str]]
    entitlements: Optional[List[str]]
    guild_id: Optional[str]
    guild_locale: Optional[str]
    id: str
    locale: Optional[str]
    member: Optional[Member]
    token: str
    type: int
    user: Optional[User]
    version: int


class Application2(BaseModel):
    application_id: str
    id: str
    token: str
    type: int
    user: User
    version: int


logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.post("/interaction")
async def interaction(
    background_tasks: BackgroundTasks,
    application: Application,
    x_signature_ed25519: Annotated[str, Header()] = None,
    x_signature_timestamp:  Annotated[str, Header()] = None,
):

    if application.type == 1:
        app_dict = application.dict(
            exclude={
                "app_permissions",
                "channel",
                "channel_id",
                "data",
                "entitlement_sku_ids",
                "entitlements",
                "guild_id",
                "guild_locale",
                "locale",
                "member"
            }
        )
    elif application.type == 2:
        app_dict = application.dict(
            exclude={
                "user"
            }
        )

    json_body = json.dumps(app_dict, separators=(',', ':'))
    message = (x_signature_timestamp.encode() + bytes(json_body.encode()))

    try:
        verify_key.verify(message, bytes.fromhex(x_signature_ed25519))
        logging.info(f"Signature verification succeeded for {json_body}")
    except (BadSignatureError, KeyError) as exc:
        logging.warning(f"Signature verification failed for {json_body}")
        raise HTTPException(status_code=401) from exc

    if application.type == 1:
        return {"type": 1}
    elif application.type == 2:
        response_content = f"Question from {application.member.user.username}: {application.data.options[0].value}"
        response = {"type": 4, "data": {"content": response_content}}
        openai_content = {
            "token": application.token,
            "application_id": application.application_id,
            "signature": x_signature_ed25519,
            "timestamp": x_signature_timestamp,
            "orig_body": app_dict,
            "orig_data": application.data.options[0].value
        }
        background_tasks.add_task(check_openai, message=openai_content)
        return response


def check_openai(message: str):
    completion = openai.ChatCompletion.create(
       model="gpt-3.5-turbo", messages=[{"role": "user", "content": message["orig_data"]}])
    result = completion.choices[0].message.content
    url = f'https://discord.com/api/v10/webhooks/{message["application_id"]}/{message["token"]}'
    payload = {
            "content": result
    }
    return requests.post(url, json=payload, timeout=20)


if __name__ == "__main__":
    print("Starting webserver...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        log_level="info",
        proxy_headers=True
        # ssl_keyfile="./cert.key",
        # ssl_certfile="./cert.cer",
        # ssl_ca_certs="./ca.cer",
        # reload=True
    )
