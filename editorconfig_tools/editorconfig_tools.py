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
    newlines = dict(zip(line_endings.values(), line_endings.keys()))


class EditorConfigChecker(EditorConfigToolObject):

    """Allows checking file validity based on given EditorConfig"""

    def __init__(self, fix=False):
        self.auto_fix = fix
        self.errors = Set()

    def check_indentation(self, line, indent_style):
        """Return error string iff incorrect characters found in indentation"""
        if indent_style == 'space' and '\t' in line:
            self.errors.add("Tab indentation found")
        elif indent_style == 'tab' and re.search('^\s* \s*', line):
            self.errors.add("Space indentation found")
        return line

    def check_charset(self, line, charset):
        """Return error string iff incorrect BOM found for expected charset"""
        found_charset = None
        if charset in ('utf-8', 'latin1'):
            charset = None
        for bom, given_charset in self.byte_order_marks.items():
            if line.startswith(bom):
                found_charset = given_charset
        if found_charset != charset:
            if not found_charset:
                found_charset = "utf-8 or latin1"
            self.errors.add("Charset %s found" % found_charset)
        return line

    def check_final_newline(self, line, insert_final_newline):
        """Return given final line with newline added/removed if necessary"""
        if not line:
            return line
        has_final_newline = line[-1:] in ('\r', '\n')
        if (insert_final_newline in ('true', 'false') and
            insert_final_newline != str(has_final_newline).lower()):
            if has_final_newline:
                self.errors.add("Final newline found")
            else:
                self.errors.add("No final newline found")
        if self.auto_fix:
            if insert_final_newline == 'true':
                return re.sub(r'\r?\n?$', r'\n', line)
            elif insert_final_newline == 'false':
                return re.sub(r'\r?\n?$', '', line)
        return line

    def check_trailing_whitespace(self, line, trim_trailing_whitespace):
        """Return line with whitespace trimmed if necessary"""
        if trim_trailing_whitespace == 'true':
            new_line = re.sub(r'[ \t]*(\r?\n?)$', r'\1', line)
            if new_line != line:
                self.errors.add("Trailing whitespace found")
            if self.auto_fix:
                line = new_line
        return line

    def check(self, filename, properties):

        """Return error string list if file format doesn't match properties"""

        # Error list, current line, correctly indented line count, line number
        lines = []
        line = None
        correctly_indented = 0
        lineno = 0

        def handle_line(function, property_name):
            """Add to error list if current line error for given function"""
            if property_name in properties:
                return function(line, properties[property_name])
            else:
                return line

        with open(filename, 'Ur+' if self.auto_fix else 'Ur') as f:
            # Loop over file lines and append each error found to error list
            if properties.get('end_of_line') in self.line_endings:
                end_of_line = properties['end_of_line']
                newline = self.line_endings[end_of_line]
            else:
                end_of_line = None
                newline = None
            for lineno, line in enumerate(f):
                if end_of_line is None and f.newlines:
                    newline = f.newlines[0]
                if lineno == 0:
                    handle_line(self.check_charset, 'charset')
                line = handle_line(self.check_trailing_whitespace,
                           'trim_trailing_whitespace')
                if ('indent_style' in properties and
                    'tab_width' in properties and
                    properties['indent_size'] == properties['tab_width']):
                    line = handle_line(self.check_indentation, 'indent_style')
                if properties.get('indent_style') == 'space':
                    spaces = len(re.search('^ *', line).group(0))
                    if (spaces <= 1 or
                        spaces % int(properties['indent_size']) == 0):
                        correctly_indented += 1
                else:
                    correctly_indented += 1
                if self.auto_fix and newline:
                    line = line.replace('\n', newline)
                    lines.append(line)
            if type(f.newlines) is tuple and end_of_line:
                self.errors.add("Mixed line endings found: %s" %
                                ','.join(self.newlines[n] for n in f.newlines))
            elif (end_of_line is not None and f.newlines is not None and
                  newline != f.newlines):
                self.errors.add("Incorrect line ending found: %s" %
                                self.newlines.get(f.newlines))
            if lineno and float(correctly_indented) / lineno < 0.05:
                self.errors.add("Over 5% of lines appear to be incorrectly indented")
            line = handle_line(self.check_final_newline,
                               'insert_final_newline')
            if self.auto_fix and line is not None:
                if newline:
                    line = line.replace('\n', newline)
                lines[-1] = line
            if self.auto_fix:
                f.seek(0)
                f.writelines(lines)
                f.truncate()
        errors = list(self.errors)
        self.errors.clear()
        return errors
