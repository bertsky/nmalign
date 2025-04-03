import os
import re
import json
from itertools import chain
from typing import Optional, List, Union, get_args
import multiprocessing as mp

import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from ocrd import Workspace, Processor, OcrdPageResult
from ocrd_models import OcrdPage, OcrdFileType
from ocrd_models.ocrd_page import (
    TextLineType,
    TextEquivType,
    RegionRefType,
    RegionRefIndexedType,
    OrderedGroupType,
    OrderedGroupIndexedType,
    UnorderedGroupType,
    UnorderedGroupIndexedType,
    to_xml,
)
from ocrd_models.ocrd_page_generateds import (
    ReadingDirectionSimpleType,
    TextLineOrderSimpleType
)
from ocrd_modelfactory import page_from_file
from ocrd_utils import (
    MIMETYPE_PAGE,
    config,
    make_file_id,
)

from ..lib import align


class NMAlignMerge(Processor):

    @property
    def executable(self):
        return 'ocrd-nmalign-merge'

    @property
    def metadata_filename(self) -> str:
        return os.path.join('ocrd', 'ocrd-tool.json')

    def zip_input_files(self, **kwargs):
        # overrides ocrd.Processor.zip_input_files, which cannot be used;
        # we actually want input with MIMETYPE_PAGE for the first grp
        # and PAGE or (any number of) text/plain files for the second grp
        if not self.input_file_grp:
            raise ValueError("Processor is missing input fileGrp")

        input_grp, other_grp = self.input_file_grp.split(",")

        pages = {}
        for input_file in self.workspace.mets.find_all_files(
                pageId=self.page_id, fileGrp=input_grp, mimetype=MIMETYPE_PAGE):
            if not input_file.pageId:
                # ignore document-global files
                continue
            ift = pages.setdefault(input_file.pageId, [None, None])
            if ift[0]:
                self._base_logger.debug(f"another PAGE file {input_file.ID} for page {input_file.pageId} "
                                        f"in input file group {input_grp}")
                raise NonUniqueInputFile(input_grp, input_file.pageId, None)
            self._base_logger.debug(f"adding file {input_file.ID} for page {input_file.pageId} "
                                    f"from input file group {input_grp}")
            ift[0] = input_file
        mimetype = "//(%s|text/plain)" % re.escape(MIMETYPE_PAGE)
        for other_file in self.workspace.mets.find_all_files(
                pageId=self.page_id, fileGrp=other_grp, mimetype=mimetype):
            if not other_file.pageId:
                # ignore document-global files
                continue
            ift = pages.get(other_file.pageId, None)
            if ift is None:
                self._base_logger.warning(f"no file for page {other_file.pageId} "
                                          f"in input file group {input_grp}")
                continue
            if ift[1]:
                # fileGrp has multiple files for this page ID
                if other_file.mimetype == MIMETYPE_PAGE or ift[1].mimetype == MIMETYPE_PAGE:
                    self._base_logger.debug(f"another PAGE file {other_file.ID} for page {other_file.pageId} "
                                            f"in input file group {other_grp}")
                    raise NonUniqueInputFile(other_grp, other_file.pageId, None)
                # more than 1 plaintext file on other side
                self._base_logger.debug(f"adding another file {other_file.ID} for page {other_file.pageId} "
                                        f"from input file group {other_grp}")
                ift.append(other_file)
            else:
                self._base_logger.debug(f"adding file {other_file.ID} for page {other_file.pageId} "
                                        f"from input file group {other_grp}")
                ift[1] = other_file
        # Warn if no files found but pageId was specified, because that might be due to invalid page_id (range)
        if self.page_id and not any(pages):
            self._base_logger.critical(f"Could not find any files for selected pageId {self.page_id}.\n"
                                       f"compare '{self.page_id}' with the output of 'orcd workspace list-page'.")
        ifts = []
        for page, ifiles in pages.items():
            if not ifiles[1]:
                self._base_logger.error(f'Found no file for page {page} in file group {other_grp}')
                if config.OCRD_MISSING_INPUT == 'abort':
                    raise MissingInputFile(other_grp, page, mimetype)
                continue
            ifts.append(tuple(ifiles))
        return ifts

    def process_workspace(self, workspace: Workspace) -> None:
        self.stats = mp.Manager().dict(all_confs=[], all_match=0, all_total=0)
        super().process_workspace(workspace)
        if len(self.stats['all_confs']):
            self.logger.info("average alignment accuracy overall: %d%%",
                             100 * sum(self.stats['all_confs']) / len(self.stats['all_confs']))
        if self.stats['all_total']:
            self.logger.info("coverage of matching lines overall: %d%%",
                             100 * self.stats['all_match'] / self.stats['all_total'])

    def process_page_file(self, *input_files : Optional[OcrdFileType]) -> None:
        """Force-align the textlines text of both inputs for each page,
        then insert the 2nd into the 1st.

        Find file pairs in both input file groups of the workspace
        for the same page IDs.

        Open and deserialize PAGE input files, then iterate over
        the element hierarchy down to the TextLine level, looking
        at each first TextEquiv. (If the second input has no TextLines,
        but newline-separated TextEquiv at the TextRegion level, then
        use these instead. If either side has no lines, then skip
        that page.)

        Align character sequences in all pairs of lines for any
        combination of textlines from either side.

        If ``normalization`` is non-empty, then apply each of these regex
        replacements to both sides before comparison.

        Then iteratively search the next closest match pair. Remember
        the assigned result as mapping from first to second fileGrp.

        When all lines of the second fileGrp have been assigned,
        or the ``cutoff_dist`` has been reached, apply the mapping
        by inserting each line from the second fileGrp into position
        0 (and `@index=0`) at the first fileGrp. Also mark the inserted
        TextEquiv via `@dataType=other` and `@dataTypeDetails=GRP`.

        (Unmatched or cut off lines will stay unchanged, except for
        their `@index` now starting at 1.)

        If ``allow_splits`` is true, then for each long bad match, spend
        some extra time searching for subsegmentation candidates, i.e.
        a sequence of multiple lines from the first fileGrp aligning
        with a single line from the second fileGrp. When such a sequence
        outscores the bad match, prefer the concatenated sequence over
        the single match when inserting results.

        Produce a new PAGE output file by serialising the resulting hierarchy.
        """
        input_tuple : List[Optional[Union[OcrdPage,str]]] = [None] * len(input_files)
        page_id = input_files[0].pageId
        self._base_logger.info("processing page %s", page_id)
        for i, input_file in enumerate(input_files):
            assert isinstance(input_file, get_args(OcrdFileType))
            self._base_logger.debug(f"parsing file {input_file.ID} for page {page_id}")
            try:
                if input_file.mimetype == MIMETYPE_PAGE:
                    page_ = page_from_file(input_file)
                    assert isinstance(page_, OcrdPage)
                    input_tuple[i] = page_
                else:
                    input_tuple[i] = input_file.local_filename
            except ValueError as err:
                # not PAGE and not an image to generate PAGE for
                self._base_logger.error(f"non-PAGE input for page {page_id}: {err}")
        output_file_id = make_file_id(input_files[0], self.output_file_grp)
        output_file = next(self.workspace.mets.find_files(ID=output_file_id), None)
        if output_file and config.OCRD_EXISTING_OUTPUT != 'OVERWRITE':
            # short-cut avoiding useless computation:
            raise FileExistsError(
                f"A file with ID=={output_file_id} already exists {output_file} and neither force nor ignore are set"
            )
        input_file_grp, other_file_grp = self.input_file_grp.split(',')

        pcgts = input_tuple[0]
        page = pcgts.get_Page()
        lines = page.get_AllTextLines()
        if not len(lines):
            self.logger.warning("no text lines on page %s of 1st input", page_id)
            return
        texts = list(map(page_element_unicode0, lines))
        if isinstance(input_tuple[1], OcrdPage):
            other_pcgts = input_tuple[1]
            other_page = other_pcgts.get_Page()
            other_lines = other_page.get_AllTextLines()
            if len(other_lines):
                other_texts = list(map(page_element_unicode0, other_lines))
            else:
                # no textline level in 2nd input: try region level with newlines
                self.logger.warning("no text lines on page %s for 2nd input, trying newline-separeted text regions", page_id)
                # keep whole regions to be subsegmented,
                # or split lines, or full page?
                other_texts = list(chain.from_iterable([
                    page_element_unicode0(region).split('\r\n')
                    for region in other_page.get_AllRegions(classes=['Text'])]))
        else:
            other_texts = []
            for other_filename in sorted(input_tuple[1:]):
                with open(other_filename, 'r') as other_file:
                    other_texts.extend(other_file.read().splitlines())
            other_lines = [TextLineType(id="line%04d"%i,
                                        TextEquiv=[TextEquivType(Unicode=line)])
                           for i, line in enumerate(other_texts)]
        if not len(other_texts):
            self.logger.error("no text lines on page %s of 2nd input", page_id)
            return
        # calculate assignments and scores
        res, dst = align.match(texts, other_texts, workers=1,
                               normalization=self.parameter['normalization'],
                               try_subseg=self.parameter['allow_splits'])
        if self.parameter['allow_splits']:
            res_ind, res_beg, res_end = res
        else:
            res_ind = res
        for other_ind in set(range(len(other_texts))).difference(res_ind):
            self.logger.warning("no match for %s on page %s", other_lines[other_ind].id, page_id)
        page_confs = []
        page_match = 0
        page_total = 0
        for ind, other_ind in enumerate(res_ind):
            line = lines[ind]
            for n, textequiv in enumerate(line.TextEquiv or [], 1):
                textequiv.index = n # increment @index of existing TextEquivs
            if len(other_lines):
                other_line = other_lines[other_ind]
            else:
                # no textline level in 2nd input, only region level newline-split:
                # create pseudo-line
                other_text = other_texts[other_ind]
                other_line = TextLineType(id="line%04d" % other_ind,
                                          TextEquiv=[TextEquivType(Unicode=other_text)])
            page_total += 1
            if other_ind < 0:
                self.logger.warning("unmatched line %s on page %s", line.id, page_id)
                continue
            page_match += 1
            textequiv = TextEquivType()
            textequiv.index = 0
            textequiv.conf = dst[ind]
            textequiv.Unicode = page_element_unicode0(other_line)
            if self.parameter['allow_splits'] and res_beg[ind] >= 0 and res_end[ind] >= 0:
                other_line.id += "[%d:%d]" % (res_beg[ind], res_end[ind])
                textequiv.Unicode = textequiv.Unicode[res_beg[ind]:res_end[ind]]
            textequiv.dataType = 'other'
            textequiv.dataTypeDetails = other_file_grp + '/' + other_line.id
            self.logger.debug("matching line %s vs %s [%d%%]", line.id, other_line.id, 100 * dst[ind])
            line.insert_TextEquiv_at(0, textequiv) # update
            page_confs.append(dst[ind])
        if len(page_confs):
            self.logger.info("average alignment accuracy for page %s: %d%%", page_id, 100 * sum(page_confs) / len(page_confs))
        if page_total:
            self.logger.info("coverage of matching lines for page %s: %d%%", page_id, 100 * page_match / page_total)

        self.stats['all_confs'].extend(page_confs)
        self.stats['all_match'] += page_match
        self.stats['all_total'] += page_total

        page_update_higher_textequiv_levels('line', pcgts)
        page_remove_lower_textequiv_levels('line', pcgts)
        # or metadata from other_pcgts (GT)?
        pcgts.set_pcGtsId(output_file_id)
        self.add_metadata(pcgts)
        self.workspace.add_file(
            file_id=output_file_id,
            file_grp=self.output_file_grp,
            page_id=page_id,
            local_filename=os.path.join(self.output_file_grp, output_file_id + '.xml'),
            mimetype=MIMETYPE_PAGE,
            content=to_xml(pcgts),
        )

# from ocrd_tesserocr
def page_element_unicode0(element):
    """Get Unicode string of the first text result."""
    if element.get_TextEquiv():
        return element.get_TextEquiv()[0].Unicode or ''
    else:
        return ''

def page_element_conf0(element):
    """Get confidence (as float value) of the first text result."""
    if element.TextEquiv:
        return 1.0 if element.TextEquiv[0].conf is None else element.TextEquiv[0].conf
    return 1.0

def page_get_reading_order(ro, rogroup):
    """Add all elements from the given reading order group to the given dictionary.
    
    Given a dict ``ro`` from layout element IDs to ReadingOrder element objects,
    and an object ``rogroup`` with additional ReadingOrder element objects,
    add all references to the dict, traversing the group recursively.
    """
    regionrefs = list()
    if isinstance(rogroup, (OrderedGroupType, OrderedGroupIndexedType)):
        regionrefs = (rogroup.get_RegionRefIndexed() +
                      rogroup.get_OrderedGroupIndexed() +
                      rogroup.get_UnorderedGroupIndexed())
    if isinstance(rogroup, (UnorderedGroupType, UnorderedGroupIndexedType)):
        regionrefs = (rogroup.get_RegionRef() +
                      rogroup.get_OrderedGroup() +
                      rogroup.get_UnorderedGroup())
    for elem in regionrefs:
        ro[elem.get_regionRef()] = elem
        if not isinstance(elem, (RegionRefType, RegionRefIndexedType)):
            page_get_reading_order(ro, elem)

