import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.library.data import *
from app.core.core import *
from app.core.comm import *
from app.library.data import ControlData, led_states
from app.library.helper import log_error, log_info, update_led_states


level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(level=logging.INFO)  #TODO: use the env settings instead of hardcoding the level here

sp_comm = ServicePlannerComm()
sp_core = ServicePlannerCore(sp_comm)
client_websockets = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await sp_core.start_periodic_update()
    yield
    await sp_core.stop_periodic_update()

def init_fastapi_app(sp_core) -> FastAPI:


    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

app = init_fastapi_app(sp_core)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

@app.get("/")
def read_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.websocket("/corews")
async def recommendation_websocket_endpoint(websocket: WebSocket):
    logging.info("Waiting for websocket connection from client ....")
    
    await websocket.accept()
    sp_core.comm.set_websocket(websocket)
    
    asyncio.create_task(sp_core.handle_recommendation_requests())
    while True:
         await asyncio.sleep(1)


@app.get("/led/status")
def get_status():
    update_led_states(
        sp_core.best_server.get_id() if sp_core.best_server else "jetson_1", 
        is_best=True)
    return led_states

@app.get("/set/{led}/{color}")
def set_led(led: str, color: str):
    if led in led_states and color in ["red", "green", "yellow", "blue", "off"]:
        led_states[led] = color
        return {"success": True, "led": led, "color": color}
    return {"error": "Invalid LED or color"}


@app.post("/control")
def update_control(data: ControlData):
    global control_state
    control_state = data.dict()
    logging.info("Received control data:", control_state)
    try:
        result = sp_core.set_parameters(control_state)
        if result:
            return {"success": True, "message": "parameters updated"}
        else:
            return {"success": False, "received": "Failed to update parameters"}
    
    except Exception as e:
        logging.exception("Error setting parameters")
        return {"success": False, "error": str(e)}


@app.post("/toggle")
def toggle_core(toggle: ToggleData):
    try:
        result = sp_core.set_status(toggle.command)

        if isinstance(result, bool):
            if result:
                return {"success": True, "message": f"Core set to {toggle.command}"}
            return {"success": False, "message": f"Core rejected command: {toggle.command}"}
        
    except Exception as e:
        logging.exception("Error toggling core")
        return {"success": False, "error": str(e)}