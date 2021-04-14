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
from datetime import datetime

logging.basicConfig(filename='/var/www/html/openWB/ramdisk/ocpp.log', level=logging.INFO)

# get Version ID for firmwareVersion
fd = open('/var/www/html/openWB/web/version', 'r')
version = fd.readline()
fd.close()

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


# https://python-forum.io/Thread-Websocket-conection-closes-abnormally

class ChargePoint(cp):
    async def send_heartbeat(self, interval):
        request = call.HeartbeatPayload()
        while True:
            await self.call(request)
            await asyncio.sleep(interval)

    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charge_point_model="openWB",
            charge_point_vendor="snaptec",
            firmware_version=version
        )

        response = await self.call(request)
        if response.status == RegistrationStatus.accepted:
            logging.info('OCPP Connected to central system')
            await self.send_heartbeat(response.interval)

    async def running_state(self):
        keep_running = True
        while keep_running:
            fd = open('/var/www/html/openWB/ramdisk/lp1enabled', 'r')
            state = fd.readline()
            fd.close()
            if state == '1':
                # print("Push Button released")
                # await self.Send_StatusNotification_available()
                await self.Start_Transaction()
                break
                # time.sleep(10)
                # continue
            else:
                # print("Push Button pressed")
                # await self.Send_StatusNotification_unavailable()
                break
                # time.sleep(10)
                # continue

    async def Start_Transaction(self):
        request = call.StartTransactionPayload(
            connector_id=1,
            id_tag='11111',
            meter_start=0,
            timestamp=datetime.utcnow().isoformat()
        )
        response = await self.call(request)
        logging.info(response)

    async def Send_StatusNotification_available(self):
        request = call.StatusNotificationPayload(
            connector_id=0,
            error_code="NoError",
            status="Available"
        )
        response = await self.call(request)
        print("Charge Point Available")

    # charge cable connected - status change to unavailable
    async def Send_StatusNotification_unavailable(self):
        request = call.StatusNotificationPayload(
            connector_id=0,
            error_code="NoError",
            status="Unavailable"
        )
        response = await self.call(request)
        print("Charge Point Occupied")

    # charge cable connected, fault - status change to fault
    async def Send_StatusNotification_fault(self):
        request = call.StatusNotificationPayload(
            connector_id=0,
            error_code="InternalError",
            status="Faulted"
        )
        response = await self.call(request)
        print("Charger Internal Error")

    # --------------------------------------------

    @on(Action.Reset)
    async def on_station_reset(self, type):
        print(type)

    @on(Action.TriggerMessage)
    async def on_TriggerMessage(self, requested_message, connector_id):
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

    @on(Action.UnlockConnector)
    async def on_UnlockConnector(self):
        print(a)

    @on(Action.RemoteStartTransaction)
    async def on_RemoteStartTransaction(self):
        print(a)

    @on(Action.ReserveNow)
    async def on_ReserveNow(self):
        print(a)

    @on(Action.RemoteStopTransaction)
    async def on_RemoteStopTransaction(self):
        print(a)

async def main():
    async with websockets.connect(
            ocpp_endpoint_url,
            extra_headers=[headers],
            # extra_headers=[basic_auth_header(ocpp_bAuth_User, ocpp_bAuth_Password)],
            subprotocols=['ocpp1.6']
    ) as ws:
        cp = ChargePoint('CP_1', ws)

        await asyncio.gather(cp.start(), cp.send_boot_notification(), cp.running_state())


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
