# pylint: disable=import-error

import os
import json
import numpy as np
import pytest

from ocrd import run_processor
from ocrd_utils import MIMETYPE_PAGE
from ocrd_models.constants import NAMESPACES as NS
from ocrd_modelfactory import page_from_file

from nmalign.ocrd.cli import NMAlignMerge

def test_pagexml(workspace, subtests):
    ws, page_id = workspace
    pages = page_id.split(',')
    page1 = pages[0]
    grp0 = 'OCR-D-GT-PAGE'
    grps = [grp for grp in ws.mets.file_groups
            if 'OCR-D-OCR-' in grp]
    for other_file_grp in grps:
        inputs = list(ws.find_files(file_grp=other_file_grp, mimetype=MIMETYPE_PAGE))
        itexts = [str(text) for input_ in inputs
                  for text in page_from_file(input_).etree.xpath(
                          "//page:TextLine/page:TextEquiv/page:Unicode", namespaces=NS)]
        ilengths = [len(text) for text in itexts]
        for length in ilengths:
            assert 0 < length
        input_file_grp = grp0 + ',' + other_file_grp
        output_file_grp = other_file_grp + '-SEG-GT'
        with subtests.test(
                msg="test forced alignment",
                input_file_grp=input_file_grp):
            run_processor(
                NMAlignMerge,
                input_file_grp=input_file_grp,
                output_file_grp=output_file_grp,
                parameter=dict(normalization={
                    " *\\n": " ",
                    "ſ": "s",
                    "a\u0364": "ä",
                    "o\u0364": "ö",
                    "u\u0364": "ü",
                    "A\u0364": "Ä",
                    "O\u0364": "Ö",
                    "U\u0364": "Ü",
                    "([^\\\\W\\s])(\\\\w)": "\\\\1 \\\\2"},
                               allow_splits=True),
                workspace=ws,
                page_id=page_id,
            )
            ws.save_mets()
            assert os.path.isdir(os.path.join(ws.directory, output_file_grp))
            results = list(ws.find_files(file_grp=output_file_grp, mimetype=MIMETYPE_PAGE))
            assert len(results), "found no output PAGE files"
            assert len(results) == len(pages)
            result1 = results[0]
            assert os.path.exists(result1.local_filename), "result for first page not found in filesystem"
            otexts = [str(text) for result in results
                      for text in page_from_file(result).etree.xpath(
                              "//page:TextLine/page:TextEquiv/page:Unicode", namespaces=NS)]
            olengths = [len(text) for text in otexts]
            for length in olengths:
                assert 0 < length
            for ilength, olength in zip(ilengths, olengths):
                assert olength == pytest.approx(ilength, rel=0.1)
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
    
# todo: test PAGE vs extracted line plaintexts
