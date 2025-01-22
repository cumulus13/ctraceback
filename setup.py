import shutil
from pathlib import Path
import os, sys
from ctraceback.custom_traceback import console
import argparse

def copy(src, dst, *, follow_symlinks=True):
    console.print(f"[bold #FFFF00]{src}[/] [bold #FFAAFF]-->[/] [bold #00FFFF]{dst}[/]")
    return shutil.copy(src, dst, follow_symlinks=follow_symlinks)

def install(quite = False):  # sourcery skip: remove-redundant-fstring
    copy(r'__version__.py', r'setup\ctraceback')
    copy(r'__version__.py', r'setup\ctraceback\ctraceback')
    copy(r'custom_traceback.py', r'setup\ctraceback\ctraceback')
    copy(r'config.py', r'setup\ctraceback\ctraceback')
    copy(r'server.py', r'setup\ctraceback\ctraceback')
    copy(r'on_top.py', r'setup\ctraceback\ctraceback')
    copy(r'test.py', r'setup\ctraceback\ctraceback')
    copy(r'traceback.ini', r'setup\ctraceback\ctraceback')
    copy(r'traceback.json', r'setup\ctraceback\ctraceback')
    if not Path(r'setup\ctraceback\ctraceback\handler').is_dir():
        os.makedirs(r'setup\ctraceback\ctraceback\handler')
    copy(r'handler\rabbitmq.py', r'setup\ctraceback\ctraceback\handler')
    
    if not quite:
        console.print(f"[#00FFFF on #FF00AA]Do you want to install[/] [bold #FFFF00](run 'pip install .')[/] [warning]?[/] [critical]\[y/build]:[/] ", end = '')
        q = input()
        if q == 'y':
            if str(Path(__file__).parent / 'setup/ctraceback') not in str(Path.cwd()): os.chdir(str(Path(__file__).parent / 'setup/ctraceback'))
            os.system('pip install -U .')
        elif q == 'build':
            build()
    else:
        if str(Path(__file__).parent / 'setup/ctraceback') not in str(Path.cwd()): os.chdir(str(Path(__file__).parent / 'setup/ctraceback'))
        os.system('pip install -U .')

def build():
    if str(Path(__file__).parent / 'setup/ctraceback') not in str(Path.cwd()):
        os.chdir(str(Path(__file__).parent / 'setup/ctraceback'))
        if sys.platform == 'win32':
            os.system('rmdir /s /q build')
            os.system('rmdir /s /q dist')
            os.system('rmdir /s /q ctraceback.egg-info')
        else:
            os.system('rm -rf build dist ctraceback.egg-info')

        os.system('python setup.py build sdist bdist_wheel')
        for i in os.listdir('dist'):
            console.print(f'[bold #FFAAFF]-->[/] [bold #00FFFF]{i}[/] [bold #FFFF00]({os.path.realpath(i)})[/]')
        
def usage():  # sourcery skip: merge-duplicate-blocks, remove-redundant-if
    parser = argparse.ArgumentParser()
    parser.add_argument('COMMAND', help = 'valid: "build", "install"')
    if len(sys.argv) == 1:
        _extracted_from_usage_5(parser)
    else:
        args = parser.parse_args()
        if args.COMMAND == 'install':
            install()
        elif args.COMMAND == 'build':
            build()
        else:
            _extracted_from_usage_5(parser)

# TODO Rename this here and in `usage`
def _extracted_from_usage_5(parser):
    parser.print_help()
    print("\n")
    install()

if __name__ == '__main__':
    usage()