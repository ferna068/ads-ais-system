from src.domain.ports import ISender
from src.domain.models import Aircraft, AISTrame
from src.domain.ports import IAISMessageBuilder
import logging

logger = logging.getLogger(__name__)

class ConvertAircraftToAISTrame:
    def __init__(self, sender: ISender):
        self.sender = sender

    async def execute(self, aircraft: Aircraft, builder: IAISMessageBuilder) -> None:
        if not (-90 <= aircraft.latitude <= 90) and not (-180 <= aircraft.longitude <= 180):
            logger.error(f"Invalid latitude or longitude: {aircraft.latitude}, {aircraft.longitude}")
            return
        
        trame: AISTrame = await builder.build_ais_type9_trame(aircraft)
        await self.sender.send(trame.nmea_message)
        logger.info(f"Sent AIS Type 9 trame: {trame.nmea_message}")