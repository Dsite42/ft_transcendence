#!/usr/bin/env python3
from aiorpc import AioRPC
from tinyrpc.dispatch import public
from asyncio import Future, sleep, run

class ExampleService:
    @public
    def ping(self) -> str:
        return 'Pong!'

    @public
    async def ping_with_delay(self) -> str:
        await sleep(5.0)
        return 'Pong! (with delay :D)'

async def main() -> None:
    async with AioRPC('localhost', 'example_service', ExampleService()):
        # Do anything else here
        await Future()

if __name__ == '__main__':
    try:
        run(main())
    except KeyboardInterrupt:
        pass
