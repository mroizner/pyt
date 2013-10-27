PyT
===

PyT (Python Transformer) is a tool designed to simplify file processing routine. Basically, it is a tool that runs a user specified piece of Python code for each line in the file. PyT can be used as an alternative to standard Unix tools such as awk, sed, grep, etc.

Installation
============

Just clone the repository and make a symlink:
```bash
$ mkdir -p ~/bin
$ git clone git://github.yandex-team.ru/roizner/pyt.git ~/bin/pyt
$ ln -s ~/bin/pyt/pyt.py ~/bin/pyt
```
If ~/bin is not in your $PATH you can add it:
```bash
$ echo "export PATH+=\"~/bin:\$PATH\" >> ~/.bashrc
$ . ~/.bashrc
```
  
Quick start
===========

Suppose you have a file "input.txt" that you want to be processed:
```
1
1 1
1 2 1
1 3 3 1
1 4 6 4 1
```

Basic usage
-----------

The simple way of using PyT is just specifying any Python command you want to be called for each line. The line itself will be passed to the command as a variable `line`.

If you want output number of characters on each line you can type:
```bash
$ pyt 'print len(line)' input.txt
1
3
5
7
9
```

The command must be a valid Python statement. Remember that you can run combine several statements into one with ";".
If you want to calculate sum of numbers for each line:
```bash
$ pyt 'tokens = line.split(); print sum(int(x) for x in tokens)' input.txt
1
2
4
8
16
```

If you want to save the output to some file you can do in the standard way by specifying the file name. You can also read input data from the standard input rather than file.
```bash
$ pyt 'tokens = line.split(); print sum(int(x) for x in tokens)' input.txt output.txt
$ cat output.txt
1
2
4
8
16
```

Begin and end commands
----------------------

You can specify *begin* and/or *end* commands that will be called before and after all the lines being processed correspondingly. These commands will be called in the same context as the main command, i.e. all these commands have access to the same set of variables.
For example, if you want to calculate the sum of all the numbers in the file:
```bash
$ pyt --begin 's = 0' 'tokens = line.split(); s += sum(int(x) for x in tokens)' --end 'print s' input.txt
31
```

Multi-line commands
-------------------

Sometimes, single Python statements are not enough. If you want to use *if*, *for*, etc. in your code you need the *extended* mode. In this mode, you can use `$^` as line breaks (like in regular expressions). If you want your next line to be indented use `$\^` for single indent, `$\\^` for double indent, and so on.
If you want to print even numbers in the file:
```bash
$ pyt -E 'tokens = line.split() $^ for t in tokens: $\^ x = int(t) $\^ if x % 2 == 0: $\\^ print x' input.txt
2
4
6
4
```

Commands in file
----------------

You can also write you commands in a separate file. The file should be a valid Python module. A function with name `transform` will be used as the main transfrom command. This function must be callable with one argument (a line). If there are functions with names `begin` and/or `end` they will be used as the corresponding commands.

Suppose you have a file transform.py:
```python
def transform(line):
    if len(line) < 4:
        print 'Line:', line
def end():
    print 'No more short lines left.'
```

You can use it with PyT:
```bash
$ pyt -f transform.py input.txt
Line: 1
Line: 1 1
No more short lines left.
```
