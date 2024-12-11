# ctraceback

Custom traceback

## Installing

Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):

$ pip install ctraceback

ctraceback supports Python 3 and newer.

## Example

```python
from ctraceback import CTraceback
sys.excepthook = CTraceback
...
try:
  ...
except:
  CTraceback(*sys.exc_info())
...
```

you can run ctraceback server to receive all traceback messages:
```bash
$ ctraceback serve
# use -h for help
```

default port is 7000 and can be change in config file `traceback.ini`

## Links

- License: [GPL](https://github.com/cumulus13/ctraceback/blob/master/LICENSE.rst)
- Code: [https://github.com/cumulus13/ctraceback](https://github.com/cumulus13/ctraceback)
- Issue tracker: [https://github.com/cumulus13/ctraceback/issues](https://github.com/cumulus13/ctraceback/issues)

## Author
[Hadi Cahyadi](mailto:cumulus13@gmail.com)

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)
[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)
 [Support me on Patreon](https://www.patreon.com/cumulus13)
