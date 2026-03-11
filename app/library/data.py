from enum import Enum
from pydantic import BaseModel
from typing import Optional
from app.library.settings import DEFAULT_EWMA_ALPHA, DEFAULT_HISTORY_LENGTH, DEFAULT_SIGMA_LEVEL

# --------- Data for frontend ---------#
class ControlData(BaseModel):
    update: Optional[int]   =   10
    hysteresis: Optional[float] =  10
    sigma: Optional[float]    =  DEFAULT_SIGMA_LEVEL
    ewma: Optional[float]  = DEFAULT_EWMA_ALPHA

led_states = {
    "led1": "green",
    "led2": "yellow",
    "led3": "blue",
    "led4": "orange"
    }

mapping = {
    "jetson_1": "led1",
    "jetson_2": "led2",
    "jetson_3": "led3",
    "jetson_4": "led4"
    }


# --------- Enums for update types ---------#
class Update(Enum):
    UNSOLICITED = "unsolicited_update"
    REQUESTED = "requested_update"