from village.devices.camera import get_camera
from village.devices.motor import motor1, motor2
from village.devices.rfid import rfid
from village.devices.scale import scale
from village.devices.temp_sensor import temp_sensor


class Dev:
    def __init__(self) -> None:
        self.cam_corridor = get_camera(0, "CORRIDOR")
        self.cam_box = get_camera(1, "BOX")
        self.cam_corridor.start_record()
        self.cam_box.start_record()
        self.motor1 = motor1
        self.motor2 = motor2
        self.rfid = rfid
        self.scale = scale
        self.temp_sensor = temp_sensor


dev = Dev()
