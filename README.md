# someip

Small Python example project that publishes and consumes a SOME/IP temperature event using the [`someipy`](https://github.com/chrizog/someipy) library.

The repository contains:

- `server.py`: offers a SOME/IP service and sends a temperature event once per second
- `client.py`: discovers the service, subscribes to the event group, and prints received measurements
- `temperature_msg.py`: defines the serialized SOME/IP payload layout
- `someipy/`: local Python virtual environment used by the project on this machine

## What This Project Does

The server exposes one SOME/IP service with one event group and one event:

- Service ID: `0x1234`
- Instance ID: `0x5678`
- Event Group ID: `0x0321`
- Event ID: `0x0123`

Every second, the server sends a payload containing:

- a payload version (`major`, `minor`)
- a timestamp counter
- 4 float temperature values

The client subscribes to that event and deserializes the payload into a `TemparatureMsg` object, then prints the measurements.

## Repository Layout

```text
.
|-- client.py
|-- server.py
|-- temperature_msg.py
|-- server.log
`-- someipy/        # local virtual environment (ignored by git)
```

## Requirements

- Python 3.8+ supported by `someipy`
- This workspace currently uses Python `3.13.1` in the checked-in local virtual environment
- Network access between the client and server machine
- Multicast support for SOME/IP service discovery

## Setup

This repository currently relies on a local virtual environment stored at `someipy/`.

PowerShell:

```powershell
.\someipy\Scripts\Activate.ps1
```

If you want to recreate the environment instead of using the existing one:

```powershell
python -m venv someipy
.\someipy\Scripts\Activate.ps1
pip install someipy psutil
```

## Configuration

The example uses hard-coded network settings, so you will usually need to adjust them before running on another machine.

### Server settings

Defined in `server.py`:

- `SERVER_IP = "100.83.23.218"`
- `SERVER_PORT = 3000`
- `SD_MULTICAST_GROUP = "224.224.224.245"`
- `SD_PORT = 30490`

The server offers the service over `TCP`.

### Client settings

Defined in `client.py`:

- `DEFAULT_INTERFACE_IP = "192.168.0.253"`
- `SD_MULTICAST_GROUP = "224.224.224.245"`
- `SD_PORT = 30490`
- client endpoint port: `3003`

The client service instance is created with `UDP`.

You can override the client interface IP at runtime:

```powershell
python .\client.py --interface_ip 192.168.0.10
```

## How To Run

Open two terminals.

### 1. Start the server

```powershell
.\someipy\Scripts\Activate.ps1
python .\server.py
```

Expected behavior:

- the server starts service discovery
- it begins offering the temperature service
- it sends one event per second
- logs are written to `server.log`

### 2. Start the client

```powershell
.\someipy\Scripts\Activate.ps1
python .\client.py --interface_ip 192.168.0.253
```

Expected behavior:

- the client subscribes to the event group
- it waits for service offers
- once events arrive, it prints the 4 deserialized temperature values

## Payload Format

`temperature_msg.py` defines the SOME/IP payload structure:

```text
TemparatureMsg
|-- version.major : Uint8
|-- version.minor : Uint8
|-- timestamp     : Uint64
`-- measurements  : Float32[4]
```

The class is spelled `TemparatureMsg` in the source code and README intentionally keeps that name to match the implementation.

## Notes And Caveats

- `someipy/` is a virtual environment, not application source code.
- `server.py` and `client.py` currently use different default local IP addresses. Update them to match your actual interfaces.
- The server offers the service using `TCP`, while the client instance is created with `UDP`. If communication does not behave as expected in your environment, align the transport settings first.
- `server.log` can grow large over time because the server writes one log entry per second.
- There are no automated tests in the repository at the moment.

## Quick Sanity Check

To validate payload serialization separately:

```powershell
.\someipy\Scripts\Activate.ps1
python .\temperature_msg.py
```

That script creates a sample message, serializes it, deserializes it again, and asserts equality.
