#!/usr/bin/env python3

'''
TODO:

# hashcat rules
RuleGen.write(self, percent=90):

# output string list
class WordGen():

# overseer
class Overseer():
    1. generate lists (put in /tmp if not hashcat)
    2. generate rules (put in /tmp if not hashcat)
    3. if hashcat: generate scripts
    3. else: output to stdout


'''
import pickle
import itertools
from time import sleep
from pathlib import Path
from functools import reduce
from sys import exit, stdin, stderr
from argparse import ArgumentParser, FileType, ArgumentError

### DEFAULTS ###

leet_chars      = (b'013578@$') # characters to consider "leet"

max_leet        = 64            # max number of leet mutations per word
max_cap         = 128           # max number of capitaliztion mutations per word

report_limit    = 50            # maximum lines for each individual report

string_delim    = b'\x00'       # unique unprintable placeholder for strings
digit_delim     = b'\x01'       # unique unprintable placeholder for digits



### CLASSES ###

class RuleGen():
    '''
    generates rules based on wordlist
    optionally generate hashcat rules and/or displays report
    '''

    def __init__(self, in_list, leet=True, custom_digits=[]):
        '''
        in_list is iterable of already-grouped words
        '''

        self.leet = leet
        self.custom_digits = list(custom_digits)

        self.rules = {}
        self.num_rules = 0

        for word in Grouper(in_list).parse():
            self.add(word)


    def report(self, display_limit=50):

        #for chartype in self.rules:
        sorted_rules = list(self.rules.items())
        sorted_rules.sort(key=lambda x: x[1], reverse=True)

        display_count = 0
        display_len = 0
        for rule in sorted_rules[:display_limit]:
            display_count += rule[1]
            display_len += 1

        try:
            percent_displayed = (display_count / self.num_rules) * 100
        except:
            assert False, 'No rules to display.'

        report = []

        title_str = '\n\nTop {:,} Rules out of {:,} ({:.1f}% coverage)'.format(display_len, len(self.rules), percent_displayed)
        report.append(title_str)
        report.append('='*len(title_str))

        for rule in sorted_rules[:display_len]:
            rule_bytes, rule_count = rule

            #b = '  {}:  "{}"'.format(str(rule_count), rule[0].replace(string_delim, b'__').decode())
            if self.custom_digits:
                rule_bytes = rule_bytes.replace(bytes(digit_delim), b'[digit]')

            rule_coverage = (rule_count / self.num_rules) * 100
                
            report.append('{:>15,} ({:.1f}%):    {:<30}'.format(rule_count, rule_coverage, rule_bytes.replace(string_delim, b'[string]').decode()))

        return '\n'.join(report) + '\n'



    def write_rules(self):

        pass



    def add(self, groups):
        '''
        takes & parses already-split word
        '''

        num_groups = len(groups)
        if not num_groups > 1 and num_groups < 6:
            return

        for index in range(num_groups):
            chartype = groups[index][0]
            if chartype == 2 or chartype == 4:
                continue

            p1 = groups[:index]
            p2 = groups[index+1:]

            prepend = b''.join(g[1] for g in p1)
            append = b''.join(g[1] for g in p2)
            
            if self.custom_digits:

                for p in range(len(p1)):
                    if p1[p][0] == 2:
                        new_prepend = list(p1)
                        new_prepend[p] = (2, digit_delim)
                        new_prepend = b''.join(g[1] for g in new_prepend)
                        rule = new_prepend + string_delim + append
                        self._add_rule(rule, digit=True)

                for a in range(len(p2)):
                    if p2[a][0] == 2:
                        new_append = list(p2)
                        new_append[a] = (2, digit_delim)
                        new_append = b''.join(g[1] for g in new_append)
                        rule = prepend + string_delim + new_append
                        self._add_rule(rule, digit=True)

            else:

                rule = prepend + string_delim + append
                self._add_rule(rule)


    def _add_rule(self, rule, digit=False):

        if digit:
            n = len(self.custom_digits)
            self.num_rules += n
            try:
                self.rules[rule] += n
            except KeyError:
                self.rules[rule] = n
                
        else:
            self.num_rules += 1
            try:
                self.rules[rule] += 1
            except KeyError:
                self.rules[rule] = 1



