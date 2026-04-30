"""Pytest conftest — stubs out PyQt6 so queue-logic tests run without Qt installed."""
import sys
import types
import queue as _queue


def _make_signal_stub():
    class _Signal:
        def __init__(self, *args):
            self._cbs = []
        def connect(self, cb):
            self._cbs.append(cb)
        def emit(self, *args):
            for cb in self._cbs:
                cb(*args)
    return _Signal


if "PyQt6" not in sys.modules:
    _Signal = _make_signal_stub()

    class _QObject:
        def __init__(self, parent=None):
            pass

    class _QThread(_QObject):
        def start(self): pass
        def wait(self): pass

    # Build the minimal fake PyQt6 package tree
    pyqt6 = types.ModuleType("PyQt6")
    core = types.ModuleType("PyQt6.QtCore")
    core.QThread = _QThread
    core.QObject = _QObject
    core.pyqtSignal = _Signal
    core.pyqtSlot = lambda *a, **kw: (lambda f: f)  # pass-through decorator
    core.Qt = types.SimpleNamespace(
        AlignmentFlag=types.SimpleNamespace(AlignCenter=None),
        Orientation=types.SimpleNamespace(Horizontal=None),
        AspectRatioMode=types.SimpleNamespace(KeepAspectRatio=None),
        TransformationMode=types.SimpleNamespace(SmoothTransformation=None),
        ItemFlag=types.SimpleNamespace(ItemIsSelectable=0),
    )

    pyqt6.QtCore = core
    sys.modules["PyQt6"] = pyqt6
    sys.modules["PyQt6.QtCore"] = core

    # Stub out other PyQt6 submodules that may be transitively imported
    for sub in ("QtWidgets", "QtGui", "QtMultimedia", "QtMultimediaWidgets"):
        mod = types.ModuleType(f"PyQt6.{sub}")
        sys.modules[f"PyQt6.{sub}"] = mod