def page_update_higher_textequiv_levels(level, pcgts, overwrite=True):
    """Update the TextEquivs of all PAGE-XML hierarchy levels above ``level`` for consistency.
    
    Starting with the lowest hierarchy level chosen for processing,
    join all first TextEquiv.Unicode (by the rules governing the respective level)
    into TextEquiv.Unicode of the next higher level, replacing them.
    If ``overwrite`` is false and the higher level already has text, keep it.
    
    When two successive elements appear in a ``Relation`` of type ``join``,
    then join them directly (without their respective white space).
    
    Likewise, average all first TextEquiv.conf into TextEquiv.conf of the next higher level.
    
    In the process, traverse the words and lines in their respective ``readingDirection``,
    the (text) regions which contain lines in their respective ``textLineOrder``, and
    the (text) regions which contain text regions in their ``ReadingOrder``
    (if they appear there as an ``OrderedGroup``).
    Where no direction/order can be found, use XML ordering.
    
    Follow regions recursively, but make sure to traverse them in a depth-first strategy.
    """
    page = pcgts.get_Page()
    relations = page.get_Relations() # get RelationsType
    if relations:
        relations = relations.get_Relation() # get list of RelationType
    else:
        relations = []
    joins = list() # 
    for relation in relations:
        if relation.get_type() == 'join': # ignore 'link' type here
            joins.append((relation.get_SourceRegionRef().get_regionRef(),
                          relation.get_TargetRegionRef().get_regionRef()))
    reading_order = dict()
    ro = page.get_ReadingOrder()
    if ro:
        page_get_reading_order(reading_order, ro.get_OrderedGroup() or ro.get_UnorderedGroup())
    if level != 'region':
        for region in page.get_AllRegions(classes=['Text']):
            # order is important here, because regions can be recursive,
            # and we want to concatenate by depth first;
            # typical recursion structures would be:
            #  - TextRegion/@type=paragraph inside TextRegion
            #  - TextRegion/@type=drop-capital followed by TextRegion/@type=paragraph inside TextRegion
            #  - any region (including TableRegion or TextRegion) inside a TextRegion/@type=footnote
            #  - TextRegion inside TableRegion
            subregions = region.get_TextRegion()
            if subregions: # already visited in earlier iterations
                # do we have a reading order for these?
                # TODO: what if at least some of the subregions are in reading_order?
                if (all(subregion.id in reading_order for subregion in subregions) and
                    isinstance(reading_order[subregions[0].id], # all have .index?
                               (OrderedGroupType, OrderedGroupIndexedType))):
                    subregions = sorted(subregions, key=lambda subregion:
                                        reading_order[subregion.id].index)
                region_unicode = page_element_unicode0(subregions[0])
                for subregion, next_subregion in zip(subregions, subregions[1:]):
                    if (subregion.id, next_subregion.id) not in joins:
                        region_unicode += '\n' # or '\f'?
                    region_unicode += page_element_unicode0(next_subregion)
                region_conf = sum(page_element_conf0(subregion) for subregion in subregions)
                region_conf /= len(subregions)
            else: # TODO: what if a TextRegion has both TextLine and TextRegion children?
                lines = region.get_TextLine()
                if ((region.get_textLineOrder() or
                     page.get_textLineOrder()) ==
                    TextLineOrderSimpleType.BOTTOMTOTOP):
                    lines = list(reversed(lines))
                if level != 'line':
                    for line in lines:
                        words = line.get_Word()
                        if ((line.get_readingDirection() or
                             region.get_readingDirection() or
                             page.get_readingDirection()) ==
                            ReadingDirectionSimpleType.RIGHTTOLEFT):
                            words = list(reversed(words))
                        if level != 'word':
                            for word in words:
                                glyphs = word.get_Glyph()
                                if ((word.get_readingDirection() or
                                     line.get_readingDirection() or
                                     region.get_readingDirection() or
                                     page.get_readingDirection()) ==
                                    ReadingDirectionSimpleType.RIGHTTOLEFT):
                                    glyphs = list(reversed(glyphs))
                                word_unicode = ''.join(page_element_unicode0(glyph) for glyph in glyphs)
                                word_conf = sum(page_element_conf0(glyph) for glyph in glyphs)
                                if glyphs:
                                    word_conf /= len(glyphs)
                                if not word.get_TextEquiv() or overwrite:
                                    word.set_TextEquiv( # replace old, if any
                                        [TextEquivType(Unicode=word_unicode, conf=word_conf)])
                        line_unicode = ' '.join(page_element_unicode0(word) for word in words)
                        line_conf = sum(page_element_conf0(word) for word in words)
                        if words:
                            line_conf /= len(words)
                        if not line.get_TextEquiv() or overwrite:
                            line.set_TextEquiv( # replace old, if any
                                [TextEquivType(Unicode=line_unicode, conf=line_conf)])
                region_unicode = ''
                region_conf = 0
                if lines:
                    region_unicode = page_element_unicode0(lines[0])
                    for line, next_line in zip(lines, lines[1:]):
                        words = line.get_Word()
                        next_words = next_line.get_Word()
                        if not(words and next_words and (words[-1].id, next_words[0].id) in joins):
                            region_unicode += '\n'
                        region_unicode += page_element_unicode0(next_line)
                    region_conf = sum(page_element_conf0(line) for line in lines)
                    region_conf /= len(lines)
            if not region.get_TextEquiv() or overwrite:
                region.set_TextEquiv( # replace old, if any
                    [TextEquivType(Unicode=region_unicode, conf=region_conf)])

def page_remove_lower_textequiv_levels(level, pcgts):
    page = pcgts.Page
    if level == 'region':
        for region in page.get_AllRegions(classes=['Text']):
            region.TextEquiv = []
    else:
        for line in page.get_AllTextLines():
            if level == 'line':
                line.Word = []
            else:
                for word in line.Word or []:
                    if level == 'word':
                        word.Glyph = []
                    else:
                        for glyph in word.Glyph:
                            glyph.Graphemes = []

@click.command()
@ocrd_cli_options
def ocrd_nmalign_merge(*args, **kwargs):
    return ocrd_cli_wrap_processor(NMAlignMerge, *args, **kwargs)
