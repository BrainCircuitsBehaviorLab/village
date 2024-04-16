import logging
import os

from pybpodapi.bpod.bpod_com_protocol_modules import BpodCOMProtocolModules
from pybpodapi.session import Session

from village.settings import settings

logger = logging.getLogger(__name__)


class BpodIO(BpodCOMProtocolModules):
    """
    Bpod I/O logic.
    """

    def __init__(
        self,
        serial_port=None,
        workspace_path=None,
        session_name=None,
        sync_channel=None,
        sync_mode=None,
    ):
        self.workspace_path = (
            workspace_path
            if workspace_path is not None
            else settings.get("SESSIONS_DIRECTORY")
        )
        self.session_name = session_name if session_name is not None else "session"

        super(BpodIO, self).__init__(serial_port, sync_channel, sync_mode)

    def create_session(self):
        return (
            Session(os.path.join(self.workspace_path, self.session_name) + ".csv")
            if self.workspace_path
            else Session()
        )

    def close(self):
        """
        Close connection with Bpod
        """
        super(BpodIO, self).close()

    def __del__(self):
        if hasattr(self, "session") and self.session:
            del self._session

    @property
    def workspace_path(self):
        return self._workspace_path

    @workspace_path.setter
    def workspace_path(self, value):
        self._workspace_path = value

    @property
    def session_name(self):
        return self._session_name

    @session_name.setter
    def session_name(self, value):
        self._session_name = value  # type: str
