#!/usr/bin/env python
import sys
from os.path import abspath

from editorconfig_tools import EditorConfigChecker
from editorconfig import get_properties, EditorConfigError


def main(*args):
    for filename in args:
        checker = EditorConfigChecker(fix=True)
        try:
            props = get_properties(abspath(filename))
        except EditorConfigError, e:
            print e
            continue
        else:
            checker.check(filename, props)


if __name__ == '__main__':
    main(*sys.argv)