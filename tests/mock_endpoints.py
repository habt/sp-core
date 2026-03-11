
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock GPU and Network Prediction Endpoints")

@app.get("/mock/gpuupdate")
def mock_gpu_update():
    gpu_data = {
        "predictions": [
            {"node_id": "jetson_1", "predicted_latency_mean_ms": 100, "uncertainty_std_ms": 10},
            {"node_id": "jetson_2", "predicted_latency_mean_ms": 150, "uncertainty_std_ms": 10},
            {"node_id": "jetson_3", "predicted_latency_mean_ms": 40, "uncertainty_std_ms": 20},
            {"node_id": "jetson_4", "predicted_latency_mean_ms": 1000, "uncertainty_std_ms": 5}
        ]
    }
    return JSONResponse(content=gpu_data)

@app.get("/mock/netupdate")
def mock_net_update():
    net_data = {
        "servers": {
            "Server_1_net": {"server_id": "Server_1_net", "delay_ms": 50, "delay_std_ms": 15},
            "Server_2_net": {"server_id": "Server_2_net", "delay_ms": 70, "delay_std_ms": 25},
            "Server_3_net": {"server_id": "Server_3_net", "delay_ms": 50, "delay_std_ms": 15},
            "Server_4_net": {"server_id": "Server_4_net", "delay_ms": 70, "delay_std_ms": 25}
        }
    }
    return JSONResponse(content=net_data)
