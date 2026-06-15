"""
optogrid.py

BLE driver for the OptoGrid device with optional IMU logging, extracted and
cleaned from erlichlab/optogrid-manager's HeadlessOptoGridClient.

Removed from the original: ZMQ, GPIO, rsync. Kept and reworked: the BLE control
API and the IMU acquisition/logging, now fully configurable.

Design notes
------------
* BLE runs on a dedicated background thread with its own asyncio event loop
  (bleak is async and the connection must stay alive between commands). The
  public API is synchronous so it can be called from PyQt slots.
* Each IMU notification carries all 9 sensor values (accel, gyro, mag) in one
  packet, so reading them costs nothing extra. What you configure with the
  on/off flags is which COLUMNS get written to disk, not what is read.
* IMU logging flags (independent, "enfoque C"):
    - save_accel_gyro    : write acc_x/y/z, gyro_x/y/z
    - save_orientation   : write roll/pitch/yaw (requires save_accel_gyro);
                           uses the magnetometer when available, falls back to
                           accel+gyro only when not (yaw will drift)
    - save_magnetometer  : write mag_x/y/z (raw)
  The 'sample' and 'sync' columns are always written.
* Data is written to Parquet; export_csv() converts a Parquet file to CSV.

Requires: bleak, numpy, pyarrow, pandas, ahrs
"""

from __future__ import annotations

import asyncio
import os
import struct
import threading
from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from ahrs.common.orientation import q2euler
from ahrs.filters import EKF
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

# --------------------------------------------------------------------------- #
# UUIDs and byte-encoding map
# --------------------------------------------------------------------------- #

DEVICE_ID_UUID = "56781500-5678-1234-1234-5678abcdeff0"
FIRMWARE_UUID = "56781501-5678-1234-1234-5678abcdeff0"
ULED_CHECK_UUID = "56781504-5678-1234-1234-5678abcdeff0"
BATTERY_UUID = "56781506-5678-1234-1234-5678abcdeff0"
STATUS_LED_UUID = "56781507-5678-1234-1234-5678abcdeff0"
SHAM_LED_UUID = "56781508-5678-1234-1234-5678abcdeff0"
DEVICE_LOG_UUID = "56781509-5678-1234-1234-5678abcdeff0"
LAST_STIM_UUID = "5678150a-5678-1234-1234-5678abcdeff0"
TRIGGER_UUID = "56781609-5678-1234-1234-5678abcdeff0"

# IMU
IMU_ENABLE_UUID = "56781700-5678-1234-1234-5678abcdeff0"
IMU_SAMPLE_RATE_UUID = "56781701-5678-1234-1234-5678abcdeff0"
IMU_DATA_UUID = "56781703-5678-1234-1234-5678abcdeff0"

OPTO_CHAR_MAP = {
    "sequence_length": "56781600-5678-1234-1234-5678abcdeff0",
    "led_selection": "56781601-5678-1234-1234-5678abcdeff0",
    "duration": "56781602-5678-1234-1234-5678abcdeff0",
    "period": "56781603-5678-1234-1234-5678abcdeff0",
    "pulse_width": "56781604-5678-1234-1234-5678abcdeff0",
    "amplitude": "56781605-5678-1234-1234-5678abcdeff0",
    "pwm_frequency": "56781606-5678-1234-1234-5678abcdeff0",
    "ramp_up": "56781607-5678-1234-1234-5678abcdeff0",
    "ramp_down": "56781608-5678-1234-1234-5678abcdeff0",
}

UUID_TO_TYPE = {
    DEVICE_ID_UUID: "string",
    FIRMWARE_UUID: "string",
    ULED_CHECK_UUID: "uint64",
    BATTERY_UUID: "uint16",
    STATUS_LED_UUID: "bool",
    SHAM_LED_UUID: "bool",
    LAST_STIM_UUID: "uint32",
    TRIGGER_UUID: "bool",
    IMU_ENABLE_UUID: "bool",
    IMU_SAMPLE_RATE_UUID: "uint8",
    "56781600-5678-1234-1234-5678abcdeff0": "uint8",
    "56781601-5678-1234-1234-5678abcdeff0": "uint64",
    "56781602-5678-1234-1234-5678abcdeff0": "uint16",
    "56781603-5678-1234-1234-5678abcdeff0": "uint16",
    "56781604-5678-1234-1234-5678abcdeff0": "uint16",
    "56781605-5678-1234-1234-5678abcdeff0": "uint8",
    "56781606-5678-1234-1234-5678abcdeff0": "uint32",
    "56781607-5678-1234-1234-5678abcdeff0": "uint16",
    "56781608-5678-1234-1234-5678abcdeff0": "uint16",
}

