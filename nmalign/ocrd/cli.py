import os
import json
from itertools import chain
from pkg_resources import resource_string
import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from ocrd import Processor
from ocrd_utils import (
    getLogger,
    make_file_id,
    assert_file_grp_cardinality,
    MIMETYPE_PAGE
)
from ocrd_modelfactory import page_from_file
from ocrd_models.ocrd_page import (
    TextEquivType,
    RegionRefType,
    RegionRefIndexedType,
    OrderedGroupType,
    OrderedGroupIndexedType,
    UnorderedGroupType,
    UnorderedGroupIndexedType,
    to_xml
)
from ocrd_models.ocrd_page_generateds import (
    ReadingDirectionSimpleType,
    TextLineOrderSimpleType
)

from ..lib import align

OCRD_TOOL = json.loads(resource_string(__name__, 'ocrd-tool.json').decode('utf8'))
TOOL = 'ocrd-nmalign-merge'

class NMAlignMerge(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools'][TOOL]
        kwargs['version'] = OCRD_TOOL['version']
        super().__init__(*args, **kwargs)

    def process(self):
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

        Then iteratively search the next closest match pair. Remember
        the assigned result as injective mapping from first to second
        fileGrp.

        When all lines of the first fileGrp have been assigned,
        or the ``cutoff_dist`` has been reached, apply the mapping
        by inserting each line from the second fileGrp into position
        0 (and `@index=0`) at the first fileGrp. Also mark the inserted
        TextEquiv via `@dataType=other` and `@dataTypeDetails=GRP`.

        (Unmatched or cut off lines will stay unchanged, except for
        their `@index=1` asf.)

        Produce a new PAGE output file by serialising the resulting hierarchy.
        """
        LOG = getLogger('processor.NMAlignMerge')
        assert_file_grp_cardinality(self.input_file_grp, 2)
        assert_file_grp_cardinality(self.output_file_grp, 1)

        input_file_grp, other_file_grp = self.input_file_grp.split(",")
        ifts = self.zip_input_files(mimetype=MIMETYPE_PAGE) # input file tuples
        for n, ift in enumerate(ifts):
            input_file, other_file = ift
            file_id = make_file_id(input_file, self.output_file_grp)
            page_id = input_file.pageId or input_file.ID
            LOG.info("INPUT FILE %i / %s", n, page_id)
            pcgts = page_from_file(self.workspace.download_file(input_file))
            pcgts.set_pcGtsId(file_id)
            self.add_metadata(pcgts)
            # or metadata from other_pcgts (GT)?
            page = pcgts.get_Page()
            lines = page.get_AllTextLines()
            if not len(lines):
                LOG.warning("no text lines on page %s of 1st input", page_id)
                continue
            texts = list(map(page_element_unicode0, lines))
            other_pcgts = page_from_file(self.workspace.download_file(other_file))
            other_page = other_pcgts.get_Page()
            other_lines = other_page.get_AllTextLines()
            other_texts = list(map(page_element_unicode0, other_lines))
            if not len(other_texts):
                # no textline level in 2nd input: try region level with newlines
                other_texts = list(chain.from_iterable(
                    [text.split('\r\n') for text in region.get_TextEquiv()[0].Unicode]))
            if not len(other_texts):
                LOG.error("no text lines on page %s of 2nd input", page_id)
                continue
            # calculate assignments and scores
            res, dst = align.match(texts, other_texts, workers=1)
            for other_ind in set(range(len(other_texts))).difference(res):
                LOG.warning("no match for %s on page %s", other_lines[other_ind].id, page_id)
            for ind, other_ind in enumerate(res):
                line = lines[ind]
                for n, textequiv in enumerate(line.TextEquiv or [], 1):
                    textequiv.index = n
                if other_ind < 0:
                    LOG.warning("unmatched line %s on page %s", line.id, page_id)
                else:
                    other_line = other_lines[other_ind]
                    LOG.debug("matching line %s vs %s [%d%%]", line.id, other_line.id, dst[ind])
                    textequiv = other_line.TextEquiv[0]
                    textequiv.index = 0
                    textequiv.dataType = 'other'
                    textequiv.dataTypeDetails = other_file_grp + '/' + other_line.id
                    line.insert_TextEquiv_at(0, textequiv)

            page_update_higher_textequiv_levels('line', pcgts)
            self.workspace.add_file(
                ID=file_id,
                file_grp=self.output_file_grp,
                pageId=input_file.pageId,
                mimetype=MIMETYPE_PAGE,
                local_filename=os.path.join(self.output_file_grp,
                                            file_id + '.xml'),
                content=to_xml(pcgts))

# from ocrd_tesserocr
def page_element_unicode0(element):
    """Get Unicode string of the first text result."""
    if element.get_TextEquiv():
        return element.get_TextEquiv()[0].Unicode or ''
    else:
        return ''

def page_element_conf0(element):
    """Get confidence (as float value) of the first text result."""
    if element.get_TextEquiv():
        # generateDS does not convert simpleType for attributes (yet?)
        return float(element.get_TextEquiv()[0].conf or "1.0")
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

@click.command()
@ocrd_cli_options
def ocrd_nmalign_merge(*args, **kwargs):
    return ocrd_cli_wrap_processor(NMAlignMerge, *args, **kwargs)
