"""Guardian Angel -- IPC Layer

Public API for the multiprocessing subsystem.
"""

from .shared_state import SharedState
from .supervisor import ProcessSupervisor

__all__ = ["SharedState", "ProcessSupervisor"]
