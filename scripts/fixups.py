#!/usr/bin/python
# vim: ts=4 :
# vim: sw=4 :

#Contains various functions for fixing spice files
#replaces the old replace_string.py and fix_*.py


#usage: open a file with read
#chain any number of fixups in a row
#write a file with write
#example
#write('output.MOD', 
#   name_has_slash(
#       replace_string('old', 'new', 
#           read('input.MOD'))))

import re
import os

def read(filename):
    """Open a file and yield its lines"""
    f = open(str(filename), 'r')
    for line in f:
        yield line


def write(filename, gen):
    f = open(str(filename), 'w')
    for line in gen:
        f.write(line)


def trailing_newline(gen):
    # add a headline with asterisk if missing
    # add trailing newline if missing
    try:
        first_line = gen.next()
        if first_line[0] != '*':
            yield '*' + os.linesep
        yield first_line
        buf1 = gen.next()
    except StopIteration:
        raise ValueError, 'Modelfile less than 2 lines'
    while True:
        try:
            buf2 = gen.next()
            yield buf1
            buf1 = buf2
        except StopIteration:
            #buf1 contains the file's last line
            if buf1[-1] != os.linesep:
                buf1 += os.linesep
            yield buf1
            raise StopIteration


def ends_without_subcircuit(gen):
    # some models have a .ENDS statement even if there is no
    # subcircuit definition.
    # comment out the wrong .ENDS statement
    in_subckt = False
    for line in gen:
        if line[0] != '*':  #skip comment lines
            if re.match('\.subckt', line.lower()):
                in_subckt = True
            if re.match('\.ends',line.lower()):
                if not in_subckt:
                    line = '* WRONG .ENDS BUGFIX: ' + line
                in_subckt = False
        yield line

 
def name_has_slash(gen):
    #removes a slash in the subcircuit's name, if present
    SUBCKT_PAT = '^(\s*\.SUBCKT\s+)(\w+)/NS'
    for line in gen:
        match = re.search(SUBCKT_PAT, line)
        if match:
            old_name = match.group(2)
            name = old_name.split('/')[0]
            yield re.sub(SUBCKT_PAT, match.group(1) + name, line)
        else:
            yield line

def replace_string(query, repl, gen):
    #Replaces all occurences of query with repl
    #query may NOT include a newline
    for line in gen:
        line = line.replace(query, repl)
        yield line
