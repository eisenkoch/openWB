import asyncio
import json
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
from ocpp.v16.enums import Action
from ocpp.routing import on
from base64 import b64encode

logging.basicConfig(filename='/var/www/html/openWB/ramdisk/ocpp.log', level=logging.INFO)

# get OCPP module config from openWB config
fd = open('/var/www/html/openWB/openwb.conf', 'r')
for line in fd:
    try:
        (key, val) = line.rstrip().split("=")
        if key == "ocpp_enable_bAuth":
            logging.debug("ocpp_enable_bAuth: " + val)
            ocpp_enable_bAuth = val
        if key == "ocpp_bAuth_User":
            logging.debug("ocpp_bAuth_User: " + val)
            ocpp_bAuth_User = val
        if key == "ocpp_bAuth_Password":
            logging.debug("ocpp_bAuth_Password: " + val)
            ocpp_bAuth_Password = val
        if key == "ocpp_endpoint":
            logging.debug("ocpp_endpoint: " + val)
            ocpp_endpoint = val
        if key == "ocpp_CPID":
            logging.debug("ocpp_CPID: " + val)
            ocpp_CPID = val
    except:
        val = ""
fd.close()

ocpp_endpoint_url = str(ocpp_endpoint) + str(ocpp_CPID)
logging.debug(ocpp_endpoint_url)


def basic_auth_header(username, password):
    assert ':' not in username
    user_pass = f'{username}:{password}'
    basic_credentials = b64encode(user_pass.encode()).decode()
    return 'Authorization', f'Basic {basic_credentials}'


if ocpp_enable_bAuth == '1':
    headers = basic_auth_header(ocpp_bAuth_User, ocpp_bAuth_Password)
else:
    headers = ''


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

    @on(Action.Reset)
    async def on_station_reset(self, type):
        print(type)

    @on(Action.TriggerMessage)
    async def on_TriggerMessage(self, requested_message, connector_id):
        # print (requested_message)
        request = call.TriggerMessage()
        await self.call(request)

    @on(Action.DataTransfer)
    async def on_DataTransfer(self):
        print(a)

    @on(Action.ChangeAvailability)
    async def on_ChangeAvailability(self):
        print(a)

    @on(Action.SendLocalList)
    async def on_SendLocalList(self):
        print(a)

    @on(Action.GetConfiguration)
    async def on_GetConfiguration(self):
        print(a)


async def main():
    async with websockets.connect(
            ocpp_endpoint_url,
            extra_headers=[headers],
            # extra_headers=[basic_auth_header(ocpp_bAuth_User, ocpp_bAuth_Password)],
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
