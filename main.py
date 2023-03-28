import uvicorn
import os
import json
import requests
import openai
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from fastapi import FastAPI


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    print("Starting webserver...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        debug=os.getenv("DEBUG", False),
        log_level=os.getenv('LOG_LEVEL', "info"),
        proxy_headers=True
    )