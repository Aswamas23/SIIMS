"""
pytest configuration for the SIIMS monitoring agent test suite.
Adds the monitoring-agent directory to sys.path so tests can import
agent modules directly (hardware, software, network, etc.).
"""
import os
import sys

# Add the monitoring-agent directory (parent of tests/) to sys.path
_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _AGENT_DIR not in sys.path:
    sys.path.insert(0, _AGENT_DIR)

# Provide a stub winreg module for non-Windows environments
# so software.py can be imported without crashing
if "winreg" not in sys.modules:
    import types
    _fake_winreg = types.ModuleType("winreg")
    _fake_winreg.HKEY_LOCAL_MACHINE = 0x80000002  # type: ignore[attr-defined]
    _fake_winreg.HKEY_CURRENT_USER = 0x80000001   # type: ignore[attr-defined]
    _fake_winreg.REG_SZ = 1                        # type: ignore[attr-defined]
    _fake_winreg.REG_EXPAND_SZ = 2                 # type: ignore[attr-defined]
    _fake_winreg.OpenKey = None                    # type: ignore[attr-defined]
    _fake_winreg.CloseKey = None                   # type: ignore[attr-defined]
    _fake_winreg.EnumKey = None                    # type: ignore[attr-defined]
    _fake_winreg.QueryValueEx = None               # type: ignore[attr-defined]
    sys.modules["winreg"] = _fake_winreg

# Provide stubs for pywin32 modules so agent.py can be imported on non-Windows
for _mod_name in ("win32serviceutil", "win32service", "win32event", "win32api", "win32timezone"):
    if _mod_name not in sys.modules:
        import types
        sys.modules[_mod_name] = types.ModuleType(_mod_name)
