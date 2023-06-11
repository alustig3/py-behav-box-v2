from __future__ import annotations
from typing import TYPE_CHECKING

from Events.PybEvents import TaskEvent

if TYPE_CHECKING:
    from Tasks.Task import Task


class LoggerEvent:
    """
        Simple class defining the base requirements for a Task Event.

        Attributes
        ----------
        task : Task
            Task the event corresponds to
        metadata : Object
            Any metadata related to the Event
    """

    def __init__(self, event: TaskEvent, name: str, eid: str, entry_time: float):
        self.entry_time = entry_time
        self.event = event
        self.name = name
        self.eid = eid
