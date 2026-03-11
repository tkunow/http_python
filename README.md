# Rest Api

## Example
```python
import json
async def main():
    app = HttpRequestHandler(["127.0.0.1", 80], DebugLevel.DEBUG)
    @app.get("/test")
    def hello_world_get():
        return json.dumps({"data": "Hello World! from outer class"})

    @app.get("/inlinehtml")
    def inline_html_get():
        return "<p>Hello World!</p>"
    @app.post("/test")
    def hello_wold_post():
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
```
