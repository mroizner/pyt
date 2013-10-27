#!/usr/bin/python
import argparse
import sys
import re


def process(input_stream, output_stream, transform, begin=None, end=None, strip_lines=True):
    prev_stdout = sys.stdout
    sys.stdout = output_stream
    try:
        if begin is not None:
            begin()
        for line in input_stream:
            if strip_lines:
                line = line.rstrip('\n')
            transform(line)
        if end is not None:
            end()
    finally:
        sys.stdout = prev_stdout


def get_command_line_funcs(transform_arg, begin_arg, end_arg, extended=False):
    globals_ = {}
    locals_ = {}

    transform_code = compile_arg(transform_arg, extended)

    def transform(line):
        locals_['line'] = line
        exec transform_code in globals_, locals_

    begin = None
    if begin_arg is not None:
        begin_code = compile_arg(begin_arg, extended)

        def begin():
            exec begin_code in globals_, locals_

    end = None
    if end_arg is not None:
        end_code = compile_arg(end_arg, extended)

        def end():
            exec end_code in globals_, locals_

    return transform, begin, end


def compile_arg(arg, extended=False):
    if not extended:
        return compile(arg, '<command-line>', 'single')
    else:
        return compile(normalize_extended(arg), '<command-line>', 'exec')


def normalize_extended(arg):
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


def get_file_funcs(filename, postpone_import=False):
    globals_ = {}

    if not postpone_import:
        execfile(filename, globals_)
        try:
            transform = globals_['transform']
        except KeyError:
            raise _no_transform_error(filename)
        begin = globals_.get('begin')
        end = globals_.get('end')
    else:
        def transform(line):
            try:
                func = globals_['transform']
            except KeyError:
                raise _no_transform_error(filename)
            func(line)

        def begin():
            execfile(filename, globals_)
            if 'begin' in globals_:
                globals_['begin']()

        def end():
            if 'end' in globals_:
                globals_['end']()

    return transform, begin, end


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
    parser.add_argument('--postpone', '-P', action='store_true', default=False,
                        help='Postpone executing file ("-f" must be specified)')
    args = parser.parse_args()

    if args.file:
        if args.begin is not None or args.end is not None or args.extended:
            parser.error('Options "--begin", "--end", "--extended" cannot be specified when reading commands from file')
        transform, begin, end = get_file_funcs(args.transform, args.postpone)
    else:
        transform, begin, end = get_command_line_funcs(args.transform, args.begin, args.end, args.extended)
    process(args.input, args.output, transform, begin, end, args.strip)


if __name__ == '__main__':
    main()