import selectors
import sys

from .constants import STDIN_TIMEOUT


class SceneStdinError(Exception):
    pass


def detect_stdin_timeout() -> None:
    selector = selectors.DefaultSelector()
    selector.register(sys.stdin, selectors.EVENT_READ)
    something = selector.select(timeout=STDIN_TIMEOUT)
    if not something:
        raise SceneStdinError
    selector.close()
