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
    transform = ExecFunc(transform_code, globals_, locals_, ['line'])

    begin = None
    if begin_arg is not None:
        begin_code = compile(begin_arg, '<command-line>', 'single')
        begin = ExecFunc(begin_code, globals_, locals_)

    end = None
    if end_arg is not None:
        end_code = compile(end_arg, '<command-line>', 'single')
        end = ExecFunc(end_code, globals_, locals_)

    return transform, begin, end


def print_if(condition, *args):
    if condition:
        print ' '.join(str(arg) for arg in args)


class ExecFunc(object):
    def __init__(self, code, globals_, locals_, arg_names=None):
        self.code = code
        self.globals = globals_
        self.locals = locals_
        self.arg_names = arg_names

    def __call__(self, *args, **kwargs):
        if args:
            self.locals.update(zip(self.arg_names, args))
        if kwargs:
            self.locals.update(kwargs)
        exec (self.code, self.globals, self.locals)


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
    parser.add_argument('--input', '-i', type=argparse.FileType(mode='r', bufsize=1024 * 1024), default=sys.stdin,
                        help='Input file')
    parser.add_argument('--output', '-o', type=argparse.FileType(mode='w', bufsize=1024 * 1024), default=sys.stdout,
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