"""
Discord ChatGPT bot
"""
import os
# import json
import uvicorn

# import requests
# import openai
# from nacl.signing import VerifyKey
# from nacl.exceptions import BadSignatureError
# from azure.servicebus import ServiceBusClient, ServiceBusMessage
from fastapi import FastAPI, Header
# from typing import List, Optional
from pydantic import BaseModel

public_key = os.getenv("APPLICATION_PUBLIC_KEY")
sbs_connection_string = os.getenv("SBS_CONN_STR")
sbs_queue_name = os.getenv("SBS_QUEUE_NAME")

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.get("/")
def read_root():
    """Hello World"""
    return {"Hello": "World"}

@app.post("/items/")
async def create_item(item: Item):
    return item

# @app.post("/process_signature")
# async def read_items(user_agent: Annotated[str | None, Header()] = None):
#     return {"User-Agent": user_agent}


if __name__ == "__main__":
    print("Starting webserver...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        log_level=os.getenv("LOG_LEVEL", "info"),
        proxy_headers=True
    )
