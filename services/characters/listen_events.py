import asyncio
import redis.asyncio as redis
from characters_app.settings import settings
import json

async def main():
    r = redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password if hasattr(settings.redis, 'password') else None,
        decode_responses=True
    )
    
    pubsub = r.pubsub()
    await pubsub.subscribe('character_events')
    print('Listening on character_events channel... Press Ctrl+C to stop')
    
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                print(f'\n=== EVENT RECEIVED ===')
                print(message['data'])
                print('=' * 50)
    except KeyboardInterrupt:
        pass
    finally:
        await pubsub.unsubscribe('character_events')
        await r.aclose()

asyncio.run(main())
