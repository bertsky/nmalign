from rapidfuzz.process import cdist
from rapidfuzz.string_metric import normalized_levenshtein
from rapidfuzz.fuzz import partial_ratio_alignment
import numpy as np

def match(l1, l2, workers=1, cutoff=None, try_subseg=False):
    """Force alignment of string lists.

    Computes string alignments between each pair among l1 and l2.
    Then iteratively searches the next closest pair. Stores
    the assigned result as injective mapping from l1 to l2.
    (Unmatched or cut off elements will be assigned -1.)
    Returns corresponding list indices and match scores [0,100]
    as a tuple of Numpy arrays.
    """
    assert len(l1) > 0
    assert len(l2) > 0
    assert isinstance(l1[0], str)
    assert isinstance(l2[0], str)
    # FIXME: normalization will allow short sequences to go before larger (equally scoring) ones, but we might prefer largest-first
    # FIXME: some bonus for local in-order (e.g. below region)?
    # FIXME: for maximal use (e.g. both page-wise and line-wise alignment), consider using coarser metrics than Levenshtein on larger sequences
    dist = cdist(l1, l2, scorer=normalized_levenshtein, score_cutoff=cutoff, workers=workers)
    ind1, ind2 = np.unravel_index(np.argmin(dist), dist.shape)
    dim1 = len(l1)
    dim2 = len(l2)
    idx1 = np.arange(dim1)
    idx2 = np.arange(dim2)
    keep1 = np.ones(dim1, dtype=np.bool)
    keep2 = np.ones(dim2, dtype=np.bool)
    result = -1 * np.ones(dim1, dtype=np.int)
    scores = np.zeros(dim1, dtype=dist.dtype)
    for _ in range(dim1):
        distview = dist[np.ix_(keep1,keep2)]
        if not distview.size:
            break
        ind1, ind2 = np.unravel_index(np.argmax(distview, axis=None), distview.shape)
        score = distview[ind1,ind2]
        if isinstance(cutoff, (int, float)) and score < cutoff:
            break
        ind1 = idx1[keep1][ind1]
        ind2 = idx2[keep2][ind2]
        assert result[ind1] < 0
        assert keep1[ind1]
        assert keep2[ind2]
        if try_subseg and score < 99:
            # if line1 is large enough and a lot larger than line2
            if ' ' in l1[ind1] and len(l1[ind1]) > 8 and len(l1[ind1]) - len(l2[ind2]) > 5:
                subscore = partial_ratio_alignment(l1[ind1], l2[ind2])
                src_length = len(l1[ind1])
            elif ' ' in l2[ind2] and len(l2[ind2]) > 8 and len(l2[ind2]) - len(l1[ind1]) > 5:
                subscore = partial_ratio_alignment(l2[ind1], l1[ind2])
                src_length = len(l2[ind2])
            else:
                subscore = None
            if subscore and subscore.score > score + 1 and (
                    (subscore.src_start > 0 and subscore.src_end == src_length) or
                    (subscore.src_start == 0 and subscore.src_end < src_length)):
                ...
                # problem: how to deal with rest of loop – revisit? disable cutoff?
                # problem: if chopping is allowed on both sides, who gets us the coordinates?
        result[ind1] = ind2
        scores[ind1] = score
        keep1[ind1] = False
        keep2[ind2] = False
    return result, scores
