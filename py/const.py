"""
Constant types in Python.
"""

import os
import sys

class _const:
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        # Restart Gradioでエラーになるため仕方なくコメントアウト
        # if name in self.__dict__:
        #     raise self.ConstError("Can't rebind const (%s)" % name)
        self.__dict__[name] = value

sys.modules[__name__]=_const()
