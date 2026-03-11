from app.components.component import Component
from app.library.settings import MAX_NET_DELAY, MAX_NET_DELAY_VARIABILITY, DEFAULT_SIGMA_LEVEL


class Network(Component):

    type = 'network'

    def __init__(self, meta):
        super().__init__()
        self.subtype = meta['subtype']

    def get_pred_delay(self) -> float:
        if self.pred_delay is None:
            return MAX_NET_DELAY
        return self.pred_delay

    def get_stdv_delay(self) -> float:
        if self.stdv_delay is None:
            return MAX_NET_DELAY_VARIABILITY
        return self.stdv_delay
    
    def get_sigma_delay(self) -> float:
        if self.sigma_delay is None:
            return MAX_NET_DELAY + DEFAULT_SIGMA_LEVEL * MAX_NET_DELAY_VARIABILITY
        return self.sigma_delay
    
    def get_ewma_delay(self) -> float:
        if self.ewma_delay is None:
            return MAX_NET_DELAY + DEFAULT_SIGMA_LEVEL * MAX_NET_DELAY_VARIABILITY
        return self.ewma_delay