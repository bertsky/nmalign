import click
import cloup

from . import OptionEatAll
from ..lib import align

@cloup.command()
@cloup.option('-j', '--processes', default=1, help='number of processes to run in parallel', type=cloup.IntRange(min=1, max=32))
@cloup.option('-s', '--show-strings', is_flag=True, help='print strings themselves instead of indices')
@cloup.option('-f', '--show-files', is_flag=True, help='print file names themselves instead of indices')
@cloup.constraint(cloup.constraints.mutually_exclusive, ['show_strings', 'show_files'])
@cloup.option('-S', '--separator', default='\t', help='print this string between result columns (default: tab)')
@cloup.option_group(
    'list to be replaced',
    #cloup.option('--files1', cls=OptionEatAll, type=cloup.File('r'), required=True)
    cloup.option('--strings1', cls=OptionEatAll, type=tuple, help='as strings'),
    cloup.option('--files1', cls=OptionEatAll, type=tuple, help='as file paths of strings'),
    cloup.option('--filelist1', type=cloup.File('r'), help='as text file with file paths of strings'),
    constraint=cloup.constraints.require_one)
@cloup.constraint(
    cloup.constraints.If('show_files',
                         then=cloup.constraints.require_one),
    ['files1', 'filelist1'])
@cloup.option_group(
    'list of replacements',
    cloup.option('--strings2', cls=OptionEatAll, type=tuple, help='as strings'),
    cloup.option('--files2', cls=OptionEatAll, type=tuple, help='as file paths of strings'),
    cloup.option('--filelist2', type=cloup.File('r'), help='as text file with file paths of strings'),
    constraint=cloup.constraints.require_one)
@cloup.constraint(
    cloup.constraints.If('show_files',
                         then=cloup.constraints.require_one),
    ['files2', 'filelist2'])
def cli(processes, show_strings, show_files, separator,
        strings1, files1, filelist1,
        strings2, files2, filelist2):
    """Force-align two lists of strings.

    Computes string alignments between each pair among l1 and l2.
    Then iteratively searches the next closest pair. Stores
    the assigned result as injective mapping from l1 to l2.
    (Unmatched or cut off elements will be assigned -1.)

    Prints the corresponding list indices and match scores [0,100]
    as CSV data.
    """
    #list1 = list(map(file_.read() for file_ in files1))
    if strings1:
        list1 = strings1
    else:
        if filelist1:
            files1 = list(map(str.strip, filelist1.readlines()))
        list1 = [open(filename, 'r').read() for filename in files1]
    if strings2:
        list2 = strings2
    else:
        if filelist2:
            files2 = list(map(str.strip, filelist2.readlines()))
        list2 = [open(filename, 'r').read() for filename in files2]
    # calculate assignments and scores
    res, dst = align.match(list1, list2, workers=processes)
    for ind1, ind2 in enumerate(res):
        score = str(dst[ind1])
        if show_strings:
            if ind2 < 0:
                continue
            a = list1[ind1]
            b = list2[ind2]
        elif show_files:
            a = files1[ind1]
            b = files2[ind2]
        else:
            a = str(ind1)
            b = str(ind2)
        click.echo(a + separator + b + separator + score)

if __name__ == '__main__':
    cli()
