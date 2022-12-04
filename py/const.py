"""
Constant types in Python.
"""

import os
import sys
import pathlib

class _const:
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        # Restart Gradioでエラーになるため仕方なくコメントアウト
        # if name in self.__dict__:
        #     raise self.ConstError("Can't rebind const (%s)" % name)
        self.__dict__[name] = value

sys.modules[__name__]=_const()

p = pathlib.Path(__file__).parts[-4:-2]
_const.JSON_DIR = os.path.join(p[0], p[1], 'json')
_const.WEBP_DIR = os.path.join(p[0], p[1], 'webp')
_const.CONFIG_FILE = os.path.join(p[0], p[1], 'config.json')
del p
