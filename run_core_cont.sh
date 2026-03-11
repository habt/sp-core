#!/bin/bash


export NET_PRED_URL=$TRUE_NET_PRED_URL
export GPU_PRED_URL=$TRUE_GPU_PRED_URL

uvicorn app.main:app --host 0.0.0.0 --port 6400 --log-level info


# docker build -t sp_core:v1 .
# docker run -p 6400:6400 --env-file config.env sp_core:v1