import click
import cloup
import json

from . import OptionEatAll
from ..lib import align

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@cloup.command(context_settings=CONTEXT_SETTINGS)
@cloup.option('-j', '--processes', default=1, help='number of processes to run in parallel', type=cloup.IntRange(min=1, max=32))
@cloup.option('-N', '--normalization', default=None, help='JSON object with regex patterns and replacements to be applied before comparison')
@cloup.option('-x', '--allow-splits', is_flag=True, help='find multiple submatches if replacement scores low')
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
def cli(processes, normalization, allow_splits, show_strings, show_files, separator,
        strings1, files1, filelist1,
        strings2, files2, filelist2):
    """Force-align two lists of strings.

    Computes string alignments between each pair among l1 and l2
    (after optionally normalising both sides).

    Then iteratively searches the next closest pair, while trying
    to maintain local monotonicity.

    If splits are allowed and the score is already low, then searches
    for more matches among l1 for the pair's right side sequence:
    If any subset of them can be combined into a path such that the
    sum score is better than the integral score, then prefers those
    assignments.

    Stores the assigned result as a mapping from l1 to l2.
    (Unmatched or cut off elements will be assigned -1.)

    Prints the corresponding list indices and match scores [0.0,1.0]
    as CSV data. (For subsequences, the start and end position will
    be appended.)
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
    if normalization:
        normalization = json.loads(normalization)
    else:
        normalization = None
    # calculate assignments and scores
    res, dst = align.match(list1, list2, normalization=normalization, workers=processes, try_subseg=allow_splits)
    if allow_splits:
        res_ind, res_beg, res_end = res
    else:
        res_ind = res
    scores = []
    match1 = set()
    match2 = set()
    for ind1, ind2 in enumerate(res_ind):
        score = dst[ind1]
        scores.append(score)
        if show_strings:
            if ind2 < 0:
                continue
            a = list1[ind1]
            b = list2[ind2]
            if allow_splits and res_beg[ind1] >= 0 and res_end[ind1] >= 0:
                b = b[res_beg[ind1]:res_end[ind1]]
        elif show_files:
            if ind2 < 0:
                continue
            a = files1[ind1]
            b = files2[ind2]
        else:
            a = str(ind1)
            b = str(ind2)
        msg = a + separator + b + separator + "%.2f" % score
        if allow_splits and res_beg[ind1] >= 0 and res_end[ind1] >= 0:
            msg += separator + str(res_beg[ind1]) + separator + str(res_end[ind1])
        click.echo(msg)
        if ind2 < 0:
            continue
        match1.add(ind1)
        match2.add(ind2)
    click.echo("average alignment confidence: %d%%" % (100 * sum(scores) / len(scores)), err=True)
    click.echo("coverage of matching inputs1: %d%%" % (100 * len(match1) / len(list1)), err=True)
    click.echo("coverage of matching inputs2: %d%%" % (100 * len(match2) / len(list2)), err=True)

if __name__ == '__main__':
    cli()
