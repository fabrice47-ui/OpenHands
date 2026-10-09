"""Prevent console windows from flashing on Windows.

When OpenHands runs on Windows from a process that has no console attached
(e.g. started with ``pythonw``, from a shortcut, a scheduled task or a
service), every console subprocess it spawns (git, python, jupyter,
powershell, ...) gets its own brand new console window, which briefly
flashes open and closed on the desktop.

``hide_subprocess_console_windows`` adds the ``CREATE_NO_WINDOW`` flag to
subprocesses in that situation only. When the current process already has a
console, children share it and no window is created, so nothing is changed
and subprocess output keeps going to the terminal as before.
"""

import subprocess
import sys

_PATCHED_ATTR = '_openhands_hides_console'


def _has_console() -> bool:
    import ctypes

    return bool(ctypes.windll.kernel32.GetConsoleWindow())  # type: ignore[attr-defined]


def hide_subprocess_console_windows() -> None:
    """Patch ``subprocess.Popen`` so children don't open a console window.

    No-op outside Windows, when the process has a visible console, or when
    already applied. Callers that pass an explicit console-related creation
    flag (``CREATE_NEW_CONSOLE``, ``DETACHED_PROCESS`` or ``CREATE_NO_WINDOW``)
    are left untouched.
    """
    if sys.platform != 'win32':
        return
    if getattr(subprocess.Popen.__init__, _PATCHED_ATTR, False):
        return
    if _has_console():
        return

    console_flags = (
        subprocess.CREATE_NEW_CONSOLE
        | subprocess.DETACHED_PROCESS
        | subprocess.CREATE_NO_WINDOW
    )
    original_init = subprocess.Popen.__init__

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        # creationflags is the 14th positional parameter after self;
        # only adjust it when it is passed by keyword or omitted.
        if len(args) < 14:
            flags = kwargs.get('creationflags') or 0
            if not flags & console_flags:
                kwargs['creationflags'] = flags | subprocess.CREATE_NO_WINDOW
        original_init(self, *args, **kwargs)

    setattr(__init__, _PATCHED_ATTR, True)
    subprocess.Popen.__init__ = __init__  # type: ignore[method-assign]
