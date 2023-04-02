"""
Discord ChatGPT bot
"""
import os
import logging
from typing import Annotated

import json
import uvicorn

import requests
import openai
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Request

PUBLIC_KEY = os.getenv("APPLICATION_PUBLIC_KEY")
openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")

verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.post("/interaction")
async def interaction2(
    background_tasks: BackgroundTasks,
    request: Request,
    x_signature_ed25519: Annotated[str, Header()] = None,
    x_signature_timestamp:  Annotated[str, Header()] = None,
):

    request_body = await request.body()
    decoded_body = json.loads(request_body.decode("utf-8"))
    message = x_signature_timestamp.encode() + request_body
    try:
        verify_key.verify(message, bytes.fromhex(x_signature_ed25519))
        # logging.info(f"Signature verification succeeded for {request_body}")
    except (BadSignatureError, KeyError) as exc:
        # logging.warning(f"Signature verification failed for {request_body}")
        raise HTTPException(status_code=401) from exc

    if decoded_body['type'] == 1:
        return {"type": 1}
    elif decoded_body['type'] == 2:
        response_content = f"Question from {decoded_body['member']['user']['username']}: {decoded_body['data']['options'][0]['value']}"
        response = {"type": 4, "data": {"content": response_content}}
        openai_content = {
            "token": decoded_body['token'],
            "application_id": decoded_body['application_id'],
            "signature": x_signature_ed25519,
            "timestamp": x_signature_timestamp,
            "orig_body": decoded_body,
            "orig_data": decoded_body['data']['options'][0]['value']
        }
        background_tasks.add_task(check_openai, message=openai_content)
        return response
    return


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
