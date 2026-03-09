import asyncio
import logging

type Address = tuple[str, int]
    
class HttpRequestHandler:
    def __init__(self, address: Address) -> None:
        self.address = address
        self.server = None

    async def start(self):
        logging.info("start socket: %s", self.address)
        self.server = await asyncio.start_server(self.connection_handler, self.address[0], self.address[1])

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.CancelledError:
                pass
    async def connection_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await self.accept_handshake(reader, writer)

    async def accept_handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        logging.info("new connection from > %s", writer.get_extra_info('peername'))

        data = await reader.read(1024)
        print(data)

if __name__ == "__main__":
    http_server = HttpRequestHandler(["127.0.0.1", "80"])

    asyncio.run(http_server.start())
