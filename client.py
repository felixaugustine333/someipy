import asyncio
import ipaddress
import logging
import sys


from someipy import ServiceBuilder, EventGroup, TransportLayerProtocol, SomeIpMessage
from someipy.service_discovery import construct_service_discovery
from someipy.client_service_instance import construct_client_service_instance
from someipy.logging import set_someipy_log_level
from temperature_msg import TemparatureMsg

SD_MULTICAST_GROUP = "224.224.224.245"
SD_PORT = 30490
DEFAULT_INTERFACE_IP = "192.168.0.253"

SAMPLE_SERVICE_ID = 0x1234
SAMPLE_INSTANCE_ID = 0x5678
SAMPLE_EVENTGROUP_ID = 0x0321
SAMPLE_EVENT_ID = 0x0123

def temperature_callback(someip_message: SomeIpMessage) -> None:
    try:
        print(
            f"Received {len(someip_message.payload)} bytes for event {someip_message.header.method_id}. Deserializing..."
        )
        temperature_msg = TemparatureMsg().deserialize(someip_message.payload)
        print(f"[CLIENT] Measurements: {[x.value for x in temperature_msg.measurements.data]}")
    except Exception as e:
        print(f"Error in deserialization: {e}")

async def main():
    set_someipy_log_level(logging.DEBUG)

    # Allow override via --interface_ip if passed as argument
    interface_ip = DEFAULT_INTERFACE_IP
    for i, arg in enumerate(sys.argv):
        if arg == "--interface_ip" and i + 1 < len(sys.argv):
            interface_ip = sys.argv[i + 1]

    service_discovery = await construct_service_discovery(
        SD_MULTICAST_GROUP, SD_PORT, interface_ip
    )

    temperature_eventgroup = EventGroup(
        id=SAMPLE_EVENTGROUP_ID,
        event_ids=[SAMPLE_EVENT_ID]
    )

    temperature_service = (
        ServiceBuilder()
        .with_service_id(SAMPLE_SERVICE_ID)
        .with_major_version(1)
        .build()
    )

    client_instance = await construct_client_service_instance(
        service=temperature_service,
        instance_id=SAMPLE_INSTANCE_ID,
        endpoint=(ipaddress.IPv4Address(interface_ip), 3003),
        ttl=5,
        sd_sender=service_discovery,
        protocol=TransportLayerProtocol.UDP,
    )

    # Register event callback
    client_instance.register_callback(temperature_callback)

    # Subscribe to event group
    client_instance.subscribe_eventgroup(SAMPLE_EVENTGROUP_ID)

    # Attach to service discovery to receive offers
    service_discovery.attach(client_instance)

    print("[CLIENT] Subscribed. Listening for events...")

    try:
        await asyncio.Future()  # Keeps the loop running forever
    except asyncio.CancelledError:
        print("Client shutting down...")
    finally:
        service_discovery.close()
        await client_instance.close()

if __name__ == "__main__":
    asyncio.run(main())