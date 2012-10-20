#
# Indentation finder, by Philippe Fremy <pfremy@freehackers.org>
#
# Copyright 2002,2005 Philippe Fremy
# Version: 1.1
#
# This program is distributed under the BSD license. You should have received
# a copy of the file LICENSE.txt along with this software.
#
# $Id: indent_finder.py,v 1.2 2002/12/01 17:36:06 philippe Exp $
#
# History:
# ========
#
# version 1.1:
# - improve the heuristic by detecting indentation steps
#
# version 1.0:
# - initial release

import sys
import re

help = \
"""Usage : %s [ --separate ] [ --verbose ] file1 file2 ... fileN

Display indentation used in the list of files. Possible answers are (with X
being the number of spaces used for indentation):
space X
tab 8

--separate: analyse each file separately and report results as:
file1: space X
file2: tab 8

"""

### used when it can not compute the exact value of the indentation
default = ("space", 4)


class IndentFinder:
    """
    IndentFinder reports the indentation used in a source file. Its approach is
    not tied to any particular language. It was tested successfully
    with python, C, C++ and Java code.

    How does it work ?

    It scans each line of the entry file for a space character (white space or
    tab) repeated until a non space character is found. Such a line
    is considered to be a properly indented line of code. Blank lines and
    mixed indentation line are safely ignored. Lines coming after a line
    ending in '\\' have higher chance of being not properly indented, and are
    thus ignored too.

    An array stores the number of lines that have a specific indentation: tab,
    number of spaces between 2 and 8. For space indentation, a line is
    considered indented with a base of x if the number of spaces modulo x
    yields zero. Thus, an indentation of 4 spaces increases the 2-spaces and
    the 4-spaces indentation line count.

    To improve the heuristics, the steps of increments in the indentation
    give an extra bonus of 10 points. For example:
    <4 space>some line
    <8 space     >some line
    is a strong hint of an indentation of 4 and gets 4 an 10 points bonus

    At the end of the scan phase, the indentation that was used with the
    highest number of lines is taken. For spaces, to avoid the problemes of
    multiples like 2 and 4, the highest indentation number is preferred. A
    lower number is chosen if it reports at least 10% more lines with this
    indentation.

    If IndentFinder ever reports wrong indentation, send me immediately a
    mail, if possible with the offending file.
    """

    INDENT_RE = re.compile(r"^((\s)\2*)\S")

    def __init__(self):
        self.clear()

    def parse_file_list(self, file_list):
        for fname in file_list:
            self.parse_file(fname)

    def parse_file(self, fname):
        with open(fname) as f:
            for line in f:
                self.analyse_line(line)

    def clear(self):
        self.spaces = [0, 0, 0, 0, 0, 0, 0]  # 2-8 entries
        self.tabbed_lines = 0
        self.last_space_indent = 0
        self.total_lines = 0
        self.skipped_lines = 0
        self.skip_line = 0

    def analyse_line(self, line):
        self.total_lines += 1
        skip_this_line = self.skip_line
        self.skip_line = (len(line) > 2 and line[-2] == "\\")
        if skip_this_line:
            self.skipped_lines += 1
            return

        match = self.INDENT_RE.match(line)
        if match:
            if match.group(2) == '\t':
                self.tabbed_lines += 1
                self.last_space_indent = 0
                return
            num_spaces = len(match.group(1))
            for i in range(2, 9):
                if (num_spaces % i) == 0:
                    self.spaces[i - 2] += 1
                if (self.last_space_indent and
                    num_spaces - self.last_space_indent == i):
                    # bonus when we detect that a new indentation level was reached
                    self.spaces[i - 2] += 10
            self.last_space_indent = num_spaces
        else:
            self.skipped_lines += 1

    def results(self):
        if self.tabbed_lines > max(self.spaces):
            return ("tab", 8)

        num_lines = 0
        indent_size = -1
        for i in range(8, 1, -1):
            if self.spaces[i - 2] > int(num_lines * 1.1):  # give a 10% threshold
                indent_size = i
                num_lines = self.spaces[indent_size - 2]

        if indent_size == -1:  # no indentation
            return (None, None)

        return ("space", indent_size)

    def __str__(self):
        indent_style, indent_size = self.results()
        if indent_style == 'space':
            return "space %d" % indent_size
        elif indent_style == 'tab':
            return "tab"
        else:
            return "<Empty file>"


def main():

    SEPARATE = 0

    fi = IndentFinder()
    file_list = []
    for opt in sys.argv[1:]:
        if opt == "--separate":
            SEPARATE = 1
        elif opt[0] == "-":
            print help % sys.argv[0]
            return
        else:
            file_list.append(opt)

    if SEPARATE:
        for fname in file_list:
            fi.clear()
            fi.parse_file(fname)
            print "%s : %s" % (fname, str(fi))
        return

    fi.parse_file_list(file_list)
    print str(fi)


if __name__ == "__main__":
    main()
