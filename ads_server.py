import asyncio
import logging
from tracemalloc import stop
import aiofiles
from typing import AsyncGenerator

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TCPADSSender:
    def __init__(self, host: str = '0.0.0.0', port: int = 4001, data_file: str = 'data/ads_data.log'):
        self.host = host
        self.port = port
        self.data_file = data_file
        self.server = None
        self.clients = set()
        logger.info(f"Initialized TCPADSSender with host: {host}, port: {port}")
    
    async def start(self) -> None:
        self.server = await asyncio.start_server(self.connect_client, self.host, self.port, backlog=100)
        logger.info(f"Started TCPADSSender on {self.host}:{self.port}")

        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self) -> None:
        if self.server:
            self.server.close()
        logger.info('Stop ADS Server')
    
    async def connect_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info('peername')
        logger.info(f"Connected client: {addr}")
        self.clients.add(writer)

        try:
            async for data in self.read_datafile():
                if not data.strip():
                    continue
                writer.write(data.encode('utf-8'))
                await writer.drain()

                logger.info(f"Sent ADS-B data to client -> {addr} : {data}")
                await asyncio.sleep(1)
        except (BrokenPipeError, ConnectionResetError):
            logger.warning(f"Client {addr} disconnected")
        except Exception as e:
            logger.error(f"Error in connect_client: {e}")
        finally:
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing writer: {e}")
            finally:
                self.clients.discard(writer)
                logger.info(f"Disconnected client: {addr}")

    async def read_datafile(self) -> AsyncGenerator[str, None]:
        while True:
            try:
                async with aiofiles.open(self.data_file, mode='r') as f:
                    async for line in f:
                        yield line
            except FileNotFoundError:
                logger.error(f"File {self.data_file} not found")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error reading datafile: {e}")
                await asyncio.sleep(5)

async def main():
    server = TCPADSSender()
    await server.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        