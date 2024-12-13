import pygetwindow as gw
import time
import sys
import os
import win32gui
import win32con
import win32process
import ctypes
from ctypes import wintypes
import psutil

try:
    from . config import CONFIG
except:
    from config import CONFIG

config = CONFIG()

def set_window_always_on_top(hwnd):
    """Set a window to always be on top."""
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    )

def unset_window_always_on_top(hwnd):
    """Unset a window's always-on-top property."""
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_NOTOPMOST,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    )

def restore_and_focus_window(hwnd):
    """Restore and bring a window to the foreground."""
    if win32gui.IsIconic(hwnd):  # Check if the window is minimized
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Restore the window
    # Attempt to bring the window to the foreground
    if not win32gui.SetForegroundWindow(hwnd):
        attach_thread_input_and_focus(hwnd)

def attach_thread_input_and_focus(hwnd):
    """Attach input threads to set a window as foreground."""
    current_thread_id = win32process.GetCurrentThreadId()
    foreground_window = win32gui.GetForegroundWindow()
    if foreground_window:
        foreground_thread_id, _ = win32process.GetWindowThreadProcessId(foreground_window)
        if ctypes.windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, True):
            win32gui.SetForegroundWindow(hwnd)
            ctypes.windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)

# Get the current active window before making changes
def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    return hwnd

# Find Windows Terminal window
def find_terminal_window():
    for window in gw.getWindowsWithTitle('Windows Terminal'):
        if 'Windows Terminal' in window.title:
            return window
    return None

def get_window_title(hwnd):
    # Define buffer size
    length = 256  # Maximum length of a window title
    buffer = ctypes.create_unicode_buffer(length)
    # Call GetWindowTextW to fetch the title
    ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length)
    return buffer.value

def get_parent_window_handle():
    find_pid = None
    # Callback function for EnumWindows
    def enum_windows_callback(hwnd, lParam):
        # Get the process ID associated with this window
        process_id = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        # if process_id.value == parent_pid:
        if process_id.value == find_pid:
            hwnd_list.append(hwnd)
        return True

    hwnd_list = []

    # Get the parent process ID
    current_process = psutil.Process(os.getpid())
    # print(f"current_process: {current_process}")
    # parent_pid = current_process.ppid()  # Get parent process ID
    parents = current_process.parents()
    # print(f"parent_pid: {parents}")

    accepts = config.ACCEPTS or config._data_default.get('ACCEPTS') or ['WindowsTerminal.exe', 'cmd.exe', 'python.exe']

    for p in parents:
        # print(f"p.name(): {p.name()}")
        if p.name() in accepts:
            find_pid = p.pid
    
    # print(f"find_pid: {find_pid}")

    if find_pid:
        # Call EnumWindows to enumerate all top-level windows
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        EnumWindows(EnumWindowsProc(enum_windows_callback), 0)

    # print(f"hwnd_list: {hwnd_list}")
    # Return the first matching window handle, if found
    return hwnd_list[0] if hwnd_list else None

def set():
    active_window = get_active_window()
    # print(f"active_window: {active_window}")
    title = get_window_title(active_window)
    # print(f"title: {title}")
    active_terminal = get_parent_window_handle()
    # print(f"active_terminal: {active_terminal}")
    title_active_terminal = get_window_title(active_terminal)
    # print(f"title_active_terminal: {title_active_terminal}")
    # print("Setting Windows Terminal to always on top and bringing it to foreground.")
    set_window_always_on_top(active_terminal)
    # win32gui.SetForegroundWindow(active_terminal)  # Bring to foreground
    time.sleep(
        config.SLEEP or config._data_default.get('SLEEP') or 7
    )
    unset_window_always_on_top(active_terminal)
    try:
        win32gui.SetForegroundWindow(active_window)  # Bring to foreground
    except:
        pass
    
    # sys.exit()
    # Find Windows Terminal window
    # terminal_window = find_terminal_window()
    # if terminal_window is None:
    #     print("Windows Terminal is not open.")
    # else:
    #     # Set Windows Terminal always on top and bring it to the foreground
    #     print("Setting Windows Terminal to always on top and bringing it to foreground.")
    #     set_window_always_on_top(terminal_window._hWnd)
    #     win32gui.SetForegroundWindow(terminal_window._hWnd)  # Bring to foreground

    #     # Wait for 10 seconds
    #     time.sleep(10)

    #     # Revert Windows Terminal always-on-top
    #     print("Reverting Windows Terminal to normal.")
    #     unset_window_always_on_top(terminal_window._hWnd)

    #     # Restore focus to the previously active window
    #     if active_window and win32gui.IsWindow(active_window):
    #         try:
    #             restore_and_focus_window(active_window)
    #         except Exception as e:
    #             print(f"Error restoring previous window: {e}")
