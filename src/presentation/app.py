from src.domain.models import Aircraft
from src.application.usecases import ConvertAircraftToAISTrame
from src.infrastructure.settings import SettingsReader
from src.infrastructure.adapters import TCPADSReceiver, TCPAISMessageSender, AisMessageBuilder
from src.infrastructure.utils import TimestampAdjuster
import logging
import asyncio

class Application:
    def __init__(self):
        self.adjuster = TimestampAdjuster()
        self.settings = SettingsReader().settings
        self.receiver = TCPADSReceiver(self.settings['ads_receiver_tcp']['host'], self.settings['ads_receiver_tcp']['port'], adjuster=self.adjuster)
        self.sender = TCPAISMessageSender(self.settings['ais_sender_tcp']['host'], self.settings['ais_sender_tcp']['port'])
        self.builder = AisMessageBuilder()
        self.usecase = ConvertAircraftToAISTrame(self.sender)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized Application")

    def stop(self) -> None:
        self.receiver.stop()
        self.sender.stop()
        self.logger.info(f"Application stopped")

    async def callback(self, aircraft: Aircraft) -> None:
        self.logger.info(f"Received aircraft: {aircraft}")
        await self.usecase.execute(aircraft, self.builder)

    async def run(self) -> None:
        self.receiver.register_callback(self.callback)
        self.receiver.start()
        asyncio.create_task(self.sender.start())
        self.logger.info(f"Application started")
        await asyncio.Future()

    