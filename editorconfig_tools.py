import re
from sets import Set


class EditorConfigToolObject(object):

    """Base class for EditorConfig tools"""

    byte_order_marks = {
        '\xef\xbb\xbf': 'utf-8-bom',
        '\xfe\xff': 'utf-16be',
        '\xff\xfe': 'utf-16le',
        '\x00\x00\xfe\xff': 'utf-32be',
        '\xff\xfe\x00\x00': 'utf-32le',
    }

    line_endings = {
        'crlf': '\r\n',
        'lf': '\n',
        'cr': '\r',
    }


class EditorConfigChecker(EditorConfigToolObject):

    """Allows checking file validity based on given EditorConfig"""

    def check_indentation(self, line, indent_style):
        """Return error string iff incorrect characters found in indentation"""
        if indent_style == 'space' and '\t' in line:
            return "Tab indentation found"
        elif indent_style == 'tab' and re.search('^\s* \s* ', line):
            return "Space indentation found"

    def check_charset(self, first_line, charset):
        """Return error string iff incorrect BOM found for expected charset"""
        found_charset = None
        if charset in ('utf-8', 'latin1'):
            charset = None
        for bom, given_charset in self.byte_order_marks.items():
            if first_line.startswith(bom):
                found_charset = given_charset
        if found_charset != charset:
            if not found_charset:
                found_charset = "utf-8 or latin1"
            return "Charset %s found" % found_charset

    def check_line_endings(self, line, end_of_line):
        """Return error string iff incorrect end of line format found"""
        if end_of_line not in self.line_endings.keys():
            return
        found_end_of_line = None
        for eol_format in ('crlf', 'lf', 'cr'):
            if line.endswith(self.line_endings[eol_format]):
                found_end_of_line = eol_format
                break
        if found_end_of_line and end_of_line != found_end_of_line:
            return "%s line ending found" % found_end_of_line

    def check_final_newline(self, last_line, insert_final_newline):
        """Return error string iff unexpected final newline presence/absense"""
        if insert_final_newline not in ('true', 'false'):
            return
        final_newline = last_line[-1:] in ('\r', '\n')
        if insert_final_newline != str(final_newline).lower():
            if final_newline:
                return "Final newline found"
            else:
                return "No final newline found"

    def check_trailing_whitespace(self, line, trim_trailing_whitespace):
        """Return error string if trailing whitespace found when not expected"""
        if (trim_trailing_whitespace == 'true' and
            re.search('\s$', line.strip('\r\n'))):
            return "Trailing whitespace found"

    def check(self, filename, properties):

        """Return error string list if file format doesn't match properties"""

        # Error list, current line, correctly indented line count, line number
        errors = Set([])
        line = ""
        correctly_indented = 0
        lineno = 0

        def check_line(function, property_name):
            """Add to error list if current line error for given function"""
            if property_name in properties:
                error = function(line, properties[property_name])
                if error:
                    errors.add(error)

        with open(filename) as f:
            # Loop over file lines and append each error found to error list
            for lineno, line in enumerate(f):
                if lineno == 0:
                    check_line(self.check_charset, 'charset')
                check_line(self.check_line_endings, 'end_of_line')
                check_line(self.check_trailing_whitespace,
                           'trim_trailing_whitespace')
                if ('indent_style' in properties and
                    'indent_size' in properties and
                    properties['indent_size'] == properties['tab_width']):
                    check_line(self.check_indentation, 'indent_style')
                if properties.get('indent_style') == 'space':
                    spaces = len(re.search('^ *', line).group(0))
                    if (spaces <= 1 or
                        spaces % int(properties['indent_size']) == 0):
                        correctly_indented += 1
                else:
                    correctly_indented += 1
            if lineno and float(correctly_indented) / lineno < 0.05:
                errors.add("Over 5% of lines appear to be incorrectly indented")
            if lineno > 0:
                check_line(self.check_final_newline, 'insert_final_newline')

        return list(errors)


class EditorConfigFixer(EditorConfigToolObject):

    """Allows fixing files based on EditorConfig given properties"""

    def fix_line_endings(self, line, end_of_line):
        """Return line fixed (if necessary) for correct end of line"""
        if end_of_line in self.line_endings.keys():
            return line.strip('\r\n') + self.line_endings[end_of_line]
        else:
            return line

    def fix_trailing_whitespace(self, line, trim_trailing_whitespace):
        """Return line with whitespace trimmed if necessary"""
        if trim_trailing_whitespace == 'true':
            return re.sub(r'[ \t]*(\r?\n?)$', r'\1', line)
        else:
            return line

    def fix_final_newline(self, line, insert_final_newline):
        """Return given final line with newline added/removed if necessary"""
        if insert_final_newline == 'true':
            return re.sub(r'\r?\n?$', r'\n', line)
        elif insert_final_newline == 'false':
            return re.sub(r'\r?\n?$', '', line)

    def fix(self, filename, properties):

        """Attempt to discovered file style errors based on given propreties"""

        # List of all lines in file (fixed based on properties) and current line
        lines = []
        line = None

        def fix_line(function, property_name):
            if property_name in properties:
                return function(line, properties[property_name])

        end_of_line = self.line_endings.get(properties.get('end_of_line'), '\n')
        with open(filename, 'r+') as f:
            for line in f:
                line = fix_line(self.fix_line_endings, 'end_of_line')
                line = fix_line(self.fix_trailing_whitespace,
                         'trim_trailing_whitespace')
                if line[-1:] in ('\r', '\n'):
                    end_of_line = re.search('\r?\n?$', line).group(0)
                lines.append(line)
            if line is not None:
                line = fix_line(self.fix_final_newline, 'insert_final_newline')
                line.replace('\n', end_of_line)
                lines[-1] = line
            f.seek(0)
            f.writelines(lines)
            f.truncate()
