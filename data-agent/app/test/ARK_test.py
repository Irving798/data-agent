
import asyncio
from app.clients.embedding_client_manager import embedding_client_manager

async def main():
    embedding_client_manager.init()
    v = await embedding_client_manager.client.aembed_query("华北地区")
    print("dim:", len(v))
    print("first5:", v[:5])

asyncio.run(main())

