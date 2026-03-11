from app.components.component import Component
from app.library.settings import MAX_SERVER_DELAY, MAX_SERVER_DELAY_VARIABILITY, DEFAULT_SIGMA_LEVEL, DEFAULT_HISTORY_LENGTH

class Gpu(Component):
    
    type = 'gpu'
    
    def __init__(self, meta):
        super().__init__()
        self.subtype = meta['subtype']
        self.address = meta['ip']
        self.id = meta['id']
        

    def get_id(self) -> str:
        return self.id

    def get_address(self) -> str:
        return self.address
    
    def get_pred_delay(self) -> float:
        if self.pred_delay is None:
            return MAX_SERVER_DELAY
        return self.pred_delay

    def get_stdv_delay(self) -> float:
        if self.stdv_delay is None:
            return MAX_SERVER_DELAY_VARIABILITY
        return self.stdv_delay
    
    def get_sigma_delay(self) -> float:
        if self.sigma_delay is None:
            return MAX_SERVER_DELAY + DEFAULT_SIGMA_LEVEL * MAX_SERVER_DELAY_VARIABILITY
        return self.sigma_delay
    
    def get_ewma_delay(self) -> float:
        if self.ewma_delay is None:
            return MAX_SERVER_DELAY + DEFAULT_SIGMA_LEVEL * MAX_SERVER_DELAY_VARIABILITY
        return self.ewma_delay