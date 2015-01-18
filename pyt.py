#!/usr/bin/python
import argparse
import sys


def process(transformation, input_stream, output_stream, extended=False, strip_lines=True):
    prev_stdout = sys.stdout
    sys.stdout = output_stream
    if strip_lines:
        input_stream = (line.rstrip('\n') for line in input_stream)

    try:
        transform_code = compile(transformation, '<command-line>', 'exec')
        if not extended:
            _globals = {}
            _locals = {}
            line_index = 0
            for line in input_stream:
                _locals['LINE'] = line
                _locals['LINE_INDEX'] = line_index
                exec transform_code in _globals, _locals
                line_index += 1

        else:
            _globals = {'INPUT': input_stream}
            _locals = {}
            exec transform_code in _globals, _locals
    finally:
        sys.stdout = prev_stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('transform',
                        help='Transformation command')
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input file')
    parser.add_argument('output', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='Output file')
    parser.add_argument('--nostrip', '-S', dest='strip', action='store_false', default=True,
                        help='Do not strip "\\n" at end of lines')
    parser.add_argument('--extended', '-e', action='store_true', default=False,
                        help='Extended mode: User code can use the input lines generator by accessing the INPUT'
                             ' variable. The code is run only once.')
    args = parser.parse_args()

    process(args.transform, args.input, args.output, args.extended, args.strip)


if __name__ == '__main__':
    main()