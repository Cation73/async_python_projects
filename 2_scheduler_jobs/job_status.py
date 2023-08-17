import enum


class JobStatus(enum.Enum):

    QUEUE = 0
    PROGRESS = 1
    COMPLETED = 2
    ERROR = 3
