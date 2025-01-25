from pathlib import Path
from configset import configset
import json
from pydebugger.debug import debug
import os
from rich.theme import Theme
from rich.console import Console

class CONFIG:
    _config_file = Path.cwd() / 'traceback.json' if (Path.cwd() / 'traceback.json').is_file() else '' or Path(__file__).parent / "traceback.json"
    _config_ini_file = str(Path.cwd() / 'traceback.ini') if (Path.cwd() / 'traceback.ini').is_file() else "" or str(Path(__file__).parent / "traceback.ini")
    config = configset(_config_ini_file)
    
    severity_theme = Theme({
        "emergency": "#FFFFFF on #ff00ff",
        "emerg": "#FFFFFF on #ff00ff",
        "alert": "white on #005500",
        "ale": "white on #005500",
        "aler": "white on #005500",
        'critical': "white on #0000FF",
        'criti': "white on #0000FF",
        'crit': "white on #0000FF",
        "error": "white on red",
        "err": "white on red",
        "warning": "black on #FFFF00",
        "warni": "black on #FFFF00",
        "warn": "black on #FFFF00",
        'notice': "black on #55FFFF",
        'notic': "black on #55FFFF",
        'noti': "black on #55FFFF",
        "info": "bold #AAFF00",
        "debug": "black on #FFAA00",
        "deb": "black on #FFAA00",
        "unknown": "white on #FF00FF"
    })
    
    console = Console(theme = severity_theme)

    _data = {
        # Remote Syslog configuration
        'VERBOSE' : config.get_config('debug', 'verbose') or False,
        'SYSLOG_SERVER' : config.get_config('syslog', 'host') or '127.0.0.1',
        'SYSLOG_PORT' : str(config.get_config('syslog', 'port')) if config.get_config('syslog', 'port') else '' or '514',
        'TRACEBACK_SERVER' : config.get_config('server', 'host') or '127.0.0.1',
        'TRACEBACK_PORT' : str(config.get_config('server', 'port')) if config.get_config('server', 'port') else '' or 7000,
        'TRACEBACK_ACTIVE' : config.get_config('server', 'active') if config.get_config('server', 'active') in [1,0] else 1,
        'DEFAULT_TAG' : config.get_config('tag', 'name') or "TracebackLogger",
        'SHOW_LOCAL'  : str(config.get_config('rich', 'show_local')) if config.get_config('rich', 'show_local') else '' or "1",
        'THEME'  : config.get_config('rich', 'theme') or "fruity",
        # Configure traceback logging
        'LOG_FILE' : config.get_config('file', 'name') or os.path.join(str(Path(__file__).parent), "traceback.log"),
        'ACCEPTS' : config.get_config_as_list('on_top', 'accepts') or ['WindowsTerminal.exe', 'cmd.exe', 'python.exe'],
        'ON_TOP' : int(config.get_config('on_top', 'active') or '0') or False,
        'SLEEP' : int(config.get_config('on_top', 'sleep') or '0') or 1,   
        
        'USE_SQL' : int(config.get_config('db', 'active') or '0') or False, 
        'DB_TYPE' : config.get_config('db', 'type') or '', 
        'DB_NAME' : config.get_config('db', 'name') or 'ctraceback',
        'DB_USERNAME' : config.get_config('db', 'username') or '', 
        'DB_PASSWORD' : config.get_config('db', 'password') or '', 
        'DB_HOST' : config.get_config('db', 'HOST') or '', 
        'DB_PORT' : config.get_config('db', 'PORT') or '', 
        'DB_LOG' : config.get_config('db', 'LOG') or False, 
        'TO_SYSLOG' : config.get_config('syslog', 'active') or False, 
        'TO_FILE' : config.get_config('file', 'active') or False, 
        'TO_DB' : config.get_config('db', 'active') or False, 
        
        'USE_RABBITMQ' : config.get_config('rabbitmq', 'active') or os.getenv('CTRACEBACK_RABBITMQ') in ['1', 'true', 'True', 'TRUE'] or False, 
        'RABBITMQ_HOST' : config.get_config('rabbitmq', 'host') or '127.0.0.1', 
        'RABBITMQ_PORT' : config.get_config('rabbitmq', 'port') or 5672, 
        'RABBITMQ_USERNAME' : config.get_config('rabbitmq', 'username') or 'guest', 
        'RABBITMQ_PASSWORD' : config.get_config('rabbitmq', 'password') or 'guest', 
        'RABBITMQ_EXCHANGE_NAME' : config.get_config('rabbitmq', 'exchange_name') or 'ctraceback', 
        'RABBITMQ_EXCHANGE_TYPE' : config.get_config('rabbitmq', 'exchange_type') or 'ctraceback', 
        'RABBITMQ_MAX_LENGTH' : config.get_config('rabbitmq', 'max_length') or 100, 
        'RABBITMQ_DURABLE' : config.get_config('rabbitmq', 'durable') or False, 
        'RABBITMQ_ACK' : config.get_config('rabbitmq', 'ack') or False, 
        'RABBITMQ_ROUTING_KEY' : config.get_config_as_list('rabbitmq', 'routing_key') if config.get_config('rabbitmq', 'routing_key') else [] or ['ctraceback.error', 'ctraceback.100'], 
        'RABBITMQ_CONSUMER_TAG' : config.get_config_as_list('rabbitmq', 'consumer_tag') if config.get_config('rabbitmq', 'consumer_tag') else '' or 'all', 
        
        'USE_KAFKA' : config.get_config('kafka', 'active') or os.getenv('CTRACEBACK_KAFKA') in ['1', 'true', 'True', 'TRUE'] or False, 
        'KAFKA_BOOTSTRAP_SERVER' : config.get_config('kafka', 'host') or '127.0.0.1', 
        'KAFKA_PORT' : config.get_config('kafka', 'port') or 5672, 
        'KAFKA_USERNAME' : config.get_config('kafka', 'username') or 'guest', 
        'KAFKA_PASSWORD' : config.get_config('kafka', 'password') or 'guest', 
        'KAFKA_TOPIC_NAME' : config.get_config('kafka', 'topic') or 'log', 
        'KAFKA_GROUP_ID' : config.get_config('kafka', 'group') or 'ctraceback', 
        'KAFKA_MAX_LENGTH' : config.get_config('kafka', 'max_length') or 100, 
        
        'USE_PULSAR' : config.get_config('pulsar', 'active') or os.getenv('CTRACEBACK_PULSAR') in ['1', 'true', 'True', 'TRUE'] or False, 
        'PULSAR_HOST' : config.get_config('pulsar', 'host') or '192.168.100.1', 
        'PULSAR_PORT' : config.get_config('pulsar', 'port') or 6650, 
        'PULSAR_USERNAME' : config.get_config('pulsar', 'username') or 'pulsar', 
        'PULSAR_PASSWORD' : config.get_config('pulsar', 'password') or 'pulsar', 
        'PULSAR_TENANT' : config.get_config('pulsar', 'tenant') or 'ctraceback_tenant',
        'PULSAR_NAMESPACE' : config.get_config('pulsar', 'namespace') or 'ctraceback_namespace',  
        'PULSAR_TOPIC' : config.get_config('pulsar', 'topic') or 'ctraceback_topic', 
        'PULSAR_SUB' : config.get_config('pulsar', 'sub') or 'ctraceback_sub', 
        'PULSAR_MAX_LENGTH' : config.get_config('pulsar', 'max_length') or 100, 
        'PULSAR_AUTH_TOKEN': config.get_config('pulsar', 'token') or '', 
        'PULSAR_VERBOSE': config.get_config('pulsar', 'verbose') or '', 
        
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
        elif self._config_file.exists() and not name in self._data and name in self._data_default:
            self.__setattr__(name, '')
            return self._data[name]
            
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @classmethod
    def get_config(cls, section, option):
        return cls.config.get_config(section, option)
    
    @classmethod
    def write_config(cls, section, option):
        return cls.config.write_config(section, option)

    @classmethod
    def set(cls, key, value):
        key = str(key).upper()  
        cls.console.print(f"[bold #FFFF00]Write/Set config[/] [bold #00FFFF]{key}[/] [bold #FFAAFF]-->[/] [bold ##00AAFF]{value if value else ''}[/]")
        if str(value).isdigit(): value = int(value)
        return CONFIG().__setattr__(key, value)
    
    def __setattr__(self, name, value):
        if name in {"_config_file", "_data"}:  # Allow setting internal attributes
            super().__setattr__(name, value)
        else:
            # Update the configuration data and save to the file
            self._data[name] = value
            with open(self._config_file, "w") as f:
                json.dump(self._data, f, indent=4)

