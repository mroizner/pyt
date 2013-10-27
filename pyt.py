#!/usr/bin/python
import argparse
import sys
import re


def process(input_stream, output_stream, transformer, strip_lines=True):
    prev_stdout = sys.stdout
    sys.stdout = output_stream
    try:
        transformer.begin()
        transform = transformer.transform   # To avoid numerous lookups
        for line in input_stream:
            if strip_lines:
                line = line.rstrip('\n')
            transform(line)
        transformer.end()
    finally:
        sys.stdout = prev_stdout


class CommandLineTransformer(object):
    def __init__(self, transform_arg, begin_arg, end_arg, extended=False):
        _globals = {}
        _locals = {}

        _transform_code = _compile_arg(transform_arg, extended)
        assert _transform_code is not None

        def transform(line):
            _locals['line'] = line
            exec _transform_code in _globals, _locals

        self.transform = transform

        self.begin = _pass
        _begin_code = _compile_arg(begin_arg, extended)
        if _begin_code is not None:
            def begin():
                exec _begin_code in _globals, _locals

            self.begin = begin

        self.end = _pass
        _end_code = _compile_arg(end_arg, extended)
        if _end_code is not None:
            def end():
                exec _end_code in _globals, _locals

            self.end = end


class FileTransformer(object):
    def __init__(self, filename):
        self._filename = filename
        self.transform = lambda line: _no_transform_error(filename)
        self.end = _pass

    def begin(self):
        globals_ = {}
        execfile(self._filename, globals_)
        if 'begin' in globals_:
            begin_func = globals_['begin']
            begin_func()
        if 'transform' in globals_:
            self.transform = globals_['transform']
        if 'end' in globals_:
            self.end = globals_['end']


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


def _pass():
    pass


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