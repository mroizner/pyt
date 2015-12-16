PyT
===

PyT (Python Transformer) is a tool designed to simplify file processing routine. Basically, it is a tool that runs a user specified piece of Python code for each line in the file. PyT can be used as an alternative to standard Unix tools such as awk, sed, grep, etc.

Installation
============

Just clone the repository and make a symlink:
```bash
$ git clone git://github.com/mroizner/pyt.git ~/pyt
$ mkdir -p ~/bin
$ ln -s ~/pyt/pyt.py ~/bin/pyt
```
If ~/bin is not in your $PATH you can add it:
```bash
$ echo 'export PATH+=\"~/bin:\$PATH\"' >> ~/.bashrc
$ . ~/.bashrc
```
  
Quick start
===========

Suppose you have a file "input.txt" that you want to be processed:
```
1
1	1
1	2	1
1	3	3	1
1	4	6	4	1
```

Basic usage
-----------

The simple way of using PyT is just specifying any Python code you want to be called for each line. The line itself will be passed to the code as a variable `line`. The index of the line (0-based) will be passed as a variable `index`.

If you want output number of characters on each line you can type:
```bash
$ pyt 'print len(line)' input.txt
1
3
5
7
9
```

You can write multi-line code:
```bash
$ pyt '
if index % 2 == 0:
  line = line.replace("\t", ", ")
  print len(line)
' input.txt
1
7
13
```

If you have a tsv-file you can use tab-separated values for each line in a variable `records` by specifying `--split` (`-s`):
```bash
$ pyt -s 'print sum(int(x) for x in records)' input.txt
1
2
4
8
16
```

If you want to print something for each line you can use `--print` (`-p`) option. In the split-mode, it prints tab-joined `records` variable. Otherwise it prints just the `line` variable.
```bash
$ pyt -s -p '
if len(records) > 1:
  records[0], records[1] = records[1], records[0]
' input.txt
1
1	1
2	1	1
3	1	3	1
4	1	6	4	1
```

As always, if you want to save the output to some file you can do it by specifying the file name. You can also read input data from the standard input rather than from a file, just omit the input file name. If the output file name is the same as the input file name the output will be written to a temp file and then the temp file will be renamed to the output file. 
```bash
$ cp input.txt output.txt
$ pyt -s 'print sum(int(x) for x in records)' output.txt output.txt
$ cat output.txt
1
2
4
8
16
```

By default, `\n` on the end of every line is omitted. You can use `--nostrip` (`-S`) option to keep it:
```bash
$ pyt -S 'print len(line)' input.txt
2
4
6
8
10
```

Extended mode
-------------

There some cases when you need to do something more than just to execute some simple code for every line. For example, you might need to import some modules. For such cases, you can use `--extended` (`-e`) option. In this mode, your code is executed only once for the whole input data (rather than for every line) and all the input is passed to your code as a varaible `input`. You can iterate over input lines with it:

```bash
$ pyt -e '
S = 0
for line in input:
  tokens = line.split()
  s = sum(int(x) for x in tokens)
  S += s
  print math.log(s)  # math is already imported
print S
' input.txt
0.0
0.69314718056
1.38629436112
2.07944154168
2.77258872224
31
```

If you use `--nostrip` option together with this mode, `input` will represent the input stream (with all the useful methods such as `read`) rather than just a generator of stripped lines.
