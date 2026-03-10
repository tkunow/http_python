import asyncio
import logging
from enum import Enum
from typing import NamedTuple

type Address = tuple[str, int]

class Methode(Enum):
    OPTIONS = "OPTIONS"
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    TRACE = "TRACE"
    CONNECT = "CONNECT"

class RequestTypes(Enum):
    HOST = "Host"
    CONNECTION = "Connection"
    SEC_CH_UA_PLATFORM = "sec-ch-ua-platform"
    USER_AGENT = "User-Agent"
    SEC_CH_UA = "sec-ch-ua"
    SEC_CH_UA_MOBILE = "sec-ch-ua-mobile"
    ACCEPT = "Accept"
    ORIGIN = "Origin"
    SEC_FETCH_SITE = "Sec-Fetch-Site"
    SEC_FETCH_MODE = "Sec-Fetch-Mode"
    SEC_FETCH_DEST = "Sec-Fetch-Dest"
    REFERER = "Referer"
    ACCEPT_ENCODING = "Accept-Encoding"
    ACCEPT_LANGUAGE = "Accept-Language"

class Request_Line(NamedTuple):
    Methode:str
    Request_URI:str
    HTTP_Version:str

class RequestHeader(NamedTuple):
    Request:Request_Line
    Host:str
    Connection:str
    sec_ch_ua_platform:str
    User_Agent:str
    sec_ch_ua:str
    sec_ch_ua_mobile:str
    Accept:str
    Origin:str
    Sec_Fetch_Site:str
    Sec_Fetch_Mode:str
    Sec_Fetch_Dest:str
    Referer:str
    Accept_Encoding:str
    Accept_Language:str

class DebugLevel(Enum):
    INFO=1
    DEBUG=2
    WARNING=3
    ERROR=4

class HttpRequestHandler:
    def __init__(self, address: Address, debug: DebugLevel | None = None) -> None:
        self.address = address
        self.server = None
        if debug is not None:
            logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

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
        headers = data.decode().split("\r\n")
        header_data = {}
        request_line = Request_Line(*headers[0].split(" "))
        header_data.update({"Request_Line": request_line})
        for line in headers:
            [header_data.update({item.value: line.split(": ")[1]}) for item in RequestTypes if not line.find(f"{item.value}:")]

        logging.info(header_data)
if __name__ == "__main__":
    http_server = HttpRequestHandler(["127.0.0.1", "80"], DebugLevel.INFO)

    asyncio.run(http_server.start())
