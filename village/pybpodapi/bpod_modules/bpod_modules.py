import importlib
import time


class BpodModules(object):

    LOADED_MODULES = []
    BPOD_API_MODULES = []

    def __init__(self, bpod):
        self.modules = []
        self.bpod = bpod

    def __add__(self, module):
        module.bpod_modules = self
        self.modules.append(module)
        return self

    def __getitem__(self, index):
        return self.modules[index]

    def __len__(self):
        return len(self.modules)

    def __iter__(self):
        return iter(self.modules)

    @staticmethod
    def create_module(
        connected,
        module_name,
        firmware_version,
        events_names,
        n_serial_events,
        serial_port,
    ):
        from pybpodapi.bpod_modules.bpod_module import BpodModule

        # solve issue related with circular imports

        if (
            len(BpodModules.LOADED_MODULES) == 0
            and len(BpodModules.BPOD_API_MODULES) > 0
        ):

            for module2import in BpodModules.BPOD_API_MODULES:
                m = importlib.import_module(module2import)
                BpodModules.LOADED_MODULES.append(m.BpodModule)

            for mclass in BpodModules.LOADED_MODULES:
                if mclass.check_module_type(module_name):
                    return mclass(
                        connected,
                        module_name,
                        firmware_version,
                        events_names,
                        n_serial_events,
                        serial_port,
                    )

        return BpodModule(
            connected,
            module_name,
            firmware_version,
            events_names,
            n_serial_events,
            serial_port,
        )

    def activate_module_relay(self, module):
        index = self.modules.index(module)
        self.bpod._bpodcom_activate_module_relay(index)

    def deactivate_module_relay(self, module):
        index = self.modules.index(module)
        self.bpod._bpodcom_deactivate_module_relay(index)

    def stop_modules_relay(self):
        for m in self.modules:
            m.deactivate_module_relay()

        time.sleep(0.1)
        self.bpod._bpodcom_clean_any_data_in_the_buffer()

    def module_write(self, module, message, dtype=None):
        index = self.modules.index(module)
        self.bpod._bpodcom_module_write(index, message, dtype)

    def module_read(self, module, size, dtype=None):
        index = self.modules.index(module)
        return self.bpod._bpodcom_module_read(index, size, dtype)

    @property
    def relay_is_active(self):
        for m in self.modules:
            if m.relay_active:
                return True

        return False
