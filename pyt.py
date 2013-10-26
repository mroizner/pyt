#!/usr/bin/python
import argparse
import sys


def process(input_stream, transform, begin=None, end=None, strip_lines=True):
    if begin is not None:
        begin()
    for line in input_stream:
        if strip_lines:
            line = line.rstrip('\n')
        transform(line)
    if end is not None:
        end()


def get_command_line_funcs(transform_arg, begin_arg, end_arg):
    globals_ = {'print_if': print_if}
    locals_ = {}

    transform_code = compile(transform_arg, '<command-line>', 'single')

    def transform(line):
        locals_['line'] = line
        exec transform_code in globals_, locals_

    begin = None
    if begin_arg is not None:
        begin_code = compile(begin_arg, '<command-line>', 'single')

        def begin():
            exec begin_code in globals_, locals_

    end = None
    if end_arg is not None:
        end_code = compile(end_arg, '<command-line>', 'single')

        def end():
            exec end_code in globals_, locals_

    return transform, begin, end


def print_if(condition, *args):
    if condition:
        print ' '.join(str(arg) for arg in args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('transform', nargs='?', default=None,
                        help='Transformation command')
    parser.add_argument('--begin', '-b', default=None,
                        help='Transformation begin command')
    parser.add_argument('--end', '-e', default=None,
                        help='Transformation end command')
    parser.add_argument('--nostrip', '-S', dest='strip', action='store_false', default=True,
                        help='Do not strip "\\n" at end of lines')
    parser.add_argument('--input', '-i', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input file')
    parser.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output file')
    args = parser.parse_args()

    transform, begin, end = None, None, None
    if args.transform is not None:
        transform, begin, end = get_command_line_funcs(args.transform, args.begin, args.end)
    else:
        parser.error('Transformation is not specified')

    sys.stdout = args.output

    process(args.input, transform, begin, end, args.strip)


if __name__ == '__main__':
    main()