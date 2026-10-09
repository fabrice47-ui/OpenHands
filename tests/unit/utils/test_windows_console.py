import subprocess
import sys
from unittest import mock

import pytest

from openhands.utils import windows_console

CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_CONSOLE = 0x00000010
DETACHED_PROCESS = 0x00000008


@pytest.fixture
def fake_windows(monkeypatch):
    """Simulate Windows constants and record the kwargs Popen receives."""
    calls = []

    def fake_init(self, *args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(sys, 'platform', 'win32')
    monkeypatch.setattr(subprocess, 'CREATE_NO_WINDOW', CREATE_NO_WINDOW, raising=False)
    monkeypatch.setattr(
        subprocess, 'CREATE_NEW_CONSOLE', CREATE_NEW_CONSOLE, raising=False
    )
    monkeypatch.setattr(subprocess, 'DETACHED_PROCESS', DETACHED_PROCESS, raising=False)
    monkeypatch.setattr(subprocess.Popen, '__init__', fake_init)
    return calls


def test_noop_outside_windows(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'linux')
    original = subprocess.Popen.__init__
    windows_console.hide_subprocess_console_windows()
    assert subprocess.Popen.__init__ is original


def test_noop_when_console_present(fake_windows):
    original = subprocess.Popen.__init__
    with mock.patch.object(windows_console, '_has_console', return_value=True):
        windows_console.hide_subprocess_console_windows()
    assert subprocess.Popen.__init__ is original


def test_adds_create_no_window_without_console(fake_windows):
    with mock.patch.object(windows_console, '_has_console', return_value=False):
        windows_console.hide_subprocess_console_windows()
        patched = subprocess.Popen.__init__
        # Applying twice must not wrap again
        windows_console.hide_subprocess_console_windows()
    assert subprocess.Popen.__init__ is patched

    subprocess.Popen.__init__(object(), ['git', 'status'])
    subprocess.Popen.__init__(object(), ['git'], creationflags=0x200)
    subprocess.Popen.__init__(object(), ['x'], creationflags=CREATE_NEW_CONSOLE)
    subprocess.Popen.__init__(object(), ['x'], creationflags=DETACHED_PROCESS)

    assert fake_windows[0][1]['creationflags'] == CREATE_NO_WINDOW
    assert fake_windows[1][1]['creationflags'] == 0x200 | CREATE_NO_WINDOW
    assert fake_windows[2][1]['creationflags'] == CREATE_NEW_CONSOLE
    assert fake_windows[3][1]['creationflags'] == DETACHED_PROCESS
