import asyncio
import logging
import sched
import time

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys

    sys.exit(1)

from ocpp.v16 import call
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import RegistrationStatus
from ocpp.exceptions import OCPPError, NotImplementedError
from ocpp.routing import create_route_map
from ocpp.messages import Call, validate_payload, MessageType
from ocpp.messages import unpack
from base64 import b64encode

logging.basicConfig(filename='/var/www/html/openWB/ramdisk/ocpp.log', level=logging.INFO)


def basic_auth_header(username, password):
    assert ':' not in username
    user_pass = f'{username}:{password}'
    basic_credentials = b64encode(user_pass.encode()).decode()
    return 'Authorization', f'Basic {basic_credentials}'


class ChargePoint(cp):
    async def send_heartbeat(self, interval):
        request = call.HeartbeatPayload()
        while True:
            await self.call(request)
            await asyncio.sleep(interval)

    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charge_point_model="openWB",
            charge_point_vendor="snaptec"
        )

        response = await self.call(request)
        if response.status == RegistrationStatus.accepted:
            logging.info('OCPP Connected to central system')
            await self.send_heartbeat(response.interval)


async def main():
    async with websockets.connect(
            # 'ws://localhost:9000/CP_1',
            # 'ws://ocpp.evnex.io/4687-111111111',
            'wss://gk-software.public.ocpp-broker.com/ocpp/cp/socket/16/openWB0111',
            extra_headers=[basic_auth_header('gk-software', 'vpfHGbtafgmcIbzWAIDG')],
            subprotocols=['ocpp1.6']
    ) as ws:
        cp = ChargePoint('CP_1', ws)

        await asyncio.gather(cp.start(), cp.send_boot_notification())


if __name__ == '__main__':
    try:
        # asyncio.run() is used when running this example with Python 3.7 and
        # higher.
        asyncio.run(main())
    except AttributeError:
        # For Python 3.6 a bit more code is required to run the main() task on
        # an event loop.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
