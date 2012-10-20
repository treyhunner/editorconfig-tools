#
# Indentation finder, by Philippe Fremy <phil at freehackers dot org>
# Copyright 2002-2008 Philippe Fremy
#
# This program is distributed under the BSD license. You should have received
# a copy of the file LICENSE.txt along with this software.
#

import sys
import re

help = \
"""Usage : %s [ --vim-output ] [ --verbose ] file1 file2 ... fileN

Display indentation used in the list of files. Possible answers are (with X
being the number of spaces used for indentation):
space X
tab 8
mixed tab X space Y

mixed means that indentation style is tab at the beginning of the line (tab
being 8 positions) and then spaces to do the indentation, unless you reach 8
spaces which are replaced by a tab. This is the vim source file indentation
for example. In my opinion, this is the worst possible style.

--vim-output: output suitable to use inside vim:
set sts=0 | set tabstop=4 | set noexpandtab | set shiftwidth=4

"""

VERSION='1.4'

### Used when indentation is tab, to set tabstop in vim
DEFAULT_TAB_WIDTH = 4

### default values for files where indentation is not meaningful (empty files)
# possible values:
# DEFAULT_RESULT = ('space', 4 )
# DEFAULT_RESULT = ('space', 2 )
# DEFAULT_RESULT = ('space', 8 )
# DEFAULT_RESULT = ('tab', DEFAULT_TAB_WIDTH )

DEFAULT_RESULT = ('space', 4 )

VERBOSE_QUIET   = 0
VERBOSE_INFO    = 1
VERBOSE_DEBUG   = 2
VERBOSE_DEEP_DEBUG   = 3

DEFAULT_VERBOSITY = VERBOSE_QUIET

###
class LineType:
    NoIndent        = 'NoIndent'
    SpaceOnly       = 'SpaceOnly'
    TabOnly         = 'TabOnly'
    Mixed           = 'Mixed'
    BeginSpace      = 'BeginSpace'

def info( s ): log( VERBOSE_INFO, s )
def dbg( s ): log( VERBOSE_DEBUG, s )
def deepdbg( s ): log( VERBOSE_DEEP_DEBUG, s )

def log( level, s ):
    if level <= IndentFinder.VERBOSITY:
        print s

