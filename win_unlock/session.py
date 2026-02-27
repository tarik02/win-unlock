import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from win_unlock.parse_columns import parse_columns

class SessionState(Enum):
    ACTIVE = "Active"
    DISC = "Disc"
    LISTEN = "Listen"
    CONNQ = "ConnQ"
    CONN = "Conn"
    DOWN = "Down"

@dataclass
class Session:
    name: str
    username: Optional[str]
    id: int
    state: SessionState
    type: Optional[str]
    device: Optional[str]

class ListSessionsError(Exception):
    pass

async def list_sessions() -> tuple[list[Session], Optional[Session]]:
    proc = await asyncio.create_subprocess_exec(
        'qwinsta',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise ListSessionsError(f"qwinsta failed with return code {proc.returncode}, stdout: {stdout.decode()}, stderr: {stderr.decode()}")

    column_names, data, active_index = parse_columns(stdout.decode())

    sessions = []

    for row in data:
        session_dict = dict(zip(column_names, row))

        session = Session(
            name=session_dict.get('SESSIONNAME'),
            username=session_dict.get('USERNAME'),
            id=int(session_dict.get('ID')),
            state=SessionState(session_dict.get('STATE')),
            type=session_dict.get('TYPE'),
            device=session_dict.get('DEVICE')
        )

        sessions.append(session)

    return sessions, sessions[active_index] if active_index is not None else None
