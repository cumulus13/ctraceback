import sys
import logging
from logging.handlers import SysLogHandler
import os
import socket
import traceback
import shutil
import pickle
import argparse
from pathlib import Path
import importlib

from rich.console import Console
from rich.traceback import Traceback #, Trace
from rich.theme import Theme

try:
    from . config import CONFIG
except:
    from config import CONFIG

console = Console(theme = CONFIG().severity_theme)

spec_handler_rabbitmq = importlib.util.spec_from_file_location("rabbitmq", str(Path(__file__).parent / 'handler' / 'rabbitmq.py'))
rabbitmq = importlib.util.module_from_spec(spec_handler_rabbitmq)
spec_handler_rabbitmq.loader.exec_module(rabbitmq)

# try:
#     from . config import CONFIG
# except:
#     from config import CONFIG
    
# try:
#     from . handler import rabbitmq
# except Exception:
#     from handler import rabbitmq

if sys.version_info.major == 3:
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus

try:
    from sqlalchemy import create_engine, Column, Integer, Text, text, func, TIMESTAMP #, String, Boolean, TIMESTAMP, BigInteger, Text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    Base = declarative_base()
except:
    pass

class CTracebackDB(Base):
    __tablename__ = 'traceback'

    id = Column(Integer, primary_key=True,  autoincrement=True)
    created = Column(TIMESTAMP, server_default=func.now())
    message = Column(Text)
    tag = Column(Text, server_default="ctraceback")
    host = Column(Text, server_default='127.0.0.1')

