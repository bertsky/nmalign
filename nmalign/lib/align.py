import re
import unicodedata
import joblib
from rapidfuzz.process import cdist
from rapidfuzz.distance.Levenshtein import normalized_similarity
from rapidfuzz.fuzz import partial_ratio, partial_ratio_alignment
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

SUBSEG_LEN_MIN = 20 # string length above which subsegmentation is attempted
SUBSEG_ACC_MAX = 0.9 # alignment accuracy below which subsegmentation is attempted
SUBSEG_ACC_MIN = 0.0 # alignment accuracy above which subsegmentation is attempted
PARTIAL_ACC_MIN = 60 # minimum subalignment score during subsegmentation

def match(l1, l2, workers=1, normalization=None, cutoff=None, try_subseg=False):
    """Force alignment of string lists.

    Computes string alignments between each pair among l1 and l2.
    Then iteratively searches the next closest pair. Stores
    the assigned result a mapping from l1 to l2.
    (Unmatched or cut off elements will be assigned -1.
     When subsegmentation is allowed, searches for subalignments
     of suboptimal matches in l2, i.e. may assign multiple l1 segments.)

    Returns corresponding list indices and match scores [0.0,1.0]
    as a tuple of Numpy arrays.
    """
    assert len(l1) > 0
    assert len(l2) > 0
    assert isinstance(l1[0], str)
    assert isinstance(l2[0], str)
    # considerations:
    # - normalization will allow short sequences to go before larger (equally scoring) ones,
    #   but we prefer largest-first; so prior to argmax, multiply normalized similarity
    #   with l2 lengths
    # - some bonus for local in-order (e.g. below region) is needed, especially for bad pairs;
    #   so prior to argmax, add a cost as number of already aligned pairs times each candidate's
    #   deviation from local monotonicity
    #   (monotonicity can be formalised as block-triangular boolean matrix:
    #    each existing pair/alignment defines the corner/intersection of two blocks,
    #    with (0,0) and (L,L) as a priori edges; blocks represent where new (x,y) pairs
    #    are compatible with the existing choices; in case of non-monotonicity,
    #    i.e. when some neighbouring (x1,y1) and (x2,y2) with x1<x2 != y1<y2 exist,
    #    there is no block between [x1,x2] _and_ [y1,y2] - so no new point in the vicinity
    #    gets prioritised until new neighbours arrive)
    # FIXME: for maximal use (e.g. both page-wise and line-wise alignment), consider using coarser metrics than Levenshtein on larger sequences
    # FIXME: allow passing confidence input (larger OCR confidence - less permissable deviation)
    def preprocess(s):
        if isinstance(normalization, dict):
            for pattern, replacement in normalization.items():
                s = re.sub(pattern, replacement, s)
        s = unicodedata.normalize('NFKC', s)
        return s
    dist = cdist(l1, l2, scorer=normalized_similarity, score_cutoff=cutoff,
                 processor=preprocess, workers=workers)
    dim1 = len(l1)
    dim2 = len(l2)
    idx1 = np.arange(dim1)
    idx2 = np.arange(dim2)
    keep1 = np.ones(dim1, dtype=np.bool)
    keep2 = np.ones(dim2, dtype=np.bool)
    result = -1 * np.ones(dim1, dtype=np.int)
    if try_subseg:
        # result must also hold start and end pos
        result = np.tile(result, (3, 1))
        result_idx, result_beg, result_end = result
    else:
        result_idx = result
    # normalized similarity favours short sequences, which are "easier" to align
    # but we want to start with longest matches, so multiply with sequence length
    scores = np.zeros(dim1, dtype=dist.dtype)
    length = np.tile(list(map(len, l2)), (dim1, 1))
    for _ in range(dim1):
        # make efficient view of remaining indexes
        distview = dist[np.ix_(keep1,keep2)]
        if not distview.size:
            break
        # in addition to isolated match score, we want to prioritise new mappings that
        # keep consistency with current mappings and local ordering on both sides, i.e.
        # monotonicity in the neighbourhood of current mappings
        monotonicity = np.zeros(dist.shape, dtype=np.bool)
        prev_ind1, prev_ind2 = 0, 0
        for ind1, ind2 in list(zip(np.flatnonzero(~keep1), result_idx[~keep1])) + [(dim1, dim2)]:
            if (ind1 >= prev_ind1) == (ind2 >= prev_ind2):
                monotonicity[prev_ind1:ind1, prev_ind2:ind2] = True
            else:
                monotonicity[prev_ind1:ind1, :] = False
                monotonicity[:, ind2:prev_ind2] = False
            prev_ind1, prev_ind2 = ind1, ind2
        monotonicity = monotonicity[np.ix_(keep1, keep2)]
        coverage = 1.0 - monotonicity.shape[0] / dim1 # sigmoid in nr of assigned idx1:
        coverage = 0.5 / (1 + np.exp(5 * (0.5 - coverage)))
        lengthview = length[np.ix_(keep1,keep2)]
        # score = (similarity [0.0-1.0] + monotonicity [0,] * coverage [0.0-0.5]) * length
        priority = (distview + coverage * monotonicity) * lengthview
        ind1, ind2 = np.unravel_index(np.argmax(priority, axis=None), priority.shape)
        scoresfor2 = distview[:,ind2] # for subseg below
        indxesfor2 = idx1[keep1] # for subseg below
        score = distview[ind1,ind2]
        if isinstance(cutoff, (int, float)) and score < cutoff:
            break
        # return to full view and assign next
        ind1 = idx1[keep1][ind1]
        ind2 = idx2[keep2][ind2]
        seg1 = l1[ind1]
        seg2 = l2[ind2]
        # assignment must be new
        assert result_idx[ind1] < 0
        assert keep1[ind1]
        assert keep2[ind2]
        # try subsegmentation / splitting ind2
        if (try_subseg and
            # not already very good alignment
            score < SUBSEG_ACC_MAX and
            # multiple words
            ' ' in seg2 and
            # long enough
            len(seg2) > SUBSEG_LEN_MIN and
            # seg2 a lot larger than seg1
            len(seg2) - len(seg1) > SUBSEG_LEN_MIN / 2):
            subseg = match_subseg(l1, seg2, scoresfor2, indxesfor2,
                                  min_score=score, workers=workers,
                                  processor=preprocess)
        else:
            subseg = []
        if not len(subseg):
            result_idx[ind1] = ind2
            scores[ind1] = score
            keep1[ind1] = False
            keep2[ind2] = False
        else:
            keep2[ind2] = False
            for subind1, begin, end, subscore in subseg:
                result_idx[subind1] = ind2
                result_beg[subind1] = begin
                result_end[subind1] = end
                scores[subind1] = subscore
                keep1[subind1] = False
    return result, scores

