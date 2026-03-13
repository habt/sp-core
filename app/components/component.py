import logging
from collections import deque
from app.library.settings import DEFAULT_HISTORY_LENGTH, DEFAULT_SIGMA_LEVEL, DEFAULT_EWMA_ALPHA

class Component():

    def __init__(self):
        self.id = None
        self.pred_delay = None
        self.stdv_delay = None
        self.curr_delay = None
        self.ewma_delay = None
        self.ewma_alpha = DEFAULT_EWMA_ALPHA
        self.sigma_level = None
        self.delay_history = deque(maxlen=DEFAULT_HISTORY_LENGTH)

    def set_sigma_level(self, sigma_level: int):
        self.sigma_level = sigma_level


    def set_prediction(self, pred: float, var: float):
        logging.info(f"Setting predictions for {self.id}. Prediction: {pred}, Stddev: {var}")
        
        self.pred_delay = pred if pred is not None else float('nan')
        self.stdv_delay = var if var is not None else float('nan')
        
        self.update_curr_delay()
        self.update_ewma_delay()


    def update_curr_delay(self):
        self.sigma_level = DEFAULT_SIGMA_LEVEL if self.sigma_level is None else self.sigma_level
        
        self.curr_delay = self.pred_delay + self.stdv_delay * self.sigma_level
        self.delay_history.append(self.curr_delay)


    def update_ewma_delay(self):
        if self.ewma_delay is not None:
            self.ewma_delay = (1 - self.ewma_alpha) * self.ewma_delay + self.ewma_alpha * self.curr_delay
        else:
            self.ewma_delay = self.curr_delay
