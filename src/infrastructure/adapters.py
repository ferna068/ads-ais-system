from datetime import timezone
from typing import Dict, Optional, Callable, Awaitable, Set, Tuple
from src.domain.ports import IReceiver, ISender, IAISMessageBuilder
from src.domain.models import Aircraft, AISTrame
from src.infrastructure.utils import TimestampAdjuster
import asyncio
import logging

logger = logging.getLogger(__name__)

class TCPADSReceiver(IReceiver):
    def __init__(self, host: str, port: int, adjuster: TimestampAdjuster, reconnect_delay: float = 5.0):
        self.host = host
        self.port = port
        self.adjuster = adjuster
        self.reconnect_delay = reconnect_delay
        self.aircrafts: Dict[str, Aircraft] = {}
        self.task: Optional[asyncio.Task] = None
        self.stopping = asyncio.Event()
        self.callback: Callable[[Aircraft], Awaitable[None]] | None = None
        logger.info(f"Initialized TCPADSReceiver with host: {host}, port: {port}, reconnect_delay: {reconnect_delay}")
    
    def register_callback(self, callback: Callable[[Aircraft], Awaitable[None]]) -> None:
        self.callback = callback
        logger.info(f"Registered callback for TCPADSReceiver")

    def start(self) -> None:
        if not self.task:
            self.stopping.clear()
            self.task = asyncio.create_task(self.run())
            logger.info(f"Started TCPADSReceiver")

    def stop(self) -> None:
        self.stopping.set()
        if self.task:
            self.task.cancel()
        self.task = None
        logger.info(f"Stopped TCPADSReceiver")
    
    async def run(self) -> None:
        while not self.stopping.is_set():
            try:
                logger.info(f"Connecting to {self.host}:{self.port}")
                reader, writer = await asyncio.open_connection(self.host, self.port)
                try:
                    while not self.stopping.is_set() and self.callback:
                        line = await reader.readline()
                        if not line:
                            break
                        text = line.decode('utf-8', errors='ignore').strip()
                        if not text:
                            continue

                        aircraft = self.parse_aircraft(text)
                        self.aircrafts[aircraft.icao] = aircraft

                        if aircraft.valid():
                            logger.info(f"Sending aircraft {aircraft.icao} to callback")
                            await self.callback(aircraft)
                finally:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception as e:
                        logger.error(f"Error closing writer: {e}")
            except Exception as e:
                logger.error(f"Error in TCPADSReceiver: {e}")
                await asyncio.sleep(self.reconnect_delay)
                continue
    
    def parse_aircraft(self, text: str) -> Optional[Aircraft]:
        try:
            logger.info(f"Parsing aircraft: {text}")    

            parts = text.strip().split(',')

            if len(parts) < 22 or not parts[0].startswith('MSG'):
                return None
            
            msg_type = int(parts[1])
            icao = parts[4].strip()
            timestamp = self.adjuster.adjust(f"{parts[6]} {parts[7]}")
            callsign = parts[10].strip() or None
            altitude = int(parts[11]) if parts[11] else None
            speed = float(parts[12]) if parts[12] else None
            heading = float(parts[13]) if parts[13] else None
            latitude = float(parts[14]) if parts[14] else None
            longitude = float(parts[15]) if parts[15] else None

            aircraft = self.aircrafts.get(icao, Aircraft(icao=icao))

            logger.info(f'Decoding message type {msg_type}...')
            
            if msg_type == 1:
                return Aircraft(
                    icao=aircraft.icao,
                    callsign=callsign if callsign else aircraft.callsign,
                    altitude=aircraft.altitude,
                    latitude=aircraft.latitude,
                    longitude=aircraft.longitude,
                    heading=aircraft.heading,
                    speed=aircraft.speed,
                    timestamp=timestamp
                )                
            elif msg_type == 2:
                return Aircraft(
                    icao=aircraft.icao,
                    callsign=aircraft.callsign,
                    altitude=aircraft.altitude,
                    latitude=latitude,
                    longitude=longitude,
                    heading=heading,
                    speed=speed,
                    timestamp=timestamp
                )
            elif msg_type == 3:
                return Aircraft(
                    icao=aircraft.icao,
                    callsign=aircraft.callsign,
                    altitude=altitude,
                    latitude=latitude,
                    longitude=longitude,
                    heading=aircraft.heading,
                    speed=aircraft.speed,
                    timestamp=timestamp
                )
            elif msg_type == 4:
                return Aircraft(
                    icao=aircraft.icao,
                    callsign=aircraft.callsign,
                    altitude=aircraft.altitude,
                    latitude=aircraft.latitude,
                    longitude=aircraft.longitude,
                    heading=heading,
                    speed=speed,
                    timestamp=timestamp
                )
            elif msg_type == 5:
                return Aircraft(
                    icao=aircraft.icao,
                    callsign=callsign if callsign else aircraft.callsign,
                    altitude=altitude,
                    latitude=aircraft.latitude,
                    longitude=aircraft.longitude,
                    heading=aircraft.heading,
                    speed=aircraft.speed,
                    timestamp=timestamp
                )
            elif msg_type == 6:
                return Aircraft(
                    icao=aircraft.icao,
                    callsign=callsign if callsign else aircraft.callsign,
                    altitude=aircraft.altitude,
                    latitude=aircraft.latitude,
                    longitude=aircraft.longitude,
                    heading=aircraft.heading,
                    speed=aircraft.speed,
                    timestamp=timestamp
                )
            elif msg_type == 7:
                return Aircraft(
                    icao=aircraft.icao,
                    callsign=aircraft.callsign,
                    altitude=altitude,
                    latitude=aircraft.latitude,
                    longitude=aircraft.longitude,
                    heading=aircraft.heading,
                    speed=aircraft.speed,
                    timestamp=timestamp
                )
            elif msg_type == 8:
                return Aircraft(
                    icao=icao,
                    callsign=aircraft.callsign,
                    altitude=aircraft.altitude,
                    latitude=aircraft.latitude,
                    longitude=aircraft.longitude,
                    heading=aircraft.heading,
                    speed=aircraft.speed,
                    timestamp=timestamp
                )
        except Exception as e:
            logger.error(f"Error parsing aircraft: {e}")
            return None
    