def match_subseg(l1, seg2, scoresfor2, indxesfor2, min_score=0, workers=1, processor=None):
    """look at all possible matches of seg2 per local alignment and find a set of mutually compatible subsegmentation"""
    # FIXME: rapidfuzz partial_ratio is not really usable: it is an average over windows
    #        along the local alignment (which means its score will always be >40
    #        as long as bigrams keep matching, and the start:end pos will usually
    #        not have any significant meaning); so we should use true Smith-Waterman here
    # more than 1 possible match of ind2
    if np.count_nonzero(scoresfor2 >= SUBSEG_ACC_MIN) < 2:
        return [] # global alignment is just too bad to begin with
    # -- first, get a fast overview of where to look for matches (in parallel, without the actual alignments)
    subinds = indxesfor2[scoresfor2 >= SUBSEG_ACC_MIN]
    subl1 = [l1[subind1] for subind1 in subinds]
    subl2 = [seg2]
    subdist = cdist(subl1, subl2, scorer=partial_ratio, score_cutoff=PARTIAL_ACC_MIN,
                    processor=processor, workers=workers)
    if np.count_nonzero(subdist >= PARTIAL_ACC_MIN) < 2:
        return [] # no (good) other matches available
    # -- second, find the actual local alignment of the good candidates,
    #            and prepare a new alignment matrix for all candidates
    #            as complete subsegmentations of seg2
    len2 = len(seg2) + 1
    subscoresfor2 = np.inf * np.ones((len2, len2)) # alignment distances from l1 to seg2[start:end]
    subindxesfor2 = -1 * np.ones((len2, len2), dtype=np.int) # alignment indices from l1 to seg2[start:end]
    # prefill with deletion distances (because partial_ratio might skip some chars)
    for i in range(len2):
        for j in range(i + 1, len2):
            subscoresfor2[i, j] = j - i
    def produce():
        for subind1 in np.nonzero(subdist >= PARTIAL_ACC_MIN)[0]:
            #subscore1 = subdist[subind1, 0]
            subind1 = subinds[subind1]
            seg1 = l1[subind1]
            yield seg1, subind1
    def consume(input_):
        seg1, ind1 = input_
        # zzz: ensure that seg1 is nearly complete
        return partial_ratio_alignment(seg1, seg2, processor=processor), ind1
    job = joblib.Parallel(n_jobs=workers)
    for subscore, subind1 in job(joblib.delayed(consume)(item) for item in produce()):
        subscore1 = (1.0 - subscore.score / 100) * (subscore.dest_end - subscore.dest_start)
        subscoresfor2[subscore.dest_start, subscore.dest_end] = subscore1
        subindxesfor2[subscore.dest_start, subscore.dest_end] = subind1
    # -- third, find the shortest path through the subsegmentation matrix,
    #           i.e. the best global sequence of non-overlapping local alignments
    subdist, subpath = shortest_path(csgraph=csr_matrix(subscoresfor2),
                                     indices=0, return_predecessors=True)
    # convert to score again and check if better than single match
    if (len2 - subdist[-1]) / len2 <= min_score:
        return []
    # follow up on best path
    subresult = []
    subpos = len2 - 1
    while subpos > 0:
        prepos = max(0, subpath[subpos])
        subscore = subdist[subpos] - subdist[prepos]
        subind = subindxesfor2[prepos, subpos]
        if subind >= 0:
            subresult.append((subind, prepos, subpos, 1.0 - subscore / (subpos - prepos)))
        subpos = prepos
    return subresult
