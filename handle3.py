import ctypes
from ctypes import wintypes
import psutil
import os

def get_parent_window_handle():
    hwnd_list = []

    # Get the parent process ID
    current_process = psutil.Process(os.getpid())
    parent_pid = current_process.ppid()  # Get parent process ID

    # Callback function for EnumWindows
    def enum_windows_callback(hwnd, lParam):
        # Get the process ID associated with this window
        process_id = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value == parent_pid:
            hwnd_list.append(hwnd)
        return True

    # Call EnumWindows to enumerate all top-level windows
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    EnumWindows(EnumWindowsProc(enum_windows_callback), 0)

    # Return the first matching window handle, if found
    return hwnd_list[0] if hwnd_list else None

if __name__ == "__main__":
    import time
    time.sleep(5)
    hwnd = get_parent_window_handle()
    if hwnd:
        print(f"Window Handle of the parent process: {hwnd}")
    else:
        print("No window handle found for the parent process.")
