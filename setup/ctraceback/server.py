import socket
import pickle
import traceback
from rich.text import Text
import shutil
import datetime
import sys
import os
import signal
import time
from pydebugger.debug import debug
try:
    from . custom_traceback import console
except:
    from custom_traceback import console

try:
    from . config import CONFIG
except:
    from config import CONFIG

if sys.platform == 'win32':
    try:
        from . import on_top
    except:
        import on_top

config = CONFIG()
server_socket = None

# Server configuration
HOST = config.TRACEBACK_SERVER or config._data_default.get('TRACEBACK_SERVER') or '127.0.0.1'
PORT = int(str(config.TRACEBACK_PORT or config._data_default.get('TRACEBACK_PORT') or 7000))

# Rich console for colorized output
# console = Console()

# Function to format and print traceback with colors
def print_traceback(exc_type, exc_value, tb_details):
    terminal_width = shutil.get_terminal_size()[0]

    # Timestamp
    timestamp = datetime.datetime.now().strftime("[bold #FF00FF]%Y[/]-[bold #0055FF]%m[/]-[bold #FF55FF]%d[/] [bold #FFFF00]%H[/]:[bold #FF5500]%M[/]:[bold #AAAAFF]%S[/].[bold #00FF00]%f[/]")
    console.print(f"[bold]{timestamp}[/bold] - ", end='')

    # Format traceback parts with colors
    type_text = Text(str(exc_type), style="white on red")
    value_text = Text(str(exc_value), style="black on #FFFF00")
    # tb_text = Text("".join(traceback.format_tb(tb)), style="green")
    tb_text = Text(tb_details, style="#00FFFF")

    # Print the traceback parts
    console.print(type_text, end = '')
    console.print(": ", end = '')
    console.print(value_text)
    console.print(tb_text)

    # Separator line
    console.print("-" * terminal_width)

def call_back_rabbitmq(ch, met, prop, body):
    debug(body = body, debug = config.VERBOSE)
    exc_type, exc_value, tb_details = pickle.loads(body)
    # Print the traceback
    print_traceback(exc_type, exc_value, tb_details)
    ch.basic_ack(delivery_tag = met.delivery_tag)
    
# Server to listen for traceback data
def start_server(host = None, port = None, handle = 'socket'):
    if not handle or handle == 'socket':
        global server_socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                console.print(f"[bold #FFAA00]Server is listening on[/] [bold #00FFFF]{host or HOST}[/]:[bold #FF55FF]{port or PORT}[/]")

                server_socket = server
                server.bind((host or HOST, int(port or PORT)))
                server.listen()
                
                while True:
                    conn, addr = server.accept()
                    with conn:
                        console.print(f"[blue]Connected by {addr}[/blue]")

                        # Receive serialized data
                        data = b""
                        while True:
                            packet = conn.recv(4096)
                            if not packet: break
                            data += packet
                            if config.ON_TOP == 1 and sys.platform == 'win32': on_top.set()

                        # Deserialize data
                        exc_type, exc_value, tb_details = pickle.loads(data)

                        # Print the traceback
                    print_traceback(exc_type, exc_value, tb_details)
        except KeyboardInterrupt:
            server_socket.close()
            sys.exit()
    elif handle in ['rabbit', 'rabbitmq']:
        if not config.USE_RABBITMQ in [1, True, "1"]:
            console.print(f"[error]Handle with 'RabbitMQ' but not activated, please active before in config file '{config._config_file}' or see documentation 'README.md' ![/]")
            exit()        
        try:
            from . handler import rabbitmq
        except Exception:
            from handler import rabbitmq
        console.print(f"[notice]Run with[/] [error]RabbitMQ \[{handle}][/] [notice]handler ![/] [warning]{config.RABBITMQ_HOST}[/]:[debug]{config.RABBITMQ_PORT}[/]/[critical]{config.RABBITMQ_EXCHANGE_NAME or 'ctraceback'}[/]")            
        while 1:
            try:
                handler = rabbitmq.RabbitMQHandler().consume(call_back_rabbitmq, verbose = config.VERBOSE)
            except Exception:
                console.print("[error] connection error, re-connection ...[/]")
                time.sleep(int(config.SLEEP) if config.SLEEP else 1)

def handle_exit_signal(signum, frame):
    """Handle termination signals."""
    console.print("\n[error]Shutting down server...[/]")
    global server_socket
    if server_socket: server_socket.close()
    os.kill(os.getpid(), signal.SIGTERM)
    # while 1:
    #     try:
    #         os.kill(os.getpid(), signal.SIGTERM)
    #         break
    #     except Exception:
    #         sys.exit(0)
    #         time.sleep(1)

# Register signal handlers
signal.signal(signal.SIGINT, handle_exit_signal)  # Handle Ctrl+C (SIGINT)
signal.signal(signal.SIGTERM, handle_exit_signal)  # Handle termination signal

if __name__ == "__main__":
    start_server()
