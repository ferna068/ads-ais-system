from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Aircraft:
    icao: str = None
    callsign: str = None
    altitude: int = None
    latitude: float = None
    longitude: float = None
    heading: int = None
    speed: int = None
    timestamp: datetime = field(default_factory=datetime.now)

    def valid(self) -> bool:
        return all([
            isinstance(self.icao, str) and len(self.icao) > 0,
            isinstance(self.callsign, str) and len(self.callsign) > 0,
            isinstance(self.altitude, (int, float)) and self.altitude >= 0,
            isinstance(self.latitude, (int, float)) and -90 <= self.latitude <= 90,
            isinstance(self.longitude, (int, float)) and -180 <= self.longitude <= 180,
            isinstance(self.heading, (int, float)) and 0 <= self.heading <= 360,
            isinstance(self.speed, (int, float)) and self.speed >= 0,
            isinstance(self.timestamp, datetime)
        ])

@dataclass
class AISTrame:
    nmea_message: str = None