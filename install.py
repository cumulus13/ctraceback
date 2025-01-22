import shutil
from pathlib import Path
import os
from ctraceback.custom_traceback import console

def copy(src, dst, *, follow_symlinks=True):
    console.print(f"[bold #FFFF00]{src}[/] [bold #FFAAFF]-->[/] [bold #00FFFF]{dst}[/]")
  return shutil.copy(src, dst, *, follow_symlinks)  

def install():
    copy(r'__version__.py', r'setup\ctraceback')
    copy(r'__version__.py', r'setup\ctraceback\ctraceback')
    copy(r'custom_traceback.py', r'setup\ctraceback\ctraceback')
    copy(r'config.py', r'setup\ctraceback\ctraceback')
    copy(r'server.py', r'setup\ctraceback\ctraceback')
    copy(r'on_top.py', r'setup\ctraceback\ctraceback')
    copy(r'text.py', r'setup\ctraceback\ctraceback')
    copy(r'traceback.ini', r'setup\ctraceback\ctraceback')
    copy(r'traceback.json', r'setup\ctraceback\ctraceback')
    if not Path(r'setup\ctraceback\ctraceback\handler').is_dir():
        os.makedirs(r'setup\ctraceback\ctraceback\handler')
    copy(r'handler\rabbitmq.py', r'setup\ctraceback\ctraceback\handler')
    
if __name__ == '__main__':
    install()