
import logging
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.library.data import led_colors, mapping


def log_error(message:str):
    logging.error(message)

def log_info(message:str):
    logging.info(message)

def server_id_to_led(server_id: str) -> str:
    return mapping.get(server_id, None)

def get_led_color(led_id: str):
    if led_id in led_colors.keys():
       return led_colors.get(led_id)
    else:
        logging.error(f"Unknown LED id {led_id}")
        return None

def update_led_states(server_id: str, is_best: bool = True, disabled: bool = False):
    active_led_id = server_id_to_led(server_id)
    led_states = {}
    if active_led_id:
        for led in led_colors:
            if led == active_led_id:
                if disabled:
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
                if not disabled:
                    led_states[led] = "grey"
        return led_states
    print(f"Updated LED states: {led_states} {server_id}")

