# pylint: disable=import-error

import os
import json
import logging
import numpy as np
import pytest

from ocrd import run_processor
from ocrd_utils import MIMETYPE_PAGE, make_file_id, config
from ocrd_models.constants import NAMESPACES as NS
from ocrd_modelfactory import page_from_file

from nmalign.ocrd.cli import NMAlignMerge

NRM = {
    " *\\n": " ",
    "ſ": "s",
    "a\u0364": "ä",
    "o\u0364": "ö",
    "u\u0364": "ü",
    "A\u0364": "Ä",
    "O\u0364": "Ö",
    "U\u0364": "Ü",
    "([^\\\\W\\s])(\\\\w)": "\\\\1 \\\\2"
}

def test_ocrd(workspace, subtests, caplog):
    caplog.set_level(logging.INFO)
    def only_align(logrec):
        return logrec.name == 'ocrd.processor.NMAlignMerge'
    ws, page_id = workspace
    pages = page_id.split(',')
    def page_order(file_):
        return pages.index(file_.pageId)
    grp0 = 'OCR-D-GT-PAGE'
    # get reference input files in order of pages
    inputs = list(sorted(ws.find_files(file_grp=grp0,
                                       mimetype=MIMETYPE_PAGE,
                                       page_id=page_id),
                         key=page_order))
    rtexts = [[textequiv
               for textequiv in page_from_file(input_).etree.xpath(
                       "//page:TextLine/page:TextEquiv[1]", namespaces=NS)]
              for input_ in inputs]
    rlines_short = [] # allow non-matches for these
    for page, rlines in zip(pages, rtexts):
        for rline in rlines:
            rstr = rline.find('page:Unicode', namespaces=NS).text
            assert len(rstr) > 0, rline.getparent().get('id')
            if len(rstr) <= 4:
                rlines_short.append((rline.getparent().get('id'), page))
    grps = [grp for grp in ws.mets.file_groups
            if 'OCR-D-OCR-' in grp]
    for other_file_grp in grps:
        # get other input files in order of pages
        inputs = list(sorted(ws.find_files(file_grp=other_file_grp,
                                           mimetype=MIMETYPE_PAGE,
                                           page_id=page_id),
                             key=page_order))
        itexts = [[textequiv
                   for textequiv in page_from_file(input_).etree.xpath(
                           "//page:TextLine/page:TextEquiv[1]", namespaces=NS)]
                  for input_ in inputs]
        # OCR line text can be empty (will be ignored during merge)
        # for ilines in itexts:
        #     for iline in ilines:
        #         istr = iline.find('page:Unicode', namespaces=NS).text
        #         assert len(istr) > 0, iline.getparent().get('id')
        input_file_grp = grp0 + ',' + other_file_grp
        output_file_grp = other_file_grp + '-SEG-GT'
        for mode in ["pagexml", "plaintext"]:
            if mode == "plaintext":
                input_file_grp += '-LINES'
                # first extract line .txt files (as ocrd-segment-extract-lines would)
                for ifile, ilines in zip(inputs, itexts):
                    for i, iline in enumerate(ilines, start=1):
                        fileGrp = other_file_grp + '-LINES'
                        file_id = make_file_id(ifile, fileGrp) + '_%04d' % i
                        ws.add_file(fileGrp,
                                    content=iline.find('page:Unicode', namespaces=NS).text,
                                    page_id=ifile.pageId,
                                    file_id=file_id,
                                    local_filename=os.path.join(fileGrp, file_id + '.txt'),
                                    mimetype='text/plain')
                config.OCRD_EXISTING_OUTPUT = 'OVERWRITE'
            with subtests.test(
                    input_file_grp=input_file_grp,
                    mode=mode):
                with caplog.filtering(only_align):
                    run_processor(
                        NMAlignMerge,
                        input_file_grp=input_file_grp,
                        output_file_grp=output_file_grp,
                        parameter=dict(normalization=NRM,
                                       allow_splits=True),
                        workspace=ws,
                        page_id=page_id,
                    )
                # too strict:
                # - one accuracy and one coverage msg per page
                # - one coverage msg overall:
                # assert len(caplog.records) == len(pages) * 2 + 1
                for logrec in caplog.records:
                    if "average alignment accuracy" in logrec.message:
                        continue
                    if "coverage of matching lines" in logrec.message:
                        continue
                    if "skipping empty line" in logrec.message:
                        continue
                    if "unmatched line" in logrec.message:
                        line_id, page = logrec.message.split()[2::3]
                        assert (line_id, page) in rlines_short
                        continue
                    if "coverage of matching lines" in logrec.message:
                        #assert logrec.message.endswith("100%")
                        assert int(logrec.message.split()[-1][:-1]) >= 95
                        continue
                    assert logrec.levelno < logging.INFO, logrec
                caplog.clear()
                ws.save_mets()
                assert os.path.isdir(os.path.join(ws.directory, output_file_grp))
                results = list(sorted(ws.find_files(file_grp=output_file_grp,
                                                    mimetype=MIMETYPE_PAGE),
                                      key=page_order))
                assert len(results), "found no output PAGE files"
                assert len(results) == len(pages)
                result1 = results[0]
                assert os.path.exists(result1.local_filename), "result for first page not found in filesystem"
                otexts = [[textequiv
                           for textequiv in page_from_file(result).etree.xpath(
                                   "//page:TextLine/page:TextEquiv[1]", namespaces=NS)]
                          for result in results]
                for page, rlines, olines in zip(pages, rtexts, otexts):
                    assert len(rlines) == len(olines)
                    for rline, oline in zip(rlines, olines):
                        rstr = rline.find('page:Unicode', namespaces=NS).text
                        ostr = oline.find('page:Unicode', namespaces=NS).text
                        rlid = rline.getparent().get('id')
                        olid = oline.getparent().get('id')
                        diag = ({rlid: rstr}, {olid: ostr})
                        assert oline.get('index') == '0' or (rlid, page) in rlines_short, diag
                        assert oline.get('dataType') == 'other' or (rlid, page) in rlines_short, diag
                        diag += ({oline.get('dataTypeDetails'): oline.get('conf')},)
                        # too strict: remaining lines typically have very low score
                        # (they only match well due to local relative order)
                        #assert float(oline.get('conf')) > 0.5, diag
                tree1 = page_from_file(result1).etree
                line1 = tree1.xpath(
                    "//page:TextLine[page:TextEquiv/page:Unicode[contains(text(),'Aufklärung') or contains(text(),'Aufklaͤrung')]]",
                    namespaces=NS,
                )
                assert len(line1) >= 1, "result is inaccurate"
                line1 = line1[0]
                line1_text = line1.xpath("page:TextEquiv[1]/page:Unicode/text()", namespaces=NS)[0]
                words = line1.xpath(".//page:Word", namespaces=NS)
                assert len(words) == 0
    
# fixme: test script, test API directly
