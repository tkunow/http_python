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

class DebugLevel(Enum):
    INFO=1
    DEBUG=2
    WARNING=3
    ERROR=4

class HttpRequestHandler:
    def __init__(self, address: Address, debug: DebugLevel | None = None) -> None:
        self.address = address
        self.server = None
        self.routes = {}
        if debug is not None:
            logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    async def start(self) -> None:
        logging.info("start socket: %s", self.address)
        self.server = await asyncio.start_server(self._connection_handler, self.address[0], self.address[1])

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.CancelledError:
                pass
        
    async def close(self) -> None:
        logging.info("close socket")
        self.server.close()
        await self.server.wait_closed()

    async def _connection_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        details = await self._accept_handshake(reader, writer)

        status_line = f"{details["Request_Line"].HTTP_Version} 200 OK\r\n"
        cors = f"Access-Control-Allow-Origin: {details["Origin"]}"

        logging.info("routes: %s", self.routes)

        if details["Request_Line"].Methode == Methode.GET.value:

            try:
                message = self.routes[details["Request_Line"].Request_URI]
                response = (status_line + cors + "\r\n\r\n" + message).encode()
                writer.write(response)
                await writer.drain()

                logging.info("send response: %s", status_line)
            except KeyError as e:
                logging.error("unknown route: %s", e)
        else:
            logging.warning("Methode not allowed: %s", details["Request_Line"].Methode)

        await self._disconnect(writer)

    async def _accept_handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> dict:
        logging.info("new connection from > %s", writer.get_extra_info('peername'))

        data = await reader.read(1024)
        headers = data.decode().split("\r\n")
        header_data = {}
        request_line = Request_Line(*headers[0].split(" "))
        header_data.update({"Request_Line": request_line})
        for line in headers:
            [header_data.update({item.value: line.split(": ")[1]}) for item in RequestTypes if not line.find(f"{item.value}:")]
        logging.info(header_data)

        return header_data

    def get(self, route:str) -> None:
        def get_decorator(func: callable):
            self.routes.update({route: func()})
            return func
        return get_decorator


    async def _disconnect(self, writer: asyncio.StreamWriter) -> None:
        logging.info("close connection: %s", writer.get_extra_info("peername"))
        writer.close()
        await writer.wait_closed()
