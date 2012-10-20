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

VERBOSE = 0

help = \
"""Usage : %s [ --separate ] [ --vim-output ] [ --verbose ] file1 file2 ... fileN

Display indentation used in the list of files. Possible answers are (with X
being the number of spaces used for indentation):
space X
tab 8

--separate: analyse each file separately and report results as:
file1: space X
file2: tab 8

--vim-output: output suitable to use inside vim:
set sts=0 | set tabstop=4 | set noexpandtab | set shiftwidth=4

"""

### used when it can not compute the exact value of the indentation
default = ("space", 4)

### Used when indentation is tab, to set tabstop
vim_preferred_tabstop_value = 4


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

    def __init__(self):
        self.clear()

    def parse_file_list(self, file_list):
        for fname in file_list:
            self.parse_file(fname)

    def parse_file(self, fname):
        f = open(fname)
        l = f.readline()
        while(l):
            self.analyse_line(l)
            l = f.readline()
        f.close()

    def clear(self):
        self.spaces = [0, 0, 0, 0, 0, 0, 0]  # 2-8 entries
        self.tab = 0
        self.last_space_indent = 0
        self.nb_lines = 0
        self.nb_skipped_lines = 0
        self.indent_re = re.compile(r"^((\s)\2*)\S")
        self.skip_line = 0

    def analyse_line(self, line):
        self.nb_lines += 1
        skip_line = self.skip_line
        if len(line) > 2 and line[-2] == "\\":
            self.skip_line = 1
        else:
            self.skip_line = 0
        if skip_line:
            self.nb_skipped_lines += 1
            return

        mo = self.indent_re.match(line)
        if mo:
            if mo.group(2) == '\t':
                self.tab += 1
                self.last_space_indent = 0
                return
            nb_space = len(mo.group(1))
            for i in range(2, 9):
                if (nb_space % i) == 0:
                    self.spaces[i - 2] += 1
                if self.last_space_indent and (nb_space - self.last_space_indent) == i:
                    # bonus when we detect that a new indentation level was reached
                    self.spaces[i - 2] += 10
            self.last_space_indent = nb_space
            return
        else:
            self.nb_skipped_lines += 1

    def results(self):
        if VERBOSE:
            print "Nb of scanned lines : %d" % self.nb_lines
            print "Nb of ignored lines : %d" % self.nb_skipped_lines
            print "Nb of lines with tab indentation: %d" % self.tab
            for i in range(2, 9):
                print "Nb of points for space %d indentation: %d" % (i, self.spaces[i - 2])

        if self.tab > max(self.spaces):
            if VERBOSE:
                print "Result = tab"
            return ("tab", 8)

        nb = 0
        idx = -1
        for i in range(8, 1, -1):
            if self.spaces[i - 2] > int(nb * 1.1):  # give a 10% threshold
                idx = i
                nb = self.spaces[idx - 2]

        if idx == -1:  # no lines
            raise Exception("<Empty file>")

        if VERBOSE:
            print "Result = space, %d" % idx
        return ("space", idx)

    def __str__(self):
        try:
            return "%s %d" % self.results()
        except Exception:
            return "<Empty file>"

    def vim_output(self):
        try:
            ts, n = self.results()
        except Exception:
            return '" Empty file'
        # spaces:
        #     => set sts to the number of spaces
        #   => set tabstop to the number of spaces
        #   => expand tabs to spaces
        #   => set shiftwidth to the number of spaces
        if ts == "space":
            return "set sts=%d | set tabstop=%d | set expandtab | set shiftwidth=%d" % (n, n, n)

        tab_width = 4
        # tab:
        #   => set sts to 0
        #   => set tabstop to preferred value
        #   => set expandtab to false
        #   => set shiftwidth to tabstop
        #   tabstop should not be touched.
        if ts == "tab":
            return "set sts=0 | set tabstop=%d | set noexpandtab | set shiftwidth=%d" % (vim_preferred_tabstop_value, tab_width)


def main():
    global VERBOSE

    SEPARATE = 0
    VIM_OUTPUT = 0
    VERBOSE = 0

    fi = IndentFinder()
    file_list = []
    for opt in sys.argv[1:]:
        if opt == "--separate":
            SEPARATE = 1
        elif opt == "--vim-output":
            VIM_OUTPUT = 1
        elif opt == "--verbose":
            VERBOSE = 1
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
    if VIM_OUTPUT:
        print fi.vim_output()
    else:
        print str(fi)


if __name__ == "__main__":
    main()