class IndentFinder:
    """
    IndentFinder reports the indentation used in a source file. Its approach
    is not tied to any particular language. It was tested successfully with
    python, C, C++ and Java code.

    How does it work ?

    It scans each line of the entry file for a space character (white space or
    tab) repeated until a non space character is found. Such a line
    is considered to be a properly indented line of code. Blank lines and
    comments line (starting with # or /* or * ) are ignored. Lines coming
    after a line ending in '\\' have higher chance of being not properly
    indented, and are thus ignored too.

    Only the increment in indentation are fed in. Dedentation or maintaining
    the same indentation is not taken into account when analysing a file. Increment
    in indentation from zero indentation to some indentation is also ignored because
    it's wrong in many cases (header file with many structures for example, do not always
    obey the indentation of the rest of the code).

    Each line is analysed as:
    - SpaceOnly: indentation of more than 8 space
    - TabOnly: indentation of tab only
    - Mixed: indentation of tab, then less than 8 spaces
    - BeginSpace: indentation of less than 8 space, that could be either a mixed indentation
        or a pure space indentation.
    - non-significant

    Then two consecutive significant lines are then considered. The only valid combinations are:
    - (NoIndent, BeginSpace)    => space or mixed
    - (NoIndent, Tab)           => tab
    - (BeginSpace, BeginSpace)  => space or mixed
    - (BeginSpace, SpaceOnly)   => space
    - (SpaceOnly, SpaceOnly)    => space
    - (TabOnly, TabOnly)        => tab
    - (TabOnly, Mixed)          => mixed
    - (Mixed, TabOnly)          => mixed

    The increment in number of spaces is then recorded.

    At the end, the number of lines with space indentation, mixed space and tab indentation
    are compared and a decision is made.

    If no decision can be made, DEFAULT_RESULT is returned.

    If IndentFinder ever reports wrong indentation, send me immediately a
    mail, if possible with the offending file.
    """

    def __init__(self, default_result=DEFAULT_RESULT):
        self.clear()
        self.default_result = default_result

    VERBOSITY = DEFAULT_VERBOSITY

    def parse_file_list( self, file_list ):
        for fname in file_list:
            self.parse_file( fname )

    def parse_file( self, fname ):
        f = open( fname )
        l = f.readline()
        while( l ):
            self.analyse_line( l )
            l = f.readline()
        f.close()

    def clear( self ):
        self.lines = {}
        for i in range(2,9): self.lines['space%d' % i] = 0
        for i in range(2,9): self.lines['mixed%d' % i] = 0
        self.lines['tab'] = 0

        self.nb_processed_lines = 0
        self.nb_indent_hint = 0
        self.indent_re  = re.compile( "^([ \t]+)([^ \t]+)" )
        self.mixed_re  = re.compile(  "^(\t+)( +)$" )
        self.skip_next_line = False
        self.previous_line_info = None

    def analyse_line( self, line ):
        if line[-1:] == '\n':
            line = line[:-1]
        deepdbg( 'analyse_line: "%s"' % line.replace(' ', '.' ).replace('\t','\\t') )
        self.nb_processed_lines += 1

        skip_current_line = self.skip_next_line
        self.skip_next_line = False
        if line[-1:] == '\\':
            deepdbg( 'analyse_line: Ignoring next line!' )
            # skip lines after lines ending in \
            self.skip_next_line = True

        if skip_current_line:
            deepdbg( 'analyse_line: Ignoring current line!' )
            return

        ret = self.analyse_line_indentation( line )
        if ret:
            self.nb_indent_hint += 1
        deepdbg( 'analyse_line: Result of line analysis: %s' % str(ret) )
        return ret

    def analyse_line_type( self, line ):
        '''Analyse the type of line and return (LineType, <indentation part of
        the line>).

        The function will reject improperly formatted lines (mixture of tab
        and space for example) and comment lines.
        '''
        mixed_mode = False
        tab_part = ''
        space_part = ''

        if len(line) > 0 and line[0] != ' ' and line[0] != '\t':
            return (LineType.NoIndent, '')

        mo = self.indent_re.match( line )
        if not mo:
            deepdbg( 'analyse_line_type: line is not indented' )
            return None

        indent_part = mo.group(1)
        text_part = mo.group(2)

        deepdbg( 'analyse_line_type: indent_part="%s" text_part="%s"' %
            (indent_part.replace(' ', '.').replace('\t','\\t').replace('\n', '\\n' ),
                text_part ) )

        if text_part[0] == '*':
            # continuation of a C/C++ comment, unlikely to be indented correctly
            return None

        if text_part[0:2] == '/*' or text_part[0] == '#':
            # python, C/C++ comment, might not be indented correctly
            return None

        if '\t' in indent_part and ' ' in indent_part:
            # mixed mode
            mo = self.mixed_re.match( indent_part )
            if not mo:
                # line is not composed of '\t\t\t    ', ignore it
                return None
            mixed_mode = True
            tab_part = mo.group(1)
            space_part = mo.group(2)

        if mixed_mode:
            if len(space_part) >= 8:
                # this is not mixed mode, this is garbage !
                return None
            return (LineType.Mixed, tab_part, space_part )

        if '\t' in indent_part:
            return (LineType.TabOnly, indent_part)

        if ' ' in indent_part:
            if len(indent_part) < 8:
                # this could be mixed mode too
                return (LineType.BeginSpace, indent_part)
            else:
                # this is really a line indented with spaces
                return (LineType.SpaceOnly, indent_part )

        assert False, 'We should never get there !'

    def analyse_line_indentation( self, line ):
        previous_line_info = self.previous_line_info
        current_line_info = self.analyse_line_type( line )
        self.previous_line_info = current_line_info

        if current_line_info == None or previous_line_info == None:
            deepdbg('analyse_line_indentation: Not enough line info to analyse line: %s, %s' % (str(previous_line_info), str(current_line_info)))
            return

        t = (previous_line_info[0], current_line_info[0])
        deepdbg( 'analyse_line_indentation: Indent analysis: %s %s' % t )
        if (t == (LineType.TabOnly, LineType.TabOnly)
            or t == (LineType.NoIndent, LineType.TabOnly) ):
            if len(current_line_info[1]) - len(previous_line_info[1]) == 1 :
                self.lines['tab'] += 1
                return 'tab'

        elif (t == (LineType.SpaceOnly, LineType.SpaceOnly)
              or t == (LineType.BeginSpace, LineType.SpaceOnly)
              or t == (LineType.NoIndent, LineType.SpaceOnly) ):
            nb_space = len(current_line_info[1]) - len(previous_line_info[1])
            if 1 < nb_space <= 8:
                key = 'space%d' % nb_space
                self.lines[key] += 1
                return key

        elif (t == (LineType.BeginSpace, LineType.BeginSpace)
              or t == (LineType.NoIndent, LineType.BeginSpace) ):
            nb_space = len(current_line_info[1]) - len(previous_line_info[1])
            if 1 < nb_space <= 8:
                key1 = 'space%d' % nb_space
                key2 = 'mixed%d' % nb_space
                self.lines[ key1 ] += 1
                self.lines[ key2 ] += 1
                return key1

        elif t == (LineType.BeginSpace, LineType.TabOnly):
            # we assume that mixed indentation used 8 characters tabs
            if len(current_line_info[1]) == 1:
                # more than one tab on the line --> not mixed mode !
                nb_space = len(current_line_info[1])*8 - len(previous_line_info[1])
                if 1 < nb_space <= 8:
                    key = 'mixed%d' % nb_space
                    self.lines[ key ] += 1
                    return key

        elif t == (LineType.TabOnly, LineType.Mixed):
            tab_part, space_part = tuple(current_line_info[1:3])
            if len(previous_line_info[1]) == len(tab_part):
                nb_space = len(space_part)
                if 1 < nb_space <= 8:
                    key = 'mixed%d' % nb_space
                    self.lines[ key ] += 1
                    return key

        elif t == (LineType.Mixed, LineType.TabOnly):
            tab_part, space_part = previous_line_info[1:3]
            if len(tab_part)+1 == len(current_line_info[1]):
                nb_space = 8-len(space_part)
                if 1 < nb_space <= 8:
                    key = 'mixed%d' % nb_space
                    self.lines[ key ] += 1
                    return key
        else:
            pass

        return None

    def results( self ):
        dbg( "Nb of scanned lines : %d" % self.nb_processed_lines )
        dbg( "Nb of indent hint : %d" % self.nb_indent_hint )
        dbg( "Collected data:" )
        for key in self.lines:
            if self.lines[key] > 0:
                dbg( '%s: %d' % (key, self.lines[key] ) )

        max_line_space = max( [ self.lines['space%d'%i] for i in range(2,9) ] )
        max_line_mixed = max( [ self.lines['mixed%d'%i] for i in range(2,9) ] )
        max_line_tab = self.lines['tab']

        dbg( 'max_line_space: %d' % max_line_space )
        dbg( 'max_line_mixed: %d' % max_line_mixed )
        dbg( 'max_line_tab: %d' % max_line_tab )

        ### Result analysis
        #
        # 1. Space indented file
        #    - lines indented with less than 8 space will fill mixed and space array
        #    - lines indented with 8 space or more will fill only the space array
        #    - almost no lines indented with tab
        #
        # => more lines with space than lines with mixed
        # => more a lot more lines with space than tab
        #
        # 2. Tab indented file
        #    - most lines will be tab only
        #    - very few lines as mixed
        #    - very few lines as space only
        #
        # => a lot more lines with tab than lines with mixed
        # => a lot more lines with tab than lines with space
        #
        # 3. Mixed tab/space indented file
        #    - some lines are tab-only (lines with exactly 8 step indentation)
        #    - some lines are space only (less than 8 space)
        #    - all other lines are mixed
        #
        # If mixed is tab + 2 space indentation:
        #     - a lot more lines with mixed than with tab
        # If mixed is tab + 4 space indentation
        #     - as many lines with mixed than with tab
        #
        # If no lines exceed 8 space, there will be only lines with space
        # and tab but no lines with mixed. Impossible to detect mixed indentation
        # in this case, the file looks like it's actually indented as space only
        # and will be detected so.
        #
        # => same or more lines with mixed than lines with tab only
        # => same or more lines with mixed than lines with space only
        #


        result = None

        # Detect space indented file
        if max_line_space >= max_line_mixed and max_line_space > max_line_tab:
            nb = 0
            indent_value = None
            for i in range(8,1,-1):
                if self.lines['space%d'%i] > int( nb * 1.1 ) : # give a 10% threshold
                    indent_value = i
                    nb = self.lines[ 'space%d' % indent_value ]

            if indent_value == None: # no lines
                result = self.default_result
            else:
                result = ('space', indent_value )

        # Detect tab files
        elif max_line_tab > max_line_mixed and max_line_tab > max_line_space:
            result = ('tab', DEFAULT_TAB_WIDTH )

        # Detect mixed files
        elif max_line_mixed >= max_line_tab and max_line_mixed > max_line_space:
            nb = 0
            indent_value = None
            for i in range(8,1,-1):
                if self.lines['mixed%d'%i] > int( nb * 1.1 ) : # give a 10% threshold
                    indent_value = i
                    nb = self.lines[ 'mixed%d' % indent_value ]

            if indent_value == None: # no lines
                result = self.default_result
            else:
                result = ('mixed', (8,indent_value) )

        else:
            # not enough information to make a decision
            result = self.default_result

        info( "Result: %s" % str( result ) )
        return result

    def __str__ (self):
        itype, ival = self.results()
        if itype != 'mixed':
            return '%s %d' % (itype, ival)
        else:
            itab, ispace = ival
            return '%s tab %d space %d' % (itype, itab, ispace)


    def vim_output( self ):
        result = self.results()
        indent_type, n = result
        if indent_type == "space":
            # spaces:
            #   => set sts to the number of spaces
            #   => set tabstop to the number of spaces
            #   => expand tabs to spaces
            #   => set shiftwidth to the number of spaces
            return "set sts=%d | set tabstop=%d | set expandtab | set shiftwidth=%d \" (%s %d)" % (n,n,n,indent_type,n)

        elif indent_type == "tab":
            # tab:
            #   => set sts to 0
            #   => set tabstop to preferred value
            #   => set expandtab to false
            #   => set shiftwidth to tabstop
            return "set sts=0 | set tabstop=%d | set noexpandtab | set shiftwidth=%d \" (%s)" % (DEFAULT_TAB_WIDTH, DEFAULT_TAB_WIDTH, indent_type )

        if indent_type == 'mixed':
            tab_indent, space_indent = n
            # tab:
            #   => set sts to 0
            #   => set tabstop to tab_indent
            #   => set expandtab to false
            #   => set shiftwidth to space_indent
            return "set sts=4 | set tabstop=%d | set noexpandtab | set shiftwidth=%d \" (%s %d)" % (tab_indent, space_indent, indent_type, space_indent )



def main():
    VIM_OUTPUT = 0

    file_list = []
    for opt in sys.argv[1:]:
        if opt == "--vim-output":
            VIM_OUTPUT = 1
        elif opt == "--verbose" or opt == '-v':
            IndentFinder.VERBOSITY += 1
        elif opt == "--version":
            print 'IndentFinder v%s' % VERSION
            return
        elif opt[0] == "-":
            print help % sys.argv[0]
            return
        else:
            file_list.append( opt )

    fi = IndentFinder()

    if len(file_list) > 1:
        # multiple files
        for fname in file_list:
            fi.clear()
            fi.parse_file( fname )
            if VIM_OUTPUT:
                print "%s : %s" % (fname, fi.vim_output())
            else:
                print "%s : %s" % (fname, str(fi))
        return

    else:
        # only one file, don't print filename
        fi.parse_file_list( file_list )
        if VIM_OUTPUT:
            sys.stdout.write( fi.vim_output() )
        else:
            print str(fi)


if __name__ == "__main__":
    main()
