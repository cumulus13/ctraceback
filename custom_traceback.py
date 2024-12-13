import logging
from logging.handlers import SysLogHandler
# import os
import socket
import traceback
import shutil
import pickle
import argparse

from rich.console import Console
from rich.traceback import Traceback #, Trace
# Initialize Rich Console
console = Console()

try:
    from . config import CONFIG
except:
    from config import CONFIG

class CTraceback:

    def __init__(self, exc_type, exc_value, tb):
        self.config = CONFIG()
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

        self.custom_exception_handler(exc_type, exc_value, tb)
 
    def custom_exception_handler(self, exc_type, exc_value, tb):
        # Generate plain-text traceback once
        plain_traceback = ''.join(traceback.format_exception(exc_type, exc_value, tb))

        tb_renderable = Traceback.from_exception(exc_type, exc_value, tb, show_locals=True if self.config.SHOW_LOCAL in ["1", 'true', 'True'] else False, width=shutil.get_terminal_size()[0], theme = self.config.THEME or 'fruity')
        console.print(tb_renderable)

        # Log to syslog only
        # syslog_message = f"{DEFAULT_TAG}: Complete Traceback:\n{plain_traceback.strip()}"
        syslog_message = f"{self.config.DEFAULT_TAG}: {plain_traceback.strip()}"
        self.syslog_logger.error(syslog_message)

        # Log to file only
        log_message = f"Complete Traceback:\n{plain_traceback.strip()}"
        self.file_logger.error(log_message)

        if self.config.TRACEBACK_ACTIVE == 1:
            # Extract traceback details as a string
            tb_details = "".join(traceback.format_tb(tb))

            # Serialize the exception data
            serialized_data = pickle.dumps((exc_type.__name__, str(exc_value), tb_details))

            try:
                # Send the data to the server
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                    client.connect((self.config.TRACEBACK_SERVER, self.config.TRACEBACK_PORT))
                    client.sendall(serialized_data)
            except ConnectionRefusedError:
                pass
            except:
                console.log(traceback.format_exc())

    @classmethod
    def usage(self):
        import sys

        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        server_subparser = parser.add_subparsers(dest = "runas", help = "Server arguments")
        
        serve_args = server_subparser.add_parser('serve', help = "Run as server")
        serve_args.add_argument('-b', '--host', default = "127.0.0.1", type=str, help = 'listen on ip/host')
        serve_args.add_argument('-p', '--port', default = 7000, type = int, help = "listen on port number (TCP)")

        parser.add_argument('-t', '--test', action='store_true', help = "Test exception")

        args = parser.parse_args()

        if len(sys.argv) == 1:
            parser.print_help()
        else:
            if args.test:
                import sys
                sys.excepthook = CTraceback


                # Example to trigger an exception
                def example_error():
                    raise ValueError("This is a test error for traceback handling!")

                example_error()
            elif args.runas == 'serve':
                if args.host or args.port != 7000:
                    try:
                        from . import server
                    except:
                        import server
                    server.start_server(args.host, args.port)
                else:
                    parser.print_help()
            else:
                parser.print_help()

# Example usage
if __name__ == "__main__":
    CTraceback.usage()