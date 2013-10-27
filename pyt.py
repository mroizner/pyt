#!/usr/bin/python
import argparse
import sys
import re


def process(input_stream, output_stream, transformer, strip_lines=True):
    prev_stdout = sys.stdout
    sys.stdout = output_stream
    try:
        transformer.begin()
        for line in input_stream:
            if strip_lines:
                line = line.rstrip('\n')
            transformer.transform(line)
        transformer.end()
    finally:
        sys.stdout = prev_stdout


class CommandLineTransformer(object):
    def __init__(self, transform_arg, begin_arg, end_arg, extended=False):
        self._globals = {}
        self._locals = {}
        self._transform_code = _compile_arg(transform_arg, extended)
        assert self._transform_code is not None
        self._begin_code = _compile_arg(begin_arg, extended)
        self._end_code = _compile_arg(end_arg, extended)

    def begin(self):
        if self._begin_code is not None:
            exec self._begin_code in self._globals, self._locals

    def transform(self, line):
        self._locals['line'] = line
        exec self._transform_code in self._globals, self._locals

    def end(self):
        if self._end_code is not None:
            exec self._end_code in self._globals, self._locals


class FileTransformer(object):
    def __init__(self, filename):
        self.filename = filename

    def begin(self):
        globals_ = {}
        execfile(self.filename, globals_)
        if 'begin' in globals_:
            begin_func = globals_['begin']
            begin_func()
        if 'transform' in globals_:
            setattr(self, 'transform', globals_['transform'])
        if 'end' in globals_:
            setattr(self, 'end', globals_['end'])

    def transform(self, line):
        raise _no_transform_error(self.filename)

    def end(self):
        pass


def _compile_arg(arg, extended=False):
    if arg is None:
        return None
    if not extended:
        return compile(arg, '<command-line>', 'single')
    else:
        return compile(_normalize_extended(arg), '<command-line>', 'exec')


def _normalize_extended(arg):
    result = ''
    tail = arg
    regexp = re.compile(r'\s*\$(\\*)\^\s*')
    while tail:
        match = regexp.search(tail)
        if match is None:
            result += tail
            tail = ''
        else:
            result += tail[:match.start()] + '\n' + len(match.group(1)) * '\t'
            tail = tail[match.end():]
    return result


def _no_transform_error(filename):
    return RuntimeError('The module "{0}" does not define function with name "transform"'.format(filename))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('transform',
                        help='Transformation command (or name of file with commands when "-f" specified)')
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input file')
    parser.add_argument('output', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output file')
    parser.add_argument('--begin', '-b', default=None,
                        help='Transformation begin command')
    parser.add_argument('--end', '-e', default=None,
                        help='Transformation end command')
    parser.add_argument('--nostrip', '-S', dest='strip', action='store_false', default=True,
                        help='Do not strip "\\n" at end of lines')
    parser.add_argument('--extended', '-E', action='store_true', default=False,
                        help='Use multi-line commands '
                             '("$\\\\\\^" for line-break and indents - each "\\" stands for one indent)')
    parser.add_argument('--file', '-f', action='store_true', default=False,
                        help='Read commands from file '
                             '(a file must be a valid Python module with defined function "transform")')
    args = parser.parse_args()

    if args.file:
        if args.begin is not None or args.end is not None or args.extended:
            parser.error('Options "--begin", "--end", "--extended" cannot be specified when reading commands from file')
        transformer = FileTransformer(args.transform)
    else:
        transformer = CommandLineTransformer(args.transform, args.begin, args.end, args.extended)
    process(args.input, args.output, transformer, args.strip)


if __name__ == '__main__':
    main()