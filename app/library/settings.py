
NETS_KEY = "nets"
SERVERS_KEY = "gpus"
COMPS_KEY = "comps"

NET_PRED_ID_KEY = "server_id"
NET_PRED_KEY = "delay_ms"
NET_PRED_VAR_KEY = "delay_std_ms"
GPU_PRED_ID_KEY = "node_id"
GPU_PRED_KEY = "predicted_latency_mean_ms"
GPU_PRED_VAR_KEY = "uncertainty_std_ms"


# DEFAULT values for delay estimation
DEFAULT_SIGMA_LEVEL = 3  # default number of standard deviations to add to the mean prediction to get the sigma delay
DEFAULT_HISTORY_LENGTH = 5 # default length of the history
DEFAULT_EWMA_ALPHA = 0.5    # this is the default smoothing factor for the exponentially weighted moving average (EWMA) of delay estimates

# MAX delay values to be used when prediction is missing or very uncertain
MAX_SERVER_DELAY = 1000     #ms, upper bound on the delay of a server
MAX_SERVER_DELAY_VARIABILITY = 200      #ms, upper bound on the variability of a server's delay
MAX_NET_DELAY = 1000         #ms, upper bound on the delay of a network link
MAX_NET_DELAY_VARIABILITY = 200     #ms, upper bound on the variability of a network link's delay


