from pathlib import Path
from configset import configset
import json
from pydebugger.debug import debug
import os

class CONFIG:
    _config_file = Path.cwd() / 'traceback.json' if (Path.cwd() / 'traceback.json').is_file() else '' or Path(__file__).parent / "traceback.json"
    _config_ini_file = str(Path.cwd() / 'traceback.ini') if (Path.cwd() / 'traceback.ini').is_file() else "" or str(Path(__file__).parent / "traceback.ini")
    config = configset(_config_ini_file)

    _data = {
        # Remote Syslog configuration
        'SYSLOG_SERVER' : config.get_config('syslog', 'host') or '127.0.0.1',
        'SYSLOG_PORT' : str(config.get_config('syslog', 'port')) if config.get_config('syslog', 'port') else '' or '514',
        'TRACEBACK_SERVER' : config.get_config('server', 'host') or '127.0.0.1',
        'TRACEBACK_PORT' : str(config.get_config('server', 'port')) if config.get_config('server', 'port') else '' or 7000,
        'TRACEBACK_ACTIVE' : config.get_config('server', 'active') if config.get_config('server', 'active') in [1,0] else 1,
        'DEFAULT_TAG' : config.get_config('tag', 'name') or "TracebackLogger",
        'SHOW_LOCAL'  : str(config.get_config('rich', 'show_local')) if config.get_config('rich', 'show_local') else '' or "1",
        'THEME'  : config.get_config('rich', 'theme') if config.get_config('rich', 'theme') else '' or "fruity",
        # Configure traceback logging
        'LOG_FILE' : config.get_config('file', 'name') or os.path.join(str(Path(__file__).parent), "traceback.log"),
        'ACCEPTS' : config.get_config_as_list('on_top', 'accepts') or ['WindowsTerminal.exe', 'cmd.exe', 'python.exe'],
        'ON_TOP' : int(config.get_config('on_top', 'active')) if config.get_config('on_top', 'active') else '' or 1,
        'SLEEP' : int(config.get_config('on_top', 'sleep')) if config.get_config('on_top', 'sleep') else '' or 7,
    }

    debug(_data = _data)

    _data_default = _data

    def __init__(self):
        # Load existing configuration if the file exists
        if self._config_file.exists():
            with open(self._config_file, "r") as f:
                self._data = json.load(f)

    def __getattr__(self, name):
        # Retrieve a value from the configuration data
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in {"_config_file", "_data"}:  # Allow setting internal attributes
            super().__setattr__(name, value)
        else:
            # Update the configuration data and save to the file
            self._data[name] = value
            with open(self._config_file, "w") as f:
                json.dump(self._data, f, indent=4)

