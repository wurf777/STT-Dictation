import os
import sys

_tcl_dir = os.path.join(sys._MEIPASS, "tcl")
if os.path.isdir(_tcl_dir) and "TCL_LIBRARY" not in os.environ:
    os.environ["TCL_LIBRARY"] = os.path.join(_tcl_dir, "tcl8.6")
    os.environ["TK_LIBRARY"] = os.path.join(_tcl_dir, "tk8.6")
