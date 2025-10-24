from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TimestampAdjuster:
    def __init__(self):
        self.start_time = datetime.now()
        self.base_epoch = datetime(1970, 1, 1)
    
    def adjust(self, str_timestamp: str) -> datetime:
        try:
            timestamp = datetime.strptime(str_timestamp, "%Y/%m/%d %H:%M:%S.%f")
            delta = timestamp - self.base_epoch
            adjusted_time = self.start_time + delta
            return adjusted_time
        except Exception as e:
            logger.error(f"Error ajusting timestamp: {e}")
            return self.start_time