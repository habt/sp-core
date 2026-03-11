
import logging
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.library.data import led_states, mapping


def log_error(message:str):
    logging.error(message)

def log_info(message:str):
    logging.info(message)

def server_id_to_led(server_id: str) -> str:
    return mapping.get(server_id, None)

def get_led_color(led_id: str):
    if led_id == "led1":
        return "green"
    elif led_id == "led2":
        return "yellow"
    elif led_id == "led3":
        return "blue"
    elif led_id == "led4":
        return "red"
    else:
        logging.error(f"Unknown LED id {led_id}")
        return None

def update_led_states(server_id: str, is_best: bool = True, disabeled: bool = False):
    led_id = server_id_to_led(server_id)
    if led_id:
        for led in led_states:
            if led == led_id:
                if disabeled:
                    led_states[led] = "grey"
                elif is_best:
                    active_led_color = get_led_color(led)
                    if active_led_color  is not None:
                        led_states[led] = active_led_color
                    else:
                        led_states[led] = "red"
                else:
                    led_states[led] = "grey"
            else:
                if not disabeled:
                    led_states[led] = "grey"
    print(f"Updated LED states: {led_states} {server_id}")