class ListGen():

    def __init__(self, in_list, digits=False):
        '''
        accepts iterable of words from which to generate list
        of individual strings and/or digits
        '''
        
        # dictionary to hold common string/digit occurences
        # 1 = strings
        # 2 = digits
        # string/digit instances are stored in dictionary in the format: {occurence:count, ... }
        self.lists      = {
            # chartype  list
            1:  {},
            2:  {}
        }

        self.totals     = {
            1: 0,
            2: 0
        }

        self.chartypes = {
            1: 'words',
        }
        if digits:
            self.chartypes[2] = 'digits'

        self.in_list    = in_list
        self.digits     = digits

        for word in Grouper(in_list).parse():
            self.add(word)


    def report(self, display_limit=50, write=''):

        report = []

        for chartype in self.chartypes:
            sorted_words = list(self.lists[chartype].items())
            sorted_words.sort(key=lambda x: x[1], reverse=True)

            display_count = 0
            display_len = 0
            for word in sorted_words[:display_limit]:
                display_count += word[1]
                display_len += 1

            try:
                percent_displayed = (display_count / self.totals[chartype]) * 100
            except:
                report.append('\nNo {} to display.\n'.format(self.chartypes[chartype]))

            title_str = '\n\nTop {:,} {} out of {:,} ({:.1f}% coverage)'.format(display_len, self.chartypes[chartype].capitalize(), len(self.lists[chartype]), percent_displayed)
            report.append(title_str)
            report.append('='*len(title_str))

            for word in sorted_words[:display_len]:
                string, count = word

                occurance = (count / self.totals[chartype]) * 100
                    
                report.append('{:>15,} ({:.1f}%):    {:<30}'.format(count, occurance, string.decode()))

            if write:
                self.write(sorted_words, write, '_{}'.format(self.chartypes[chartype]))

        return '\n'.join(report) + '\n'


    def write(self, sorted_list, filename, suffix):

        with open(str(filename) + suffix, 'wb') as f:
            for word in sorted_list:
                f.write(word[0] + b'\n')


    def add(self, word):

        for group in word:
            chartype, string = group
            if chartype == 4 or (chartype == 2 and not self.digits):
                continue
            try:
                self.lists[chartype][string] += 1
            except KeyError:
                self.lists[chartype][string] = 1
            self.totals[chartype] += 1



class Mutator():

    def __init__(self, in_list, perm=0, leet=True, cap=True, capswap=True):

        # "leet" character swaps - modify as needed.
        # Keys are replaceable characters; values are their leet replacements.

        self.leet_common = self._dict_str_to_bytes({
            'a': ['@'],
            'A': ['@'],
            'e': ['3'],
            'E': ['3'],
            'i': ['1'],
            'I': ['1'],
            'o': ['0'],
            'O': ['0'],
            's': ['$'],
            'S': ['$'],
        })

        self.leet_all = self._dict_str_to_bytes({
            'a': ['4', '@'],
            'A': ['4', '@'],
            'b': ['8'],
            'B': ['8'],
            'e': ['3'],
            'E': ['3'],
            'i': ['1'],
            'I': ['1'],
            'l': ['1'],
            'L': ['1'],
            'o': ['0'],
            'O': ['0'],
            's': ['5', '$'],
            'S': ['5', '$'],
            't': ['7'],
            'T': ['7']
        })

        self.in_list        = in_list

        # max = maximum mutations per word
        # cur = used for carrying over unused mutations into next iteration
        self.max_leet       = max_leet
        self.max_cap        = max_cap
        self.cur_leet       = 0
        self.cur_cap        = 0

        self.perm_depth     = perm
        self.do_leet        = leet
        self.do_capswap     = capswap
        self.do_cap         = cap or capswap


    def gen(self):
        '''
        generator function
        runs mangling functions on wordlist
        yields each mutated word
        '''

        for word in self.cap(self.leet(self.perm(self.in_list))):
            yield word


    def perm(self, in_list, repeat=True):
        '''
        permutates words from iterable
        takes:      iterable containing words
        yields:     word permutations ('pass', 'word' --> 'password', 'wordpass', etc.)
        '''

        if self.perm_depth > 1:

            words = list(in_list)
            
            for d in range(1, self.perm_depth+1):
                if repeat:
                    for p in itertools.product(words, repeat=d):
                        yield b''.join(p)

                else:
                    for p in itertools.permutations(words, d):
                        yield b''.join(p)
        else:
            for word in in_list:
                yield word


    def cap(self, in_list):

        for word in in_list:

            if self.do_cap:

                self.cur_cap += self.max_cap

                for r in self._cap(word):
                    self.cur_cap -= 1
                    yield r
                    if self.cur_cap <= 0:
                        break

            else:
                yield word


    def leet(self, in_list):

        for word in in_list:

            if self.do_leet:

                self.cur_leet += self.max_leet

                results = [] # list is almost 4 times faster than set
                num_results = 0

                gen_common = self._leet(word, swap_values=self.leet_common)
                for r in gen_common:
                    if not r in results:
                        if self.cur_leet <= 0:
                            break
                        results.append(r)
                        self.cur_leet -= 1
                        yield r

                gen_sparse = self._leet(word, swap_values=self.leet_all, passthrough=False)
                for r in gen_sparse:
                    if not r in results:
                        if self.cur_leet <= 0:
                            break
                        results.append(r)
                        self.cur_leet -= 1
                        yield r


                self.cur_leet += (self.max_leet - len(results))

                results = []

            else:
                yield word


    def _cap(self, word, swap=True):
        '''
        takes:      iterable containing words
                    passthrough: whether or not to yield unmodified word
        yields:     case variations (common only, unless 'all' is specified)
        '''

        # set type used to prevent duplicates
        results = []
        self._uniq_add(results, word)
        self._uniq_add(results, word.lower())
        self._uniq_add(results, word.upper())
        self._uniq_add(results, word.swapcase())
        self._uniq_add(results, word.capitalize())
        self._uniq_add(results, word.title())

        for r in results:
            yield r

        if self.do_capswap:

            # oneliner which basically does it all
            # TODO: change to emulate leet function with common and less common caps
            for r in map(bytes, itertools.product(*zip(word.lower(), word.upper()))):
                if not r in results:
                    results.append(r)
                    yield r


    def _uniq_add(self, l, e):

        if not e in l:
            l.append(e)


    def _dict_str_to_bytes(self, d):

        new_dict = {}
        for key in d:
            new_dict[ord(key)] = [ord(v) for v in d[key]]
        return new_dict


    def _leet(self, word, swap_values=None, passthrough=True):
        '''
        takes:      iterable containing words
                    swap_values: dictionary containing leet swaps
                    passthrough: whether or not to yield unmodified word
        yields:     leet mutations, not exceeding max_results per word
        '''

        if not swap_values:
            swap_values = self.leet_all

        if passthrough:
            yield word

        swaps = []
        word_length = len(word)

        for i in range(word_length):
            try:
                for l in swap_values[word[i]]:
                    swaps.append((i, l))

            except KeyError:
                continue

        num_swaps_range = range(len(swaps))
        word_list = list(word)


        for num_swaps in num_swaps_range:

            for c in itertools.combinations(num_swaps_range, num_swaps+1):

                try:

                    new_word = word_list.copy()
                    already_swapped = []

                    for n in c:
                        assert not swaps[n][0] in already_swapped
                        new_word[swaps[n][0]] = swaps[n][1]
                        already_swapped.append(swaps[n][0])

                    yield bytes(new_word)

                except AssertionError:
                    continue



