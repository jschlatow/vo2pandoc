#!/usr/bin/env python
#
# vo2pandoc.py
# 
# convert vim outliner files to pandoc markdown 
#
# Copyright 2014 Johannes Schlatow

import sys
import re

todoStart = "\\todo[inline]{"
todoEnd   = "}"

def showHelp():
    # TODO add option: automatic lists
    # TODO add option: custom todo marker
    print("""
    Usage:
        vo2pandoc.py inputfile > outputfile

    This script converts the standard Vim Outliner Syntax to pandoc markdown as follow.

        Each indentation is converted into a section heading. If, however, a section does
        not contain any body text, they is converted into a (nested) list.

        Body text (:) can contain any (pandoc) markdown formatting.
        Preformated text (;) is converted into a line block in order to preserve line breaks.

        User-defined text (>) is converted into a block quote.
        Preformated user-defined text (<) is converted in a (fenced) code block.

        Tables (|) are converted into piped tables.

        Checkboxes [_] and [X] are always converted into list items. The unchecked item
        gets an additional TODO marker.
    """)

def parseArgs():
    global inputfile
    if len(sys.argv) != 2:
        showHelp()
        sys.exit()
    else:
        inputfile = sys.argv[1]

def getLevel(line):
    count = 0
    for c in line:
        if c == "\t":
            count += 1
        else:
            return count

def nextIdx(idx, lines):
    if idx < 0:
        return idx

    for i in range(idx+1, len(lines)):
        if len(lines[i].strip()) > 0:
            return i
    return -1

def makeHeader(line, level):
    return (level + 1) * '#' + line

def renderHeaders(items):
    out = []
    for [line, content] in items:
        out.append(makeHeader(line.strip(), getLevel(line)))
        out.extend(content)

    return out

def renderList(items):
    out = []
    for [line, content] in items:
        out.append("* " + line.strip())
        for c in content:
            out.append("    " + c)

    return out

def processBodyText(idx, lines):
    out = [""]
    while idx >= 0 and lines[idx].strip().startswith(':'):
        out.append(lines[idx].strip()[1:].strip())
        idx = nextIdx(idx, lines)

    out.append("")
    return [out, idx]

def processBodyPreText(idx, lines):
    out = [""]
    while idx >= 0 and lines[idx].strip().startswith(';'):
        out.append("| " + lines[idx].strip()[1:].strip())
        idx = nextIdx(idx, lines)

    out.append("")
    return [out, idx]

def processUserText(idx, lines):
    out = []
    while idx >= 0 and lines[idx].strip().startswith('>'):
        out.append(lines[idx].strip())
        idx = nextIdx(idx, lines)

    out.append("")
    return [out, idx]

def processUserPreText(idx, lines):
    out = ["~~~"]
    while idx >= 0 and lines[idx].strip().startswith('<'):
        out.append(lines[idx].strip()[1:])
        idx = nextIdx(idx, lines)

    out.append("~~~")
    return [out, idx]

def processTable(idx, lines):
    out = []
    while idx >= 0 and lines[idx].strip().startswith('|'):
        line = lines[idx].strip()
        # table header?
        if line[1] == '|':
            line = "| " + line[2:]
            out.append(line)
            out.append(re.sub('[^\|]', "-", line))
        else:
            out.append(line)

        idx = nextIdx(idx, lines)

    out.append("")
    return [out, idx]

def processSection(idx, lines, level):
    curlevel = getLevel(lines[idx])
    if curlevel > level and idx >= 0:
        out = []
        isList  = True
        firstItem = True
        makeList = False
        items = []
        while curlevel > level and idx >= 0:
            curline = lines[idx]
            start = curline.strip()[0]
            if start == ':':
                isList = False
                if not firstItem:
                    if makeList:
                        out.extend(renderList(items))
                    else:
                        out.extend(renderHeaders(renderList(items)))
                    firstItem = True

                [textout, nidx] = processBodyText(idx, lines)
                out.extend(textout)
            elif start == ';':
                isList = False
                if not firstItem:
                    if makeList:
                        out.extend(renderList(items))
                    else:
                        out.extend(renderHeaders(renderList(items)))
                    firstItem = True

                [textout, nidx] = processBodyPreText(idx, lines)
                out.extend(textout)
            elif start == '>':
                isList = False
                if not firstItem:
                    if makeList:
                        out.extend(renderList(items))
                    else:
                        out.extend(renderHeaders(renderList(items)))
                    firstItem = True

                [textout, nidx] = processUserText(idx, lines)
                out.extend(textout)
            elif start == '<':
                isList = False
                if not firstItem:
                    if makeList:
                        out.extend(renderList(items))
                    else:
                        out.extend(renderHeaders(renderList(items)))
                    firstItem = True

                [textout, nidx] = processUserPreText(idx, lines)
                out.extend(textout)
            elif start == '|':
                isList = False
                if not firstItem:
                    if makeList:
                        out.extend(renderList(items))
                    else:
                        out.extend(renderHeaders(renderList(items)))
                    firstItem = True

                [textout, nidx] = processTable(idx, lines)
                out.extend(textout)
            elif start == '[':
                # TODO implement checkbox parsing (i.e. modify curline and force list generation)
                print("Error: Checkboxes not implemented")
                sys.exit()
            else:
                [secout, nidx, isListItem] = processSection(nextIdx(idx, lines), lines, curlevel)
                if firstItem:
                    items = []
                    firstItem = False
                    makeList = isListItem
                elif not isListItem:
                    isList = False
                    makeList = False

                items.append([curline, secout])

            curlevel = getLevel(lines[nidx])
            idx = nidx

        if not firstItem:
            if makeList:
                out.extend(renderList(items))
            else:
                out.extend(renderHeaders(items))

        return [out, idx, isList]

    else:
        # section is empty
        return [[""], idx, True]

def main():
    parseArgs()
    file = open(inputfile, "r")
    lines = file.readlines()
    file.close()

    [out, idx, isList] = processSection(0, lines, -1)

    for line in out:
        print(line)


if __name__ == "__main__":
    main()
