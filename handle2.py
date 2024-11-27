import ctypes
from ctypes import wintypes
import psutil
import os

def get_current_window_handle():
    hwnd_list = []

    # Get the current process ID
    current_pid = os.getpid()

    # Callback function for EnumWindows
    def enum_windows_callback(hwnd, lParam):
        # Get the process ID associated with this window
        process_id = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value == current_pid:
            hwnd_list.append(hwnd)
        return True

    # Call EnumWindows to enumerate all top-level windows
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    EnumWindows(EnumWindowsProc(enum_windows_callback), 0)

    # Return the first matching window handle, if found
    return hwnd_list[0] if hwnd_list else None

if __name__ == "__main__":
    hwnd = get_current_window_handle()
    if hwnd:
        print(f"Window Handle: {hwnd}")
    else:
        print("No window handle found for the current process.")