class Grouper():
    '''
    Takes words as iterable of 'bytes' objects
    Yields each word, split by character type
    Format is ( (chartype, "chunk"), ... )
    '''

    def __init__(self, in_list, leet=True, progress=True):

        self.in_list    = in_list
        self.leet       = leet
        self.progress   = progress
        self.processed  = 0


    def parse(self):
        '''
        generator function
        parses list and yields each word, split into chunks based on chartype
        '''

        for word in self.in_list:
            if self.progress == True and self.processed % 1000 == 0:
                stderr.write('{:,} words processed      \r'.format(self.processed))
            yield self.group_word(word)
            self.processed += 1 


    def group_word(self, word):

        group_map = self.group_chartypes(word)
        groups = []

        for chunk in group_map:
            groups.append( ( chunk[0], word[ chunk[1][0]:chunk[1][1] ] ) )

        if self.leet:
            return self.group_l33t(groups)
        else:
            return groups


    def group_chartypes(self, b):

        group_map       = []
        # [ ( chartype, (start,end) ), ... ]

        start           = 0
        end             = 0
        group           = bytes()
        prev_chartype   = 0
        group_index     = 0

        for index in range(len(b)):
            chartype = self.get_chartype(b[index:index+1])

            if not chartype & prev_chartype:
                if start-end:
                    group_map.append( (prev_chartype, (start,end)) )
                    group_index += 1
                start = index

            end = index + 1
            prev_chartype = int(chartype)

        if start-end:
            group_map.append( (prev_chartype, (start,end)) )
            group_index += 1

        return group_map


    def get_chartype(self, char):

        if char.isalpha():
            return 1
        elif char.isdigit():
            return 2
        else:
            return 4


    def group_l33t(self, groups):

        try:
            assert len(groups) > 2
            # word must have at least two chartypes
            assert reduce( (lambda x,y: x&y), [v[0] for v in groups] ) not in (1,2,4)

            l33t_groups = []
            group_index = 0

            while 1:
                try:
                    if groups[group_index][0] & 1 > 0 and groups[group_index+1][0] & 6 > 0 and groups[group_index+2][0] & 1 > 0:

                        if all(c in leet_chars for c in groups[group_index+1][1]):
                            l33t_groups.append(self._combine_groups(groups[group_index:group_index+3]))
                            group_index += 3
                        else:
                            l33t_groups += groups[group_index:group_index+2]
                            group_index += 2

                    else:
                        l33t_groups.append(groups[group_index])
                        group_index += 1

                except IndexError:
                    l33t_groups += groups[group_index:]
                    break

            assert groups != l33t_groups
            return self.group_l33t(l33t_groups)

        except AssertionError:
            return groups


    def _combine_groups(self, groups):

        chartype    = groups[0][0] # just take chartype of first group
        string      = b''

        for group in groups:
            #chartype = chartype | group[0]
            string += group[1]

        return (chartype, string)



class ReadWords():

    def __init__(self, filename):

        self.filename = str(filename)
        assert(Path(self.filename).is_file()), 'Cannot find the file {}'.format(self.filename)


    def read(self):

        with open(self.filename, 'rb') as f:
            for line in f:
                try:
                    assert not string_delim in line
                    yield line.strip(b'\r\n')
                except AssertionError:
                    continue



class ReadSTDIN():

    def __init__(self):

        self.wordlist = []


    def read(self):

        if not self.wordlist:
            while 1:
                line = stdin.buffer.readline()
                if line:
                    try:
                        assert not string_delim in line
                        self.wordlist.append(line.strip(b'\r\n'))
                    except AssertionError:
                        continue
                else:
                    break

        return self.wordlist



def read_digits(s):

    try:
        digits = ReadWords(s).read()
    except AssertionError:
        digits = [d.encode() for d in s.split(',')]

    for d in digits:
        yield d



if __name__ == '__main__':

    ### ARGUMENTS ###

    parser = ArgumentParser(description="FETCH THE PASSWORD STRETCHER")

    parser.add_argument('-w', '--wordlist',         type=ReadWords,   default=ReadSTDIN(),      help="wordlist to mangle (default: STDIN)")
    parser.add_argument('-d', '--digits',           type=read_digits, default=[],               help="create rules using these digits")
    parser.add_argument('-s', '--save',             type=Path,                                  help="save individual strings/digits in this file")
    parser.add_argument('-r', '--report',           action='store_true',                        help="print report")

    parser.add_argument('-L',   '--leet',           action='store_true',                        help="\"leetspeak\" mutations")
    parser.add_argument('-c',   '--capital',        action='store_true',                        help="common upper/lowercase variations")
    parser.add_argument('-C',   '--capswap',        action='store_true',                        help="all possible case combinations")
    #parser.add_argument('-P',   '--permutations',   type=int,           default=1,              help="Max times to combine words (careful! exponential)", metavar='INT')


    try:

        options = parser.parse_args()

        # def __init__(self, in_list, perm=0, leet=True, cap=True, capswap=True):
        #m = Mutator(options.wordlist, leet=options.leet, cap=options.capital, capswap=options.capswap)
        #g = m.gen()

        l = ListGen(options.wordlist.read(), digits=(True if options.digits else False))
        r = RuleGen(options.wordlist.read(), custom_digits=options.digits)

        if options.report:
            print(l.report(10, options.save))
            print(r.report(10))



    except ArgumentError:
        stderr.write("\n[!] Check your syntax. Use -h for help.\n")
        exit(2)
    except AssertionError as e:
        stderr.write("\n[!] {}\n".format(str(e)))
        exit(1)
    except KeyboardInterrupt:
        stderr.write("\n[!] Program interrupted.\n")
        exit(2)