# IMU trigger sync marker (same sentinel value as the original)
SYNC_MARKER = 65536


def _encode(uuid: str, value) -> bytes:
    t = UUID_TO_TYPE.get(uuid, "hex")
    s = str(value)
    if t == "string":
        return s.encode("utf-8")
    if t == "uint8":
        return struct.pack("<B", int(s))
    if t == "uint16":
        return struct.pack("<H", int(s))
    if t == "uint32":
        return struct.pack("<I", int(s))
    if t == "uint64":
        return struct.pack("<Q", int(s))
    if t == "bool":
        return struct.pack("<B", 1 if s.lower() in ("true", "1", "yes") else 0)
    return bytes.fromhex(s.replace(" ", ""))


def _decode(uuid: str, data: bytes) -> str:
    t = UUID_TO_TYPE.get(uuid, "hex")
    try:
        if t == "string":
            return data.decode("utf-8").rstrip("\x00")
        if t == "uint8":
            return str(data[0])
        if t == "uint16":
            return str(int.from_bytes(data[:2], "little"))
        if t == "uint32":
            return str(int.from_bytes(data[:4], "little"))
        if t == "bool":
            return "True" if data[0] == 1 else "False"
        return data.hex()
    except Exception:
        return "<decode error>"


def _decode_imu(data: bytes):
    """Decode an IMU data packet: uint32 sample count + 9 int16 sensor values
    (acc x/y/z, gyro x/y/z, mag x/y/z). Returns a list of 10 ints."""
    sample_count = int.from_bytes(data[:4], "little")
    vals = [struct.unpack("<h", data[4 + i : 6 + i])[0] for i in range(0, 18, 2)]
    return [sample_count] + vals


# --------------------------------------------------------------------------- #
# Stimulation parameters
# --------------------------------------------------------------------------- #


@dataclass
class OptoSetting:
    """Optogenetic stimulation parameters. Defaults match the original repo."""

    sequence_length: int = 1
    led_selection: int = 1729382256910270464
    duration: int = 500
    period: int = 2
    pulse_width: int = 1
    amplitude: int = 100
    pwm_frequency: int = 50000
    ramp_up: int = 0
    ramp_down: int = 500


# --------------------------------------------------------------------------- #
# IMU logging configuration
# --------------------------------------------------------------------------- #


@dataclass
class IMUConfig:
    """
    What to WRITE to disk. The three flags are independent, with one
    rule: orientation requires accel+gyro. All-off is valid (logs only sample,
    timestamp, sync). Orientation uses the magnetometer when it is being
    received; otherwise it falls back to accel+gyro (yaw will drift).
    """

    save_accel_gyro: bool = True
    save_orientation: bool = True
    save_magnetometer: bool = False

    def validate(self) -> None:
        if self.save_orientation and not self.save_accel_gyro:
            raise ValueError("save_orientation requires save_accel_gyro to be True")

    def columns(self) -> list[str]:
        """Ordered list of data columns to write, given the flags."""
        cols = ["sample"]
        if self.save_accel_gyro:
            cols += ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]
        if self.save_magnetometer:
            cols += ["mag_x", "mag_y", "mag_z"]
        if self.save_orientation:
            cols += ["roll", "pitch", "yaw"]
        cols += ["sync"]
        return cols


# --------------------------------------------------------------------------- #
# The driver
# --------------------------------------------------------------------------- #