class CTraceback:

    def __init__(self, exc_type = None, exc_value = None, tb = None, to_syslog = True, to_file = True, to_db = False):
        self.config = CONFIG()
        self.to_syslog = to_syslog or self.config.TO_SYSLOG or os.getenv('TRACEBACK_TO_SYSLOG') in ["1", "True", "true", 1]
        self.to_file = to_file or self.config.TO_FILE or os.getenv('TRACEBACK_TO_FILE') in ["1", "True", "true", 1]
        self.to_db = to_db or self.config.TO_DB or os.getenv('TRACEBACK_TO_DB') in ["1", "True", "true", 1]
        # Create syslog handler (UDP for performance)
        self.syslog_handler = SysLogHandler(address=(self.config.SYSLOG_SERVER, int(self.config.SYSLOG_PORT) if self.config.SYSLOG_PORT else 514), socktype=socket.SOCK_DGRAM)
        self.syslog_handler.setLevel(logging.ERROR)
        self.syslog_formatter = logging.Formatter('%(message)s')
        self.syslog_handler.setFormatter(self.syslog_formatter)

        # Create logger for syslog only
        self.syslog_logger = logging.getLogger("SyslogOnly")
        self.syslog_logger.addHandler(self.syslog_handler)
        self.syslog_logger.setLevel(logging.ERROR)
        self.syslog_logger.propagate = False

        # Add a file handler for traceback.log
        self.file_handler = logging.FileHandler(self.config.LOG_FILE or self.config._data_default.get('LOG_FILE'))
        self.file_handler.setLevel(logging.ERROR)
        self.file_formatter = logging.Formatter('%(asctime)s - %(message)s')
        self.file_handler.setFormatter(self.file_formatter)

        # Create logger for file only
        self.file_logger = logging.getLogger("FileOnly")
        self.file_logger.addHandler(self.file_handler)
        self.file_logger.setLevel(logging.ERROR)
        self.file_logger.propagate = False

        if exc_type and exc_value and tb: self.traceback(exc_type, exc_value, tb)

    def create_db(self, username = None, password = None, hostname = None, dbname = None, dbtype = None, port = None):
        if self.config.USE_SQL:
            DB_TYPE = self.config.DB_TYPE
            if DB_TYPE:
                username = username or self.CONFIG.DB_USERNAME or 'traceback_admin'
                password = password or self.CONFIG.DB_PASSWORD or 'Xxxnuxer13'
                hostname = hostname or self.CONFIG.DB_HOSTNAME or '127.0.0.1'
                dbname = dbname or self.CONFIG.DB_BANE or 'ctraceback'
                port = port or self.CONFIG.DB_PORT or ''
                password_encoded = quote_plus(password)
                
                #engine_config = f'{dbtype}://{username}:{password_encoded}@{hostname}/{dbname}'
                engine_config ="{0}://{1}:{2}@{3}:{5}/{4}".format(
                    dbtype,
                    username,
                    password_encoded,
                    hostname,
                    dbname,
                    port
                )            

                engine = create_engine(engine_config, echo=self.CONFIG.DB_LOG)
                
                Base.metadata.create_all(engine)
            
                Session = sessionmaker(bind=engine)
                session = Session()
                
                return session     

    def insert_db(self, message, username=None, password=None, hostname=None, port = None, dbname=None, tag = 'ctracebak'):
        tag = os.getenv('DEBUG_TAG') or os.getenv('DEBUG_APP') or CONFIG.get_config('DEBUG', 'tag') or CONFIG.get_config('app', 'name') or tag or 'debug'
        if self.config.USE_SQL:
            try:
                session = self.create_db(username, password, hostname, dbname, port)
                new_data = CTracebackDB(message=message, tag = tag)
                session.add(new_data)
                session.commit()
                session.close()
                return True
            except:
                if os.getenv('DEBUG') == '1': print(traceback.format_exc())
                return False 
 
    def traceback(self, exc_type, exc_value, tb):
        # sourcery skip: boolean-if-exp-identity, remove-unnecessary-cast
        # Generate plain-text traceback once
        plain_traceback = ''.join(traceback.format_exception(exc_type, exc_value, tb))

        tb_renderable = Traceback.from_exception(exc_type, exc_value, tb, show_locals=True if self.config.SHOW_LOCAL in ["1", 'true', 'True'] else False, width=shutil.get_terminal_size()[0], theme = self.config.THEME or 'fruity')
        console.print(tb_renderable)

        if self.to_syslog:
            # Log to syslog only
            # syslog_message = f"{DEFAULT_TAG}: Complete Traceback:\n{plain_traceback.strip()}"
            syslog_message = f"{self.config.DEFAULT_TAG}: {plain_traceback.strip()}"
            self.syslog_logger.error(syslog_message)
            
        if self.to_db or self.config.USE_SQL:
            self.insert_db(plain_traceback.strip(), tag = self.config.DEFAULT_TAG)

        # Log to file only
        if self.to_file:
            log_message = f"Complete Traceback:\n{plain_traceback.strip()}"
            self.file_logger.error(log_message)

        
        # Extract traceback details as a string
        tb_details = "".join(traceback.format_tb(tb))

        # Serialize the exception data
        serialized_data = pickle.dumps((exc_type.__name__, str(exc_value), tb_details))

        if self.config.TRACEBACK_ACTIVE == 1:
            try:
                # Send the data to the server
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                    client.connect((self.config.TRACEBACK_SERVER, int(self.config.TRACEBACK_PORT)))
                    client.sendall(serialized_data)
            except ConnectionRefusedError:
                console.log("[white on red blink]error send traceback to ctraceback server, this maybe ctraceback server not active/run or connection is error ![/]")
            except Exception:
                console.log(traceback.format_exc())
        if self.config.VERBOSE:
            print(f"is_rabbit_active = {self.config.USE_RABBITMQ}")
            print(f'is_rabbit_active_valid = {self.config.USE_RABBITMQ in [1, True, "1"]}')
        
        if self.config.USE_RABBITMQ in [1, True, "1"]:
            rabbitmq.RabbitMQHandler().send(serialized_data, self.config.VERBOSE)

    @classmethod
    def usage(self):

        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        server_subparser = parser.add_subparsers(dest = "runas", help = "Server arguments")
        
        serve_args = server_subparser.add_parser('serve', help = "Run as server")
        serve_args.add_argument('-H', '--host', default = "127.0.0.1", type=str, help = 'listen on ip/host')
        serve_args.add_argument('-P', '--port', default = 7000, type = int, help = "listen on port number (TCP)")
        serve_args.add_argument('-ha', '--handler', help = 'valid arguments: "socket", "rabbit[mq]", default = "socket"', nargs='*')
        serve_args.add_argument('-q', '--queue', help = 'Queue Name', action = 'store')
        serve_args.add_argument('-x', '--exchange-name', help = 'Exchange Name', action = 'store')
        serve_args.add_argument('-t', '--exchange-type', help = 'Exchange Type', action = 'store')
        serve_args.add_argument('-k', '--routing-key', help = 'Routing Key', action = 'store')
        serve_args.add_argument('-T', '--tag', help = 'Tag', action = 'store')
        serve_args.add_argument('-u', '--username', help = 'Queue Authentication Username', action = 'store')
        serve_args.add_argument('-p', '--password', help = 'Queue Authentication Password', action = 'store')
        serve_args.add_argument('-d', '--durable', help = 'Queue Durable Mode', action = 'store_true')
        serve_args.add_argument('-a', '--ack', help = 'Queue Ack Mode', action = 'store_true')
        serve_args.add_argument('-l', '--last', help = 'Queue with Last N', action = 'store_true')
        serve_args.add_argument('-ln', '--last-number', help = 'N for last', action = 'store')
        serve_args.add_argument('-rh', '--rabbit-host', help = 'RabbitMQ Hostname if run with multiple handler, default is "127.0.0.1"', action = 'store')
        serve_args.add_argument('-rp', '--rabbit-port', help = 'RabbitMQ Port if run with multiple handler, default is 5672', action = 'store')

        parser.add_argument('-t', '--test', action='store_true', help = "Test exception")
        parser.add_argument('-v', '--verbose', help = 'Verbosity', action = 'store_true')

        args = parser.parse_args()

        if len(sys.argv) == 1:
            parser.print_help()
        else:
            if args.test:
                sys.excepthook = CTraceback


                # Example to trigger an exception
                def example_error():
                    raise ValueError("This is a test error for traceback handling!")

                example_error()
            elif args.runas == 'serve':
                if args.host or args.port != 7000:
                    try:
                        from . import server
                    except Exception:
                        import server
                    # def start_server(host = None, port = None, handle = 'socket', exchange_name = None, exchange_type = None, queue_name = None, routing_key = None, username = None, password = None, durable = False, ack = False, last = None, last_number = None, rabbitmq_host = None, rabbitmq_port = None, verbose = False):
                    server.start_server(args.host, args.port, args.handler, args.exchange_name, args.exchange_type, args.queue_name, args.routing_key, args.username, args.password, args.durable, args.ack, args.last, args.last_number, args.rabbit_host, args.rabbit_port, args.verbose) 
                else:
                    parser.print_help()
            else:
                parser.print_help()

# Example usage
if __name__ == "__main__":
    CTraceback.usage()
