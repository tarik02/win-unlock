import argparse
import asyncio
import os
import sys
from typing import Optional
import psutil
import logging
from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.commons.iosettings import RDPIOSettings
import ctypes

from win_unlock.session import SessionState, list_sessions

RDP_URL_ENV_VAR = "WIN_UNLOCK_RDP_URL"

def is_locked():
    return any(p.name() == "LogonUI.exe" for p in psutil.process_iter())

def create_default_iosettings() -> RDPIOSettings:
    iosettings = RDPIOSettings()
    iosettings.performance_flags = 0
    return iosettings

class SessionNotLockedError(Exception):
    pass

class RdpConnectionError(Exception):
    pass

class NoActiveRdpSessionError(Exception):
    pass

class FailedToMoveSessionError(Exception):
    pass

async def unlock(
    rdp_url: str,
    iosettings: Optional[RDPIOSettings] = None,
    logger: Optional[logging.Logger] = None,
    force: bool = False
):
    if logger is None:
        logger = logging.Logger("unlock")
        logger.disabled = True

    logger.debug("Checking if session is locked...")

    if not is_locked() and not force:
        logger.warning("Session is not locked. Skipping")
        raise SessionNotLockedError("Session is not locked. Skipping")

    if iosettings is None:
        logger.warning("No IO settings provided, using default settings")
        iosettings = create_default_iosettings()

    logger.debug("Creating RDP connection factory...")
    factory = RDPConnectionFactory.from_url(rdp_url, iosettings)

    logger.debug("Getting RDP connection...")
    connection = factory.get_connection(iosettings)

    logger.info("Connecting to RDP session...")
    _, err = await connection.connect()
    if err is not None:
        logger.warning('Connection failed: %s', err)
        raise RdpConnectionError('RDP connection failed') from err

    logger.info("RDP connection successful!")

    logger.debug("Looking for active RDP session...")
    for _ in range(50):
        sessions, _ = await list_sessions()

        rdp_session = next((s for s in sessions if s.name == "rdp-tcp#0" and s.state == SessionState.ACTIVE), None)

        if rdp_session is not None:
            break

        await asyncio.sleep(0.1)
    else:
        logger.warning("No active RDP session found after multiple attempts.")
        raise NoActiveRdpSessionError("RDP connection succeeded but no active RDP session found after multiple attempts.")

    await asyncio.sleep(0.1)

    logger.debug("Moving RDP session to console...")

    proc = await asyncio.create_subprocess_exec(
        'tscon', str(rdp_session.id), '/dest:console',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.warning("Failed to move RDP session to console with return code %d", proc.returncode)
        raise FailedToMoveSessionError(f"Failed to move RDP session to console with return code {proc.returncode}, stdout: {stdout.decode()}, stderr: {stderr.decode()}")

    logger.debug("Waiting for RDP connection to be disconnected...")
    await connection.disconnected_evt.wait()
    logger.debug("RDP connection disconnected.")

    logger.info("Session should be unlocked now!")

async def main():
    parser = argparse.ArgumentParser(description="Unlock the current Windows session using RDP")
    rdp_url_group = parser.add_mutually_exclusive_group()
    rdp_url_group.add_argument("--rdp-url", help="RDP connection URL in the format rdp+ntlm-password://username:password@host:port")
    rdp_url_group.add_argument("--rdp-url-file", metavar="FILE", help="Path to a file containing the RDP connection URL")
    parser.add_argument("--width", type=int, help="RDP session width in pixels (must be used with --height)")
    parser.add_argument("--height", type=int, help="RDP session height in pixels (must be used with --width)")
    parser.add_argument("--force", action="store_true", help="Force unlock even if session is not locked")
    args = parser.parse_args()

    if (args.width is None) != (args.height is None):
        parser.error("--width and --height must be provided together")

    if args.rdp_url:
        rdp_url = args.rdp_url
    elif args.rdp_url_file:
        with open(args.rdp_url_file) as f:
            rdp_url = f.read().strip()
    elif RDP_URL_ENV_VAR in os.environ:
        rdp_url = os.environ[RDP_URL_ENV_VAR]
    else:
        parser.error(f"RDP URL must be provided via --rdp-url, --rdp-url-file, or the {RDP_URL_ENV_VAR} environment variable")

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("win_unlock")

    iosettings = create_default_iosettings()

    if args.width is not None:
        iosettings.video_width = args.width
        iosettings.video_height = args.height
    else:
        iosettings.video_width = ctypes.windll.user32.GetSystemMetrics(0)
        iosettings.video_height = ctypes.windll.user32.GetSystemMetrics(1)

    try:
        await unlock(rdp_url, iosettings=iosettings, logger=logger, force=args.force)
    except SessionNotLockedError:
        print('Session is not locked. Use --force to force unlock.')
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
