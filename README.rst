EditorConfig Tools
==================

.. image:: https://secure.travis-ci.org/treyhunner/editorconfig-tools.png?branch=master
   :target: http://travis-ci.org/treyhunner/editorconfig-tools
.. image:: https://coveralls.io/repos/treyhunner/editorconfig-tools/badge.png?branch=master
   :target: https://coveralls.io/r/treyhunner/editorconfig-tools

Goals of this project
---------------------

* Create tool to infer format for ``.editorconfig`` file from current code
* Create tool to validate current code from existing ``.editorconfig`` files
* Create tool to fix style errors in code from existing ``.editorconfig`` files

Examples
--------

Here is an example of the command-line API we want to support::

    $ cat .editorconfig
    [*]
    indent_style = space
    indent_size = 4

    $ check_editorconfig *
    Makefile: Tab indentation found

    $ infer_editorconfig *
    [*]
    indent_style = space
    indent_size = 4
    end_of_line = lf
    charset = utf-8
    insert_final_newline = true
    trim_trailing_whitespace = true

    [Makefile]
    indent_style = tab
    indent_size = N/A

    $ fix_editorconfig *
    Makefile: Converted tabs to spaces

    $ check_editorconfig *

    $ guess_editorconfig *
    [*]
    indent_style = space
    indent_size = 4
    end_of_line = lf
    charset = utf-8
    insert_final_newline = true
    trim_trailing_whitespace = true


Project Status
--------------

This project is not yet completed.  Feel free to play with the existing code,
but don't expect it to work well (or at all) yet.
