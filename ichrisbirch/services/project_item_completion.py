"""When a project item or one of its tasks was finished.

Both rows store `completed` as a boolean and `completed_at` as the timestamp
beside it. The two update endpoints write through here so the pair cannot drift:
an item whose `completed` says true and whose `completed_at` says nothing is a
row no reader can interpret.
"""

from datetime import UTC
from datetime import datetime

from ichrisbirch.models.project import ProjectItem
from ichrisbirch.models.project import ProjectItemTask


def stamp_completion(row: ProjectItem | ProjectItemTask, was_completed: bool, update_data: dict) -> None:
    """Record or clear the completion time when `completed` changes value.

    Only a transition writes. Re-sending `completed: true` on a finished row
    leaves the recorded time alone, because the second call finished nothing —
    and on a finished row whose time is unknown it leaves the null alone rather
    than stamping today onto history.
    """
    if 'completed' not in update_data:
        return
    completed = update_data['completed']
    if completed == was_completed:
        return
    row.completed_at = datetime.now(UTC) if completed else None
