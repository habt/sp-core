#!/bin/bash

python3 -m venv .venv || exit $?

. .venv/bin/activate

pip install -r requirements.txt || exit $?

set -a
. config.env
set +a

if [ "$USE_MOCK" = "true" ]; then
    export NET_PRED_URL=$MOCK_NET_PRED_URL
    export GPU_PRED_URL=$MOCK_GPU_PRED_URL
else
    export NET_PRED_URL=$TRUE_NET_PRED_URL
    export GPU_PRED_URL=$TRUE_GPU_PRED_URL
fi

uvicorn app.main:app --host 0.0.0.0 --port 6400 --log-level info

#rm -r .venv
