
import asyncio
from bleak import BleakScanner


async def run():
    devices = await BleakScanner.discover()
    for d in devices:
        # print(d)
        address = str(d).split(' ')[0][:-1]
        name = str(d).replace(address, '')
        #print(address)

        if address == 'E0:95:FD:FF:06:6C':
            print('Found:', name)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
