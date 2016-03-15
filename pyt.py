#!/usr/bin/env python
import argparse
import os
import sys
import math


def process(transformation, input_stream, output_stream,
            extended=False, strip_lines=True, auto_print=False, split=False):
    prev_stdout = sys.stdout
    sys.stdout = output_stream
    if strip_lines:
        input_stream = (line.rstrip('\n') for line in input_stream)

    try:
        transform_code = compile(transformation, '<command-line>', 'exec')
        if not extended:
            _globals = {'math': math}
            _locals = {}
            for line_index, line in enumerate(input_stream):
                if split:
                    records = line.split('\t')
                    _locals['records'] = records
                _locals['line'] = line
                _locals['index'] = line_index
                exec transform_code in _globals, _locals
                if auto_print:
                    print '\t'.join(str(record) for record in _locals['records']) if split else _locals['line']
        else:
            _globals = {'input': input_stream, 'math': math}
            _locals = {}
            exec transform_code in _globals, _locals
    finally:
        sys.stdout = prev_stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('transform',
                        help='Transformation command')
    parser.add_argument('input', nargs='?', help='Input file')
    parser.add_argument('output', nargs='?', help='Output file')
    parser.add_argument('--split', '-s', action='store_true',
                        help='Split each line by "\\t". Tokens will be available in the "records" variable.')
    parser.add_argument('--print', '-p', dest='auto_print', action='store_true',
                        help='Print each line (or records joined by "\\t") after transformation')
    parser.add_argument('--nostrip', '-S', dest='strip', action='store_false',
                        help='Do not strip "\\n" at end of lines')
    parser.add_argument('--extended', '-e', action='store_true',
                        help='Extended mode: User code can use the input lines generator by accessing the "input"'
                             ' variable. The code is run only once.')
    args = parser.parse_args()

    temp_file = None
    if args.input is None:
        input_stream = sys.stdin
    else:
        input_stream = open(args.input, 'r')
    if args.output is None:
        output_stream = sys.stdout
    elif args.output != args.input:
        output_stream = open(args.output, 'w')
    else:
        temp_file = args.output + '~'
        output_stream = open(temp_file, 'w')

    process(args.transform, input_stream, output_stream, args.extended, args.strip, args.auto_print, args.split)

    if temp_file is not None:
        output_stream.close()
        os.rename(temp_file, args.output)


if __name__ == '__main__':
    main()