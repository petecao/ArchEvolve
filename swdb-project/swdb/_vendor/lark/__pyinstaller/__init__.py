# SPDX-License-Identifier: MIT
# Vendored from Lark 1.3.1 on 2026-10-03; import namespace adapted.
# For usage of lark with PyInstaller. See https://pyinstaller-sample-hook.readthedocs.io/en/latest/index.html

import os

def get_hook_dirs():
    return [os.path.dirname(__file__)]
