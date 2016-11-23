#!/usr/bin/env python
import abc
import argparse
import csv
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('transform', type=compile_expr, help='Transformation code')
    parser.add_argument('--input', '-i', help='Main input file')
    parser.add_argument('--output', '-o', help='Main output file')
    parser.add_argument('--input2', '-I', help='Secondary input file')
    parser.add_argument('--output2', '-O', help='Secondary output file')

    parser.add_argument('--in-format', default='text', help='Format of the main input. Available formats: '
                                                            'text (default), text-lines, tsv, tsv-header, json.')
    parser.add_argument('--out-format', default='text', help='Format of the main output. Available formats: '
                                                             'text (default), tsv, tsv-header, json, json-node.')
    parser.add_argument('--in2-format', default='text', help='Format of the main input. Available formats: '
                                                             'text (default), text-lines, tsv, tsv-header, json.')
    parser.add_argument('--out2-format', default='text', help='Format of the main output. Available formats: '
                                                              'text (default), tsv, tsv-header, json, json-node.')

    parser.add_argument('--map', '-m', action='store_true',
                        help='Apply transformation for each element of the main input')
    parser.add_argument('--begin', '-b', type=compile_expr, help='Code to execute before transformations')
    parser.add_argument('--end', '-e', type=compile_expr, help='Code to execute after transformations')

    args = parser.parse_args()

    temp_file = None
    if args.input is None:
        input_stream1 = sys.stdin
    else:
        input_stream1 = open(args.input, 'r')
    if args.output is None:
        output_stream1 = sys.stdout
    elif args.output not in [args.input, args.input2]:
        output_stream1 = open(args.output, 'w')
    else:
        temp_file = args.output + '~'
        output_stream1 = open(temp_file, 'w')
    temp_file2 = None
    if args.input2 is None:
        input_stream2 = None
    else:
        input_stream2 = open(args.input2, 'r')
    if args.output2 is None:
        output_stream2 = None
    elif args.output2 not in [args.input, args.input2]:
        output_stream2 = open(args.output2, 'w')
    else:
        temp_file2 = args.output2 + '~'
        output_stream2 = open(temp_file2, 'w')

    process(args.transform, input_stream1, output_stream1, args.in_format, args.out_format,
            input_stream2, output_stream2, args.in2_format, args.out2_format,
            args.map, args.begin, args.end)

    if temp_file is not None:
        output_stream1.close()
        os.rename(temp_file, args.output)
    if temp_file2 is not None:
        output_stream2.close()
        os.rename(temp_file2, args.output2)


def process(transformation, input1_stream, output1_stream,
            input1_format=None, output1_format=None,
            input2_stream=None, output2_stream=None,
            input2_format=None, output2_format=None,
            mapping_mode=False, begin=None, end=None):
    input1 = get_input(input1_stream, input1_format)
    output1 = get_output(output1_stream, output1_format)
    input2 = get_input(input2_stream, input2_format) if input2_stream is not None else None
    output2 = get_output(output2_stream, output2_format) if output2_stream is not None else None

    def output(value, stream=1):
        if stream == 1:
            output1(value)
        elif stream == 2:
            if output2 is None:
                raise Exception('Secondary output is not specified')
            output2(value)
        else:
            raise Exception('Incorrect stream index: %s' % stream)

    user_vars = {'input': input1, 'input1': input1, 'input2': input2,
                 'output': output, 'output1': output1, 'output2': output2}

    if begin is not None:
        exec begin in user_vars, user_vars
    if mapping_mode:
        for _index, _ in enumerate(input1):
            user_vars['_'] = _
            user_vars['_index'] = _index
            exec transformation in user_vars, user_vars
    else:
        exec transformation in user_vars, user_vars
    if end is not None:
        exec end in user_vars, user_vars

    output1.finish()
    if output2 is not None:
        output2.finish()


def get_input(input_stream, input_format):
    if input_format == 'text' or input_format is None:
        return input_stream
    if input_format == 'text-lines':
        return (line.rstrip('\r\n') for line in input_stream)
    if input_format == 'tsv':
        return csv.reader(input_stream, delimiter='\t')
    if input_format == 'tsv-header':
        return csv.DictReader(input_stream, delimiter='\t')
    if input_format == 'json':
        return json.load(input_stream)
    raise Exception('Unknown input format: %s' % input_format)


def get_output(output_stream, output_format):
    if output_format == 'text' or output_format is None:
        return TextOutput(output_stream)
    if output_format == 'tsv':
        return TsvOutput(output_stream)
    if output_format == 'tsv-header':
        return TsvWithHeaderOutput(output_stream)
    if output_format == 'json':
        return JsonOutput(output_stream, True)
    if output_format == 'json-node':
        return JsonOutput(output_stream, False)
    raise Exception('Unknown output format: %s' % output_format)


class Output(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, output_stream):
        self.output = output_stream

    @abc.abstractmethod
    def __call__(self, value):
        pass

    @abc.abstractmethod
    def finish(self):
        pass


class TextOutput(Output):
    def __call__(self, value):
        print >> self.output, value

    def finish(self):
        pass


class TsvOutput(Output):
    def __init__(self, output_stream):
        super(TsvOutput, self).__init__(output_stream)
        self.writer = csv.writer(output_stream, delimiter='\t', lineterminator=os.linesep)

    def __call__(self, value):
        self.writer.writerow(value)

    def finish(self):
        pass


class TsvWithHeaderOutput(Output):
    def __init__(self, output_stream):
        super(TsvWithHeaderOutput, self).__init__(output_stream)
        self.writer = None

    def __call__(self, value):
        if self.writer is None:
            self.writer = csv.DictWriter(self.output, list(value), delimiter='\t', lineterminator=os.linesep)
            if not isinstance(value, dict):
                return

        if isinstance(value, dict):
            self.writer.writerow(value)
        else:
            self.writer.writerow(dict(zip(self.writer.fieldnames, value)))

    def finish(self):
        pass


class JsonOutput(Output):
    def __init__(self, output_stream, add_to_list):
        super(JsonOutput, self).__init__(output_stream)
        self.add_to_list = add_to_list
        self.result = [] if add_to_list else None

    def __call__(self, value):
        if self.add_to_list:
            self.result.append(value)
        else:
            self.result = value

    def finish(self):
        json.dump(self.result, self.output)


def compile_expr(expr):
    return compile(expr, '<command-line>', 'exec')

if __name__ == '__main__':
    main()
