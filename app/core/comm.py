import time
import requests
import asyncio
import sys
import json
import logging
import os

logging.basicConfig(level=logging.INFO)  #TODO: use the env settings instead of hardcoding the level here


class ServicePlannerComm():
    
    def __init__(self):
        self.timeout = 5
        self.client_websocket = None
        self.gpu_data_url = os.getenv("GPU_PRED_URL")  #TODO: add fallback if env variable is not set
        self.net_data_url = os.getenv("NET_PRED_URL")  #TODO: add fallback if env variable is not set

    # Requests the GPU prediction from the GPU prediction module
    def request_gpu_update(self):
        logging.info(f"Requesting GPU predictions from {self.gpu_data_url} with timeout {self.timeout} seconds...")

        try:
            response = requests.get(
                self.gpu_data_url,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logging.error("Request for GPU update failed:", e)
            return None

    # Requests network prediction update from the network prediction/estimation service
    def request_net_update(self):
        logging.info(f"Requesting Network predictions from {self.net_data_url} with timeout {self.timeout} seconds...")

        try:
            response = requests.get(
                self.net_data_url,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        
        except requests.exceptions.RequestException as e:
            logging.error("Request for net update failed:", e)
            return None

    # Set the websocket used to communicate with the SP agent
    def set_websocket(self, websocket):
        self.client_websocket = websocket


    # Sends network recommendation to SP agent
    async def send_recommendation(self, type, data):
        logging.info(f"Sending ip address {data} through websocket")
        
        if self.client_websocket is None:
            logging.error("Websocket connection not established. Cannot send data.")
            return
        
        await self.client_websocket.send_json({
            "ts": int(time.time()),
            "payload": {
                "type": type,
                "server_endpoint_ip": data,
                "network_path": "x"
            }
        })

    # Receives recommendation request from SP agent
    async def receive_recommendation_request(self):
        msg = await self.client_websocket.receive_text()

        data = json.loads(msg)

        logging.info("Received:-----", data)

        return data