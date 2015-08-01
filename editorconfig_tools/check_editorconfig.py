#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import sys
from clint import arguments
from clint.textui import puts, colored, indent
from os.path import abspath

from .editorconfig_tools import EditorConfigChecker
from editorconfig import get_properties, EditorConfigError


COMMANDS = [
    ('--fix', "Fix EditorConfig file automatically."),
    ('--help', "Print this help message."),
]
FLAGS = [flag for (flag, desc) in COMMANDS]


def usage():
    puts('Usage: {0}\n'.format(
        colored.green('check_editorconfig [args] <file...>')))
    puts('Arguments:')
    for flag, description in COMMANDS:
        with indent(2):
            puts('{0:20} {1}'.format(str(colored.blue(flag)), description))


def main():
    args = arguments.Args()
    invalid_files = args.not_flags.not_files.all
    if any(f for f in args.flags.all if f not in FLAGS):
        usage()
        sys.exit(1)
    if args.contains(('-h', '--help')):
        usage()
        sys.exit()
    if invalid_files:
        print("Invalid files found")  # TODO
        sys.exit(1)
    fix = args.contains(('-f', '--fix'))

    for filename in args.files:
        checker = EditorConfigChecker(fix=fix)
        try:
            props = get_properties(abspath(filename))
        except EditorConfigError as e:
            print(e)
            continue
        else:
            for error in checker.check(filename, props):
                print("%s: %s" % (filename, error))


if __name__ == '__main__':
    main()
