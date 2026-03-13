---

# Service Planner Core (SP Core)

SP Core is a **service selection system** consisting of a **browser-based frontend** and a **Python backend** that ingests predictions, calculates delays, and selects the best server for connections.

The system evaluates predicted **GPU and network delays**, applies **smoothing and stability mechanisms**, and determines the optimal server based on configurable policies.

---

# Overview

SP Core consists of:

* **Frontend**

  * Browser UI for monitoring system state
  * Allows configuration of selection parameters

* **Backend Core**

  * Fetches prediction data from services
  * Computes connection delays
  * Applies smoothing and stability logic
  * Selects the best server

---

# Architecture

```
Predictions (GPU / Network)
        │
        ▼
Communication Layer
        │
        ▼
ServicePlannerCore
        │
        ├── Update component predictions
        ├── Compute sigma delays
        ├── Compute EWMA delays
        └── Select best server
        │
        ▼
Frontend polls system status
        │
        ▼
Frontend may update control parameters
```

---

# Project Structure

```
sp_core/
│
├── app/
│   ├── core/
│   │   └── core.py                # ServicePlannerCore logic
│   │
│   ├── components/
│   │   └── component.py           # Server/link component logic
│   │
│   └── frontend/
│       └── index.html             # Web UI
│
├── tests/
│   └── gpu_net_mock_endpoints.py  # Mock prediction endpoints
│
├── config.env                     # Runtime configuration
│
└── docker-compose.yml
```

---

# Running SP Core

To start SP Core on the server:

```bash
cd sp_core
docker compose up
```

The frontend will be available at:

```
http://172.22.232.194:6400/
```

---

# Backend Core

File:

```
app/core/core.py
```

Main class:

```
ServicePlannerCore
```

Responsibilities:

* Load topology (servers, links, connections)
* Poll prediction services
* Maintain prediction history
* Compute smoothed delays
* Select the best server
* Expose status API
* Accept control updates from frontend

---

# Components

File:

```
app/components/component.py
```

The `Component` class represents **servers and network links**.

State maintained per component:

* `pred_delay`
* `stdv_delay`
* `sigma_delay`
* `ewma_delay`
* `delay_history`
* `ewma_alpha`
* `sigma_level`

Methods:

```python
set_prediction()
update_sigma_delay()
update_ewma_delay()
```

These methods manage smoothing and delay history updates.

---

# Communication Layer

Responsible for retrieving predictions from:

* Real prediction services
* Local mock services

Functions used:

```
comm.request_gpu_update()
comm.request_net_update()
```

Endpoints are configured via `config.env`.

---

# Configuration

File:

```
config.env
```

This file controls runtime behavior such as prediction endpoints, thresholds, and refresh intervals.

| Variable               | Description                                       |
| ---------------------- | ------------------------------------------------- |
| USE_MOCK               | Use mock endpoints instead of real services       |
| TRUE_NET_PRED_URL      | Network prediction service URL                    |
| TRUE_GPU_PRED_URL      | GPU prediction service URL                        |
| MOCK_NET_PRED_URL      | Mock network prediction endpoint                  |
| MOCK_GPU_PRED_URL      | Mock GPU prediction endpoint                      |
| TOPOLOGY_FILE          | Path to topology JSON                             |
| KEEP_ALIVE_INTERVAL    | Keep-alive interval in seconds                    |
| CORE_REFRESH_INTERVAL  | Core update loop interval                         |
| HYSTERISIS_THRESHOLD   | Hysteresis counter threshold (currently not used) |
| SIGMA_THRESHOLD        | Number of standard deviations used in sigma delay |
| EWMA_COEFFICIENT       | EWMA smoothing coefficient                        |
| SWITCHING_THRESHOLD_MS | Minimum improvement required to switch servers    |
| DEFAULT_SERVER         | Fallback server when data is unavailable          |

Note: Environment variables are loaded as **strings** and converted to appropriate types in code.

---

# Delay Calculation

## Sigma Delay

A conservative delay estimate based on prediction uncertainty.

```
sigma_delay = pred_delay + sigma_level * stdv_delay
```

---

## EWMA Delay

Exponentially Weighted Moving Average used to smooth delay measurements.

```
ewma_next = (1 - alpha) * ewma_prev + alpha * new_sample
```

Where:

* `alpha` = EWMA coefficient
* Higher values → faster responsiveness

---

# Server Selection

Server selection uses:

* **EWMA-based comparison**
* **Switching threshold**
* **Hysteresis counter**

These mechanisms prevent rapid server switching (flapping).

---

# Frontend

File:

```
app/frontend/index.html
```

Responsibilities:

* Display system status via LED panel
* Allow runtime parameter configuration
* Poll backend for updates

Frontend periodically calls:

```
GET /led/status
```

Control updates are sent using:

```
POST /control
```

---

# Frontend Configuration Parameters

The following parameters can be adjusted via the web UI.

---

## Sigma Level

Input:

```
value3
```

Type: Integer
Range: `0 – 6`

Purpose:

```
sigma_delay = pred_delay + sigma_level * stdv_delay
```

---

## EWMA Coefficient

Input:

```
value4
```

Type: Float
Range: `0.0 – 1.0`

Purpose:

```
ewma_next = (1 - alpha) * ewma_prev + alpha * new_sample
```

---

## Hysteresis Threshold

Input:

```
value2
```

Type: Integer
Range: `>= 0`

Purpose:

Number of consecutive cycles required before switching servers.

Prevents frequent server changes.

---

## Refresh Interval

Input:

```
value5
```

Type: Seconds
Range: `>= 1`

Controls frontend polling interval.

---

# Frontend → Backend Control Payload

Example JSON payload sent to backend:

```json
{
  "sigma": 2,
  "ewma": 0.8,
  "hysteresis": 4,
  "refresh_seconds": 10
}
```

---

# Stability & Timing

The backend runs a periodic update loop controlled by:

```
CORE_REFRESH_INTERVAL
```

Each cycle:

1. Fetch predictions
2. Update component states
3. Recalculate delays
4. Reevaluate server selection

---

# Debugging Tips

### Logging

Use percent-style logging to avoid formatting issues.

```python
logging.info("Prediction value: %s", value)
```

---

### NaN Protection

Ensure prediction inputs do not propagate `NaN` values into EWMA calculations.

---

### Mock Mode

To isolate external service issues:

```
USE_MOCK=true
```

This uses the local mock endpoints:

```
tests/gpu_net_mock_endpoints.py
```

---

# Development Notes

Key files to understand when modifying behavior:

| File                          | Purpose                                |
| ----------------------------- | -------------------------------------- |
| `app/core/core.py`            | Core orchestration and selection logic |
| `app/components/component.py` | Per-component delay calculations       |
| `app/frontend/index.html`     | UI and control panel                   |
| `config.env`                  | Runtime configuration                  |

---

