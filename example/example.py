import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from http_server.http_server import HttpRequestHandler, request, DebugLevel
import asyncio
import json

async def main():
    app = HttpRequestHandler(["127.0.0.1", 8080], DebugLevel.DEBUG)
    @app.get("/test")
    def hello_world_get():
        return json.dumps({"data": "Hello World! from outer class"})

    @app.get("/inlinehtml")
    def inline_html_get():
        return "<p>Hello World!</p>"
    @app.post("/test")
    def hello_wold_post():
        print(request.get())
        return json.dumps({"data": "post succeeded"})

    try:
        await app.start()
    finally:
        await app.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