class TCPAISMessageSender(ISender):
    def __init__(self, host: str = '127.0.0.1', port: int = 4002):
        self.host = host
        self.port = port
        self.server: asyncio.base_events.Server | None = None
        self.clients: Set[asyncio.StreamWriter] = set()
        self.lock = asyncio.Lock()
        logger.info(f"Initialized TCPAISMessageSender with host: {host}, port: {port}")
    
    async def start(self) -> None:
        self.server = await asyncio.start_server(self.connect_client, self.host, self.port, backlog=100)
        logger.info(f"Started TCPAISMessageSender on {self.host}:{self.port}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        async with self.lock:
            for w in list(self.clients):
                try:
                    w.close()
                    await w.wait_closed()
                except Exception as e:
                    logger.error(f"Error closing client: {e}")
            self.clients.clear()
            logger.info(f"Stopped TCPAISMessageSender")
    
    async def send(self, message: str) -> None:
        data = f'{message}\n'.encode('utf-8')
        async with self.lock:
            for w in list(self.clients):
                try:
                    w.write(data)
                    await w.drain()
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    try:
                        w.close()
                        await w.wait_closed()
                    except Exception as e:
                        logger.error(f"Error closing client: {e}")
                    self.clients.discard(w)
    
    async def connect_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.clients.add(writer)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
        finally:
            self.clients.discard(writer)
            logger.info(f"Disconnected client: {writer.get_extra_info('peername')}")
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing writer: {e}")

class AisMessageBuilder(IAISMessageBuilder):
    def __init__(self):
        self.lock = asyncio.Lock()
        logger.info(f"Initialized AisMessageBuilder")
    
    def to_bits(self, value: int, length: int, signed: bool = False) -> str:
        if signed and value < 0:
            value = (1 << length) + value
        return format(value & ((1 << length) - 1), f'0{length}b')
    
    def deg_to_ais_lon(self, lon: float) -> int:
        return int(round(lon * 60 * 10000))
    
    def deg_to_ais_lat(self, lat: float) -> int:
        return int(round(lat * 60 * 10000))

    def sixbit_encode(self, bitstring: str) -> Tuple[str, int]:
        table = [chr(i + 48) if i < 40 else chr(i + 56) for i in range(64)]
        pad = (6 - (len(bitstring) % 6)) % 6
        bitstring_padded = bitstring + '0' * pad
        payload = ''
        for i in range(0, len(bitstring_padded), 6):
            sextet = bitstring_padded[i:i+6]
            payload += table[int(sextet, 2)]
        return payload, pad

    def nmea_checksum(self, body: str) -> str:
        cs = 0
        for ch in body:
            cs ^= ord(ch)
        return format(cs, '02X')

    async def build_ais_type9_trame(self, aircraft: Aircraft) -> AISTrame:
        async with self.lock:
            nmea_message = f"!AIVDM,1,1,,B,1234567890,0*5A"

            bits = ''
            bits += self.to_bits(9, 6)                                                      # message type
            bits += self.to_bits(0,2)                                                       # repeat
            bits += self.to_bits(int(aircraft.icao[:6], 16), 30)                            # mmsi
            bits += self.to_bits(int(round(aircraft.altitude * 0.3048)), 12)                # altitude
            bits += self.to_bits(int(aircraft.speed), 10)                                   # sog
            bits += self.to_bits(1, 1)                                                      # position accuracy
            bits += self.to_bits(self.deg_to_ais_lon(aircraft.longitude), 28, signed=True)  # longitude
            bits += self.to_bits(self.deg_to_ais_lat(aircraft.latitude), 27, signed=True)   # latitude
            bits += self.to_bits(int(round(aircraft.heading * 10)) % 4096, 12)              # cog
            bits += self.to_bits(aircraft.timestamp.astimezone(timezone.utc).second, 6)     # timestamp utc
            bits += self.to_bits(0, 8)                                                      # regional
            bits += self.to_bits(0, 1)                                                      # dte
            bits += self.to_bits(0, 3)                                                      # spare 
            bits += self.to_bits(0, 1)                                                      # assigned
            bits += self.to_bits(0, 1)                                                      # raim
            bits += self.to_bits(0, 20)                                                     # radio status

            if len(bits) != 168:
                bits = bits[:168].ljust(168, '0')

            payload, pad = self.sixbit_encode(bits)
            body = f'AIVDM,1,1,,A,{payload},{pad}'
            checksum = self.nmea_checksum(body)
            nmea_message = f'!{body}*{checksum}'

            return AISTrame(nmea_message=nmea_message)
