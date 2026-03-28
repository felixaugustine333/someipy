import asyncio
import ipaddress
import logging

from someipy import (
    TransportLayerProtocol,
    ServiceBuilder,
    EventGroup,
    construct_server_service_instance,
)
from someipy.service_discovery import construct_service_discovery
from someipy.logging import set_someipy_log_level
from someipy.serialization import Uint8, Uint64, Float32
from temperature_msg import TemparatureMsg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

# === Configuration ===
SERVER_IP = "100.83.23.218"
SERVER_PORT = 3000
SD_MULTICAST_GROUP = "224.224.224.245"
SD_PORT = 30490

SAMPLE_SERVICE_ID = 0x1234
SAMPLE_INSTANCE_ID = 0x5678
SAMPLE_EVENTGROUP_ID = 0x0321
SAMPLE_EVENT_ID = 0x0123

async def main():
    # Enable logging for SOME/IP stack
    set_someipy_log_level(logging.INFO)

    # Setup service discovery
    service_discovery = await construct_service_discovery(
        SD_MULTICAST_GROUP, SD_PORT, SERVER_IP
    )

    # Define temperature event group and service
    temperature_eventgroup = EventGroup(
        id=SAMPLE_EVENTGROUP_ID, event_ids=[SAMPLE_EVENT_ID]
    )

    temperature_service = (
        ServiceBuilder()
        .with_service_id(SAMPLE_SERVICE_ID)
        .with_major_version(1)
        .with_eventgroup(temperature_eventgroup)
        .build()
    )

    # Setup the server service instance (TCP)
    service_instance_temperature = await construct_server_service_instance(
        service=temperature_service,
        instance_id=SAMPLE_INSTANCE_ID,
        endpoint=(ipaddress.IPv4Address(SERVER_IP), SERVER_PORT),
        ttl=5,
        sd_sender=service_discovery,
        cyclic_offer_delay_ms=2000,
        protocol=TransportLayerProtocol.TCP,
    )

    # Attach and start offering the service
    service_discovery.attach(service_instance_temperature)
    service_instance_temperature.start_offer()

    logging.info("[SERVER] Offering temperature service...")

    # Create the temperature message object
    msg = TemparatureMsg()
    msg.version.major = Uint8(1)
    msg.version.minor = Uint8(0)
    msg.timestamp = Uint64(0)

    try:
        while True:
            await asyncio.sleep(1)
            msg.timestamp = Uint64(msg.timestamp.value + 1)

            # Simulate 4 temperature values
            for i in range(4):
                msg.measurements.data[i] = Float32(20.0 + i)

            payload = msg.serialize()
            service_instance_temperature.send_event(
                SAMPLE_EVENTGROUP_ID, SAMPLE_EVENT_ID, payload
            )

            logging.info(f"[SERVER] Sent: Timestamp={msg.timestamp.value}, Measurements={[m.value for m in msg.measurements.data]}")

    except asyncio.CancelledError:
        await service_instance_temperature.stop_offer()
    finally:
        service_discovery.close()

if __name__ == "__main__":
    asyncio.run(main())