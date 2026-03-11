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
        self.get_routes = {}
        self.post_routes = {}
        if debug is DebugLevel.INFO:
            logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO, datefmt='%Y/%m/%d %I:%M:%S')
        elif debug is DebugLevel.DEBUG:
            logging.basicConfig(format='%(levelname)s - [%(asctime)s] %(message)s', level=logging.DEBUG, datefmt='%Y/%m/%d %I:%M:%S')

    async def start(self) -> None:
        logging.info("serving HTTP App on %s port %s (http://%s:%s)", self.address[0], self.address[1], self.address[0], self.address[1])
        self.server = await asyncio.start_server(self._connection_handler, self.address[0], self.address[1])

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.CancelledError:
                pass
        
    async def close(self) -> None:
        logging.info("shutdown HTTP on %s port %s", self.address[0], self.address[1])
        self.server.close()
        await self.server.wait_closed()

    async def _connection_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        details = await self._accept_handshake(reader, writer)


        logging.debug("GET routes: %s", self.get_routes)
        logging.debug("POST routes: %s", self.post_routes)

        try:
            if details["Request_Line"].Methode == Methode.GET.value:
                await self._response(writer, details, self.get_routes)
            elif details["Request_Line"].Methode == Methode.POST.value:
                logging.debug("post: %s", details["Message_Body"])
                await self._response(writer, details, self.post_routes)
            else:
                logging.warning("Methode not allowed: %s", details["Request_Line"].Methode)
        except KeyError as e:
            logging.error("unknown route: %s %s", details["Request_Line"].Methode, e)
            status_line = f"{details["Request_Line"].HTTP_Version} 404 Not Found\r\n"
            cors = f"Access-Control-Allow-Origin: {details["Origin"]}"
            writer.write((status_line + cors).encode())
            await writer.drain()

        await self._disconnect(writer)

    async def _response(self, writer: asyncio.StreamWriter, details: dict, routes:dict) -> None:
        status_line = f"{details["Request_Line"].HTTP_Version} 200 OK\r\n"
        cors = f"Access-Control-Allow-Origin: {details["Origin"]}"

        message = routes[details["Request_Line"].Request_URI]
        response = (status_line + cors + "\r\n" f"Content-Length: {len(message)}" + "\r\n\r\n" + message).encode()
        writer.write(response)
        await writer.drain()

        logging.info("%s %s %s", details["Request_Line"].Methode, details["Request_Line"].Request_URI, status_line)


    async def _accept_handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> dict:
        logging.debug("connection from: %s", writer.get_extra_info('peername'))

        header_data = {}

        data = await reader.read(1024)
        message = data.decode().split("\r\n\r\n")
        header_data.update({"Message_Body": message[1]})

        headers = message[0].split("\r\n")

        request_line = Request_Line(*headers[0].split(" "))
        header_data.update({"Request_Line": request_line})
        for line in headers:
            [header_data.update({item.value: line.split(": ")[1]}) for item in RequestTypes if not line.find(f"{item.value}:")]
        logging.debug("client request: %s", header_data)

        return header_data

    def get(self, route:str) -> None:
        def get_decorator(func: callable):
            self.get_routes.update({route: func()})
            return func
        return get_decorator

    def post(self, route:str) -> None:
        def post_decorator(func: callable):
            self.post_routes.update({route: func()})
            return func
        return post_decorator


    async def _disconnect(self, writer: asyncio.StreamWriter) -> None:
        logging.debug("close connection: %s", writer.get_extra_info("peername"))
        writer.close()
        await writer.wait_closed()
