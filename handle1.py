import psutil
import ctypes
from ctypes import wintypes

def get_parent_window_handle():
    # Get the current process's parent process
    current_process = psutil.Process()
    parent_process = current_process.parent()
    
    # Get the parent process ID
    parent_pid = parent_process.pid

    # Use EnumWindows to find the window with the matching process ID
    hwnd_list = []

    def enum_windows_callback(hwnd, lParam):
        # Get the process ID of the window
        process_id = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value == parent_pid:
            hwnd_list.append(hwnd)
        return True

    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    EnumWindows(EnumWindowsProc(enum_windows_callback), 0)

    return hwnd_list[0] if hwnd_list else None

if __name__ == "__main__":
    hwnd = get_parent_window_handle()
    if hwnd:
        print(f"Handle of the parent window: {hwnd}")
    else:
        print("Could not find the parent window handle.")
