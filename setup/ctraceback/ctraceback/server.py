import socket
import pickle
import traceback
from rich.console import Console
from rich.text import Text
import shutil
import datetime
import sys
import signal

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

# Server configuration
HOST = config.TRACEBACK_SERVER or config._data_default.get('TRACEBACK_SERVER') or '127.0.0.1'
PORT = int(str(config.TRACEBACK_PORT or config._data_default.get('TRACEBACK_PORT') or 7000))

# Rich console for colorized output
console = Console()

# Function to format and print traceback with colors
def print_traceback(exc_type, exc_value, tb_details):
    terminal_width = shutil.get_terminal_size()[0]

    # Timestamp
    timestamp = datetime.datetime.now().strftime("[bold #FF00FF]%Y[/]-[bold #0055FF]%m[/]-[bold #FF55FF]%d[/] [bold #FFFF00]%H[/]:[bold #FF5500]%M[/]:[bold #AAAAFF]%S[/].[bold #00FF00]%f[/]")
    console.print(f"[bold]{timestamp}[/bold] - ", end='')

    # Format traceback parts with colors
    type_text = Text(str(exc_type), style="white on red blink")
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

# Server to listen for traceback data
def start_server(host = None, port = None):
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

def handle_exit_signal(signum, frame):
    """Handle termination signals."""
    console.print("\n[bold #FF00FF]Shutting down server...[/]")
    if server_socket:
        server_socket.close()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_exit_signal)  # Handle Ctrl+C (SIGINT)
signal.signal(signal.SIGTERM, handle_exit_signal)  # Handle termination signal

if __name__ == "__main__":
    start_server()