class OptoGrid:
    """Synchronous, thread-safe BLE driver for the OptoGrid, with optional IMU
    logging. BLE work happens on a private background thread; public methods
    block the calling thread for the BLE round-trip but never block the loop."""

    _active: Optional["OptoGrid"] = None

    def __init__(
        self,
        sessions_directory: str,
        filename: str,
        device_name: str = "OptoGrid 1",
        command_timeout: float = 5.0,
        scan_timeout: float = 4.0,
        device_log: bool = False,
        imu_config: Optional[IMUConfig] = None,
    ):
        self.device_name = device_name
        self.command_timeout = command_timeout
        self.scan_timeout = scan_timeout
        self.device_log = device_log
        self.imu_config = imu_config or IMUConfig()
        self.imu_config.validate()
        self.sessions_directory = sessions_directory
        self.filename = filename

        self._client: Optional[BleakClient] = None
        self._selected: Optional[BLEDevice] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

        # IMU runtime state
        self._imu_active = False
        self._imu_sample_rate = 100
        self._imu_buffer: list = []
        self._pending_sync: list = []
        self._parquet_writer = None
        self._parquet_schema = None
        self._parquet_file: Optional[str] = None
        self._imu_columns: list[str] = []

        # orientation / EKF state
        self._ekf = None
        self._q = np.array([1.0, 0.0, 0.0, 0.0])
        self._mag_offset = np.array([0.0, 0.0, 0.0])
        self._mag_scale = np.array([1.0, 1.0, 1.0])
        self._mag_seen = False  # whether we are currently receiving valid mag

    # ---- IMU config can be changed before a logging session -------------- #

    def configure_imu(self, imu_config: IMUConfig) -> None:
        """Replace the IMU logging configuration. Cannot change mid-session."""
        if self._imu_active:
            raise RuntimeError("Cannot reconfigure IMU while logging is active")
        imu_config.validate()
        self.imu_config = imu_config
        print(f"IMU config set: {imu_config}")

    # ---- lifecycle ------------------------------------------------------- #

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if OptoGrid._active is not None and OptoGrid._active is not self:
            print("Warning: Stopping previous OptoGrid instance left open")
            OptoGrid._active.stop()
        OptoGrid._active = self
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, name="optogrid-ble", daemon=True
        )
        self._thread.start()
        print("OptoGrid BLE thread started")

    def _run_loop(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self) -> None:
        if self._loop is None:
            return
        try:
            if self._imu_active:
                self.stop_imu_logging()
            if self.is_connected:
                self.disconnect()
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread:
                self._thread.join(timeout=5)
            if OptoGrid._active is self:
                OptoGrid._active = None
            self._loop.close()
            self._loop = None
            self._thread = None
            print("OptoGrid BLE thread stopped")

    def _submit(self, coro, timeout: Optional[float] = None):
        if self._loop is None:
            raise RuntimeError("OptoGrid not started. Call start() first.")
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout if timeout is not None else self.command_timeout)

    # ---- connection ------------------------------------------------------ #

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    def status(self) -> str:
        """Human-readable connection status, e.g. for a GUI label."""
        if not self.is_connected:
            return "Disconnected"
        name = getattr(self._selected, "name", "Unknown Device")
        address = getattr(self._selected, "address", "Unknown Address")
        return f"Connected to {name} ({address})"

    def connect(self, identifier: Optional[str] = None, timeout: float = 5.0) -> bool:
        target = identifier or self.device_name
        try:
            if self._submit(self._connect(target), timeout=timeout):
                return True
            print("Warning: Connect failed")
        except Exception as e:
            print(f"Error: Connect error: {e}")
        return False

    async def _connect(self, identifier: str) -> bool:
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            self._client = None

        is_addr = (
            (len(identifier) == 36 and identifier.count("-") == 4)
            or (len(identifier) == 17 and ":" in identifier)
            or (
                len(identifier) > 10
                and all(c in "0123456789ABCDEFabcdef:-" for c in identifier)
            )
        )

        if is_addr:
            print(f"Connecting directly to {identifier}")
            self._client = BleakClient(
                identifier, disconnected_callback=self._on_disconnect
            )
            await self._client.connect()
            try:
                name = await self._read(DEVICE_ID_UUID)
            except Exception:
                name = f"OptoGrid-{identifier[-4:]}"
            self._selected = type("Device", (), {"name": name, "address": identifier})()
        else:
            print(f"Scanning for device: {identifier}")
            devices = await BleakScanner.discover(timeout=self.scan_timeout)
            match = next((d for d in devices if d.name and identifier in d.name), None)
            if not match:
                print(f"Warning: Device {identifier} not found")
                return False
            self._client = BleakClient(
                match.address, disconnected_callback=self._on_disconnect
            )
            await self._client.connect()
            self._selected = match
            name = match.name

        await self._enable_device_log()
        self._load_mag_calibration(name)
        await self._update_ekf_frequency()
        print(f"Connected to {name}")
        return True

    def _on_disconnect(self, client) -> None:
        print("Warning: OptoGrid disconnected unexpectedly")
        if self._imu_active:
            # flush whatever we have; can't await here, do it directly
            try:
                self._flush_imu()
                self._close_parquet()
            except Exception as e:
                print(f"Error flushing IMU on disconnect: {e}")
            self._imu_active = False

    async def _enable_device_log(self) -> None:
        if not self.device_log:
            return
        assert self._client is not None
        try:
            await self._client.start_notify(DEVICE_LOG_UUID, self._on_device_log)
            print("Device log notifications enabled")
        except Exception as e:
            print(f"Warning: Could not enable device log notifications: {e}")

    async def _on_device_log(self, sender, data: bytearray) -> None:
        try:
            null = data.find(0)
            msg = (data[:null] if null != -1 else data).decode(
                "utf-8", errors="replace"
            )
            print(f"ble_log: {msg}")
        except Exception as e:
            print(f"Error in device log handler: {e}")

    def disconnect(self) -> bool:
        try:
            return self._submit(self._disconnect())
        except Exception as e:
            print(f"Error: Disconnect error: {e}")
            return False

    async def _disconnect(self) -> bool:
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            print("Disconnected")
        self._client = None
        self._selected = None
        return True

    def scan(self) -> list[str]:
        return self._submit(self._scan(), timeout=self.scan_timeout + 1)

    async def _scan(self) -> list[str]:
        devices = await BleakScanner.discover(timeout=self.scan_timeout)
        return [f"{d.name} ({d.address})" for d in devices if d.name and "O" in d.name]

    # ---- stimulation core ------------------------------------------------ #

    def trigger(self) -> bool:
        if not self.is_connected:
            print("Warning: trigger ignored — not connected")
            return False
        try:
            self._submit(self._trigger())
            return True
        except Exception as e:
            print(f"Error: Trigger failed: {e}")
            return False

    async def _trigger(self) -> None:
        assert self._client is not None
        await self._client.write_gatt_char(TRIGGER_UUID, _encode(TRIGGER_UUID, "True"))
        print("Sent opto trigger")
        # Mark a sync event in the IMU stream, exactly like the original
        if self._imu_active:
            self._handle_sync(SYNC_MARKER)

    def program(self, settings: OptoSetting) -> bool:
        if not self.is_connected:
            print("Warning: program ignored — not connected")
            return False
        try:
            self._submit(self._program(settings))
            return True
        except Exception as e:
            print(f"Error: Programming failed: {e}")
            return False

    async def _program(self, settings: OptoSetting) -> None:
        assert self._client is not None
        data = asdict(settings)
        seq_uuid = OPTO_CHAR_MAP["sequence_length"]
        await self._client.write_gatt_char(
            seq_uuid, _encode(seq_uuid, data["sequence_length"])
        )
        for name, value in data.items():
            if name == "sequence_length":
                continue
            uuid = OPTO_CHAR_MAP[name]
            if isinstance(value, (list, tuple)):
                buf = bytearray()
                for v in value:
                    buf.extend(_encode(uuid, v))
                await self._client.write_gatt_char(uuid, bytes(buf))
            else:
                await self._client.write_gatt_char(uuid, _encode(uuid, value))
        print("Opto programmed")

    # ---- IMU: calibration & EKF ------------------------------------------ #

    def _load_mag_calibration(self, device_name: str) -> bool:
        """Load hard/soft-iron magnetometer calibration if the file exists."""
        try:
            path = os.path.join(
                self.sessions_directory, f"{device_name} Calibration.csv"
            )
            if not os.path.exists(path):
                print(f"No magnetometer calibration file ({path}); using raw mag")
                return False
            cal = pd.read_csv(path)
            if not all(c in cal.columns for c in ("mag_x", "mag_y", "mag_z")):
                print("Error: Calibration file missing mag_x/mag_y/mag_z columns")
                return False
            mx, my, mz = cal["mag_x"].values, cal["mag_y"].values, cal["mag_z"].values
            self._mag_offset = np.array(
                [
                    (mx.max() + mx.min()) / 2,
                    (my.max() + my.min()) / 2,
                    (mz.max() + mz.min()) / 2,
                ]
            )
            rx, ry, rz = mx.ptp(), my.ptp(), mz.ptp()
            avg = (rx + ry + rz) / 3
            self._mag_scale = np.array(
                [
                    avg / rx if rx > 0 else 1.0,
                    avg / ry if ry > 0 else 1.0,
                    avg / rz if rz > 0 else 1.0,
                ]
            )
            print(f"Magnetometer calibration loaded from {path}")
            return True
        except Exception as e:
            print(f"Error loading magnetometer calibration: {e}")
            return False

    async def _update_ekf_frequency(self) -> None:
        """Read the device IMU sample rate and (re)create the EKF filter."""
        try:
            assert self._client is not None
            val = await self._client.read_gatt_char(IMU_SAMPLE_RATE_UUID)
            rate = int.from_bytes(val[:2], "little")
            if rate > 0:
                self._imu_sample_rate = rate
        except Exception as e:
            print(
                f"Warning: Could not read IMU sample rate, "
                f"using {self._imu_sample_rate} Hz: {e}"
            )
        self._init_ekf()

    def _init_ekf(self) -> None:
        """Create the EKF only if orientation is requested (avoids the import
        and the CPU cost when not needed)."""
        if not self.imu_config.save_orientation:
            self._ekf = None
            return
        self._ekf = EKF(
            frequency=self._imu_sample_rate,
            var_acc=0.0001,
            var_gyro=10,
            var_mag=0.1,
            declination=0.0,
        )
        self._q = np.array([1.0, 0.0, 0.0, 0.0])
        print(f"EKF initialised at {self._imu_sample_rate} Hz")

    def _compute_orientation(self, imu_vals):
        """Compute roll/pitch/yaw from one IMU sample. Uses the magnetometer
        when its reading looks valid; otherwise runs accel+gyro only."""
        acc = np.array(imu_vals[1:4]) * (32.0 / 65536.0)
        gyr = np.array(imu_vals[4:7]) * (4000.0 / 65536.0)
        mag_raw = np.array(imu_vals[7:10])
        mag_cal = (mag_raw - self._mag_offset) * self._mag_scale
        mag = mag_cal * (100.0 / 65536.0)

        acc_w = np.array([acc[0], -acc[1], -acc[2]])
        gyr_w = np.array([gyr[0], -gyr[1], -gyr[2]])
        mag_w = np.array([mag[1], -mag[0], -mag[2]])

        gyr_w = np.where(np.abs(gyr_w) < 5, 0, gyr_w)

        mag_valid = np.linalg.norm(mag) > 0.01
        if mag_valid:
            self._q = self._ekf.update(
                q=self._q, gyr=np.radians(gyr_w), acc=acc_w * 9.80665, mag=mag_w * 100.0
            )
        else:
            self._q = self._ekf.update(
                q=self._q, gyr=np.radians(gyr_w), acc=acc_w * 9.80665
            )
        roll, pitch, yaw = np.degrees(q2euler(self._q))
        return float(roll), float(pitch), (float(yaw) + 360) % 360

    # ---- IMU: enable / logging ------------------------------------------- #

    def start_imu_logging(self) -> Optional[str]:
        """Enable the IMU on the device and start logging to a Parquet file.
        Returns the file path, or None on failure."""
        if not self.is_connected:
            print("Warning: start_imu_logging ignored — not connected")
            return None
        if self._imu_active:
            print("Warning: IMU logging already active")
            return self._parquet_file
        try:
            return self._submit(self._start_imu())
        except Exception as e:
            print(f"Error: Failed to start IMU logging: {e}")
            return None

    async def _start_imu(self) -> Optional[str]:
        assert self._client is not None

        # (re)build EKF in case orientation flag changed since connect
        self._init_ekf()

        # enable IMU on the device
        await self._client.write_gatt_char(
            IMU_ENABLE_UUID, _encode(IMU_ENABLE_UUID, "True")
        )
        # subscribe to IMU notifications
        await self._client.start_notify(IMU_DATA_UUID, self._on_imu_data)

        fname = os.path.join(self.sessions_directory, f"{self.filename}_IMU.parquet")

        # build schema from the configured columns
        self._imu_columns = self.imu_config.columns()
        type_map = {
            "sample": pa.int64(),
            "sync": pa.int64(),
            "acc_x": pa.int64(),
            "acc_y": pa.int64(),
            "acc_z": pa.int64(),
            "gyro_x": pa.int64(),
            "gyro_y": pa.int64(),
            "gyro_z": pa.int64(),
            "mag_x": pa.int64(),
            "mag_y": pa.int64(),
            "mag_z": pa.int64(),
            "roll": pa.float64(),
            "pitch": pa.float64(),
            "yaw": pa.float64(),
        }
        self._parquet_schema = pa.schema([(c, type_map[c]) for c in self._imu_columns])
        self._parquet_writer = pq.ParquetWriter(
            fname, self._parquet_schema, compression="snappy"
        )
        self._parquet_file = fname
        self._imu_buffer = []
        self._pending_sync = []
        self._imu_active = True
        print(f"IMU logging started: {fname} | columns: {self._imu_columns}")
        return fname

    async def _on_imu_data(self, sender, data: bytearray) -> None:
        try:
            imu_vals = _decode_imu(data)  # [sample, acc xyz, gyro xyz, mag xyz]

            # take a queued sync if present, else 0
            sync_value = self._pending_sync.pop(0) if self._pending_sync else 0

            row = {
                "sample": imu_vals[0],
                "sync": sync_value,
            }
            if self.imu_config.save_accel_gyro:
                row.update(
                    {
                        "acc_x": imu_vals[1],
                        "acc_y": imu_vals[2],
                        "acc_z": imu_vals[3],
                        "gyro_x": imu_vals[4],
                        "gyro_y": imu_vals[5],
                        "gyro_z": imu_vals[6],
                    }
                )
            if self.imu_config.save_magnetometer:
                row.update(
                    {"mag_x": imu_vals[7], "mag_y": imu_vals[8], "mag_z": imu_vals[9]}
                )
            if self.imu_config.save_orientation:
                roll, pitch, yaw = self._compute_orientation(imu_vals)
                row.update({"roll": roll, "pitch": pitch, "yaw": yaw})

            # store as a tuple in column order
            self._imu_buffer.append([row[c] for c in self._imu_columns])
            if len(self._imu_buffer) >= 100:
                self._flush_imu()
        except Exception as e:
            print(f"Error in IMU data handler: {e}")

    def sync(self, value: int = 1) -> bool:
        """Manually mark a sync value in the IMU stream, independent of trigger().

        Useful to mark task events (e.g. trial onset) in the IMU log. If IMU
        logging is not active, returns False without doing anything."""
        if not self._imu_active:
            print("Warning: sync ignored — IMU logging not active")
            return False
        self._handle_sync(value)
        return True

    def _handle_sync(self, value: int) -> None:
        """Mark a sync value on the most recent buffered sample, or queue it for
        the next incoming sample (exactly the original's logic)."""
        if self._imu_buffer:
            sync_idx = self._imu_columns.index("sync")
            self._imu_buffer[-1][sync_idx] = value
            print(f"Sync {value} written to current IMU sample")
        else:
            self._pending_sync.append(value)
            print(f"Sync {value} queued for next IMU sample")

    def _flush_imu(self) -> None:
        if not self._imu_buffer or not self._parquet_writer:
            return
        try:
            df = pd.DataFrame(self._imu_buffer, columns=self._imu_columns)
            table = pa.Table.from_pandas(
                df, schema=self._parquet_schema, preserve_index=False
            )
            self._parquet_writer.write_table(table)
            self._imu_buffer = []
        except Exception as e:
            print(f"Error flushing IMU buffer: {e}")

    def _close_parquet(self) -> None:
        if self._parquet_writer:
            try:
                self._parquet_writer.close()
            except Exception as e:
                print(f"Error closing parquet writer: {e}")
            self._parquet_writer = None

    def stop_imu_logging(self) -> Optional[str]:
        """Disable the IMU on the device and close the Parquet file. Returns the
        file path that was written."""
        if not self._imu_active:
            print("Warning: No active IMU logging to stop")
            return None
        path = self._parquet_file
        try:
            self._submit(self._stop_imu())
        except Exception as e:
            print(f"Error stopping IMU logging: {e}")
        return path

    async def _stop_imu(self) -> None:
        assert self._client is not None
        try:
            await self._client.stop_notify(IMU_DATA_UUID)
        except Exception:
            pass
        try:
            await self._client.write_gatt_char(
                IMU_ENABLE_UUID, _encode(IMU_ENABLE_UUID, "False")
            )
        except Exception:
            pass
        self._flush_imu()
        self._close_parquet()
        self._imu_active = False
        print(f"IMU logging stopped: {self._parquet_file}")

    @property
    def imu_logging(self) -> bool:
        return self._imu_active

    # ---- small reads ----------------------------------------------------- #

    def toggle_status_led(self, on: bool) -> bool:
        return self._write_bool(STATUS_LED_UUID, on, "status LED")

    def toggle_sham_led(self, on: bool) -> bool:
        return self._write_bool(SHAM_LED_UUID, on, "sham LED")

    def _write_bool(self, uuid: str, on: bool, label: str) -> bool:
        if not self.is_connected:
            return False
        assert self._client is not None
        try:
            self._submit(
                self._client.write_gatt_char(
                    uuid, _encode(uuid, "True" if on else "False")
                )
            )
            print(f"{label} {'on' if on else 'off'}")
            return True
        except Exception as e:
            print(f"Error: Failed to set {label}: {e}")
            return False

    def read_battery_mv(self) -> Optional[int]:
        if not self.is_connected:
            return None
        try:
            return int(self._submit(self._read(BATTERY_UUID)))
        except Exception as e:
            print(f"Error: Battery read failed: {e}")
            return None

    def read_last_stim_ms(self) -> Optional[int]:
        if not self.is_connected:
            return None
        try:
            return int(self._submit(self._read(LAST_STIM_UUID)))
        except Exception as e:
            print(f"Error: Last-stim read failed: {e}")
            return None

    def read_uled_check(self) -> Optional[int]:
        if not self.is_connected:
            return None
        try:
            return int(self._submit(self._read(ULED_CHECK_UUID)))
        except Exception as e:
            print(f"Error: uLED check read failed: {e}")
            return None

    def read_device_id(self) -> Optional[str]:
        if not self.is_connected:
            return None
        try:
            return self._submit(self._read(DEVICE_ID_UUID))
        except Exception as e:
            print(f"Error: Device-id read failed: {e}")
            return None

    async def _read(self, uuid: str) -> str:
        assert self._client is not None
        val = await self._client.read_gatt_char(uuid)
        return _decode(uuid, val)

    # ---- context manager ------------------------------------------------- #

    def __enter__(self) -> "OptoGrid":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


# --------------------------------------------------------------------------- #
# Parquet -> CSV export
# --------------------------------------------------------------------------- #


def export_csv(parquet_path: str, csv_path: Optional[str] = None) -> str:
    """Convert a Parquet IMU log to CSV. If csv_path is omitted, uses the same
    name with a .csv extension. Returns the CSV path."""
    if csv_path is None:
        csv_path = os.path.splitext(parquet_path)[0] + ".csv"
    df = pd.read_parquet(parquet_path)
    df.to_csv(csv_path, index=False)
    return csv_path
