[![PyPI version](https://badge.fury.io/py/nmalign.svg)](https://badge.fury.io/py/nmalign)

# nmalign

    forced alignment of lists of string by fuzzy string matching
    
  * [Introduction](#introduction)
  * [Installation](#installation)
  * [Usage](#usage)
     * [standalone command-line interface nmalign](#standalone-command-line-interface-nmalign)
     * [OCR-D processor interface ocrd-nmalign-merge](#ocr-d-processor-interface-ocrd-nmalign-merge)
  * [Open Tasks](#open-tasks)

## Introduction

This offers **forced alignment** of textlines by fuzzy string matching.
(The implementation is based on [rapidfuzz cdist](https://maxbachmann.github.io/RapidFuzz/Usage/process.html#cdist).)

It combines all pairs of strings (i.e. text lines) from either side,
calculates their edit distance (assuming some of them are very similar),
and assigns an injective mapping from one side to the other by iteratively
selecting those pairs which have the next-smallest distance (and taking
them out of the search).

This can be used in OCR settings to align lines when you have different
segmentation. For example, often ground truth data is only transcribed on
the page level, but OCR results are available on the line level with precise
coordinates. If GT and OCR text are close enough to each other, you could then
map the GT text to the predicted coordinates.

It offers:
- an API (`nmalign.match`)
- a standalone CLI (for strings / text files / list files)
- an [OCR-D](https://ocr-d.de) compliant [workspace processor](https://ocr-d.de/en/spec/cli) (for [METS-XML](https://ocr-d.de/en/spec/mets)/[PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents)


## Installation

Create and activate a [virtual environment](https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments) as usual.

To install Python dependencies:

    pip install -r requirements.txt

To install this module (along with Python dependencies), do:

    pip install .

## Usage

### standalone command-line interface `nmalign`


```
Usage: nmalign [OPTIONS]

  Force-align two lists of strings.

  Computes string alignments between each pair among l1 and l2. Then iteratively
  searches the next closest pair. Stores the assigned result as injective
  mapping from l1 to l2. (Unmatched or cut off elements will be assigned -1.)

  Prints the corresponding list indices and match scores [0,100] as CSV data.

list to be replaced: [exactly 1 required]
  --strings1 TUPLE               as strings
  --files1 TUPLE                 as file paths of strings
  --filelist1 FILENAME           as text file with file paths of strings

list of replacements: [exactly 1 required]
  --strings2 TUPLE               as strings
  --files2 TUPLE                 as file paths of strings
  --filelist2 FILENAME           as text file with file paths of strings

Other options:
  -j, --processes INTEGER RANGE  number of processes to run in parallel
                                 [1<=x<=32]
  -s, --show-strings             print strings themselves instead of indices
  -f, --show-files               print file names themselves instead of indices
  -S, --separator TEXT           print this string between result columns
                                 (default: tab)
  --help                         Show this message and exit.
```

For example:

<details><summary>file input, index output</summary>
<p>

```
nmalign --files1 GT.SELECTED/FILE_0094_*.gt.txt --files2 GT/FILE_0094_*.gt.txt
0    -1    0.0
1    -1    0.0
2    0    91.78082
3    1    100.0
4    2    90.90909
5    3    95.945946
6    4    95.588234
7    5    89.85507
8    6    92.64706
9    7    92.10526
10    8    93.84615
11    9    89.61039
12    10    89.85507
13    11    89.189186
14    12    92.0
15    13    96.969696
16    14    95.38461
17    15    90.41096
18    16    91.25
19    17    96.1039
20    18    95.89041
21    19    93.50649
22    20    93.333336
23    21    92.68293
24    22    88.6076
25    23    95.652176
26    24    92.85714
27    25    71.014496
28    26    92.753624
29    27    94.5946
30    28    80.0
31    29    89.393936
32    30    83.333336
33    31    97.01492
34    32    94.366196
35    33    89.333336
36    34    100.0
37    35    95.588234
38    36    92.0
39    37    87.5
40    38    91.54929
41    39    92.85714
42    40    90.0
```

</p>
</details>
<details><summary>file input, string output</summary>
<p>

```
zo ??o wbohim wotpalenym we jich nuzy a p??chi natwarjenju ze w??ch??ch ??tro???	zo ??o wbohim wotpalenym we jih nuzy a pihi natwarjenju ze w??chech ftro-	91.78082
now a podwolnje pomha??che.	now a podwolnje pomha??che.	100.0
We l??c??e w??jny mjez pru??kim kralom a raku??kim kh????orom 1866 na 13.	We l??cze w??jny mjez pru??kim kralom a raku??tim khezorom 1866 na 13.	90.90909
januara rano we 4 hod??inach wozjewi ??o we drjewjanej kh????cy we Filipsdorfu	januara rano we 4 hodzinach wozjewi ??o we drjewjanej khezcy we Filipsdorfu	95.945946
pola Rumburka Mac?? Bo??a khorej knje??nje Madlenje Kadec, jej prajicy:	pola Rumburka Macz Boza khorej knjeznje Madlenje Kadec, jej prajicy:95.588234
???Moje d????c??o, z n??tka za??ije" (twoja bolaca rana). We Filipsdorfu na???	???Moje dz??czo, z n??tka zazije??? (twoja bolaca rana). We Filipsdorfu na-	89.85507
twari ??o wot l??ta 1870 z darow pobo??nych w??riwych wulka rjana cyrkej	twari ??o wot leta 1870 z darow pobozuych weriwych wulka rjana eyrkej92.64706
a Serbja k ??wj. Marji tam rad puc??uja.	a Serbja ?? fwj. Marji tam rad puczuja.	92.10526
Do Rumburka (1 hod??inu wot Filipsdorfa daloko) Serbja hi??om dl??he	Do Rumburka (1 hodjinu wot Filipsdorfa daloko) Serbia hijom dlehe	93.84615
hac?? 100 l??t na porciunkulu (na 1. a 2. augu??c??e) k kapucinarjam z proce????io???	haci 100 ??et na porciunkulu (na 1. a 2. auqu??cze) ?? kapucinarjam z proce????iv-	89.61039
nom khod??a: do ??tareje a noweje Krupki we C??echach (k c??e??pjacomu J?????	nom khodja: do ??tareje a noweje Krupki we Czechach (f czetpjacomu J??-	89.85507
zu??ej na ??wjatym ??khod??e a k bolo??c??iwej Mac??eri Bo??ej) dw??jcy za l??to, na	zu??ej na ??wjatym ??khodze a ?? bolo??cziwej Maczeri Bozej) dw??jcy za Leto, na	89.189186
??wjatki a na ??wj. d??e?? Marijnoho naroda (8. ??eptembra), te?? tak do??ho. Pr?????	??wjatki a na fwj. dze?? Marijnoho naroda (8. ??eptembra), te?? tak dolho. Pre-	92.0
nja ??erb??ka putnica do Krupki b?? w????ta Korchowa z Nowo??lic (1754).	nja ??erb??ka putnica do Krupki be we??ta Korchowa z Nowo??lic (1754).	96.969696
Hdy?? we ??eptembrje 1865 ??erb??ki proce????ion do Krupki d??????che a do	Hdyi we ??eptembrje 1865 ??erb??ki proce????ion do Krupki dze??che a do	95.38461
m????tac??ka Gottleuby p??chi??d??e, hanjachu a wu??m??chowachu pobo??nych Serbow.	mi??taczka Gottleuby p??chindze, hanjachu a wu??m??chowachu pobozuych Serbow.	90.41096
Kr??tki c??as na to, na 4. oktobrje 1865, wulki d????l m????tac??ka ??o wotpali. M??yn??ki	Kr??tki czas na to, na 4. oktobrje 1865, wulki dzel m????taczka ??o wotpali. Mtyn??ei	91.25
mi??chtr k. Jurij Wawrik z Khanjec, kotry?? b?? p??chi proce????ionje poby??, nahro???	mi??chtr k. Jurij Wawrik z Khanjec, kotryz be p??chi proce????ionje pobyk, nahro???	96.1039
mad??i za wotpalenych mjez Serbami 110 toleri a p??chip??????a je do Gottleuby	madzi za wotpalenych mjez Serbami 110 toleri a p??chip????ta je do Gottleuby	95.89041
z li??tom: ???Dar lubo??c??e za wotpalenych wot kathol??kich Serbow, ki?? k????de l??to	z li??tom: ???Dar lubo??cze za wotpalenych wot kathol??kich Serbow, kiz k??zde l??to	93.50649
p??chez Gottleubu do Krupki puc??uja." Hdy?? ??erb??ki proce????ion we ??c??ehowacym	p??chez Gottleubu do Krupki puczuja.??? Hdyz ??erb??ki proce????ion we ??czehowaeym	93.333336
l??c??e 1866 ??o za??y Gottleubje p??chibli??i, c??ehnjechu jomu m????chc??ano??ta, luther??ki	l??cze 1866 ??o za??y Gottleubje p??chiblizi, czehnjechu jomu me??chczano??ta, luther??ki	92.68293
duchowny a ??chul??ke d????c??i nap??chec??o, powitachu j??n luboznje z ryc??u a z kh??r???	duchowny a ??chul??ke dz???czi nap??checzo, powitachu j??n luboznje 3 ryczu a 3 kher???	88.6076
lu??chom a pod??akowachu ??o za do??taty pjenje??ny dar. Knj. Jurij Wawrik	lu??chom a podzakowachu ??o za do??taty pjenjezuy dar. Knj. Jurij Wawrik	95.652176
nahromad??i te?? we l??c??e 1865 mjez Serbami 60 toleri na wobnowjenjo Ma???	nahromadzi te} we lecze 1865 mjez Serbami 60 toleri na wobnowjenjo Ma-	92.85714
rijnoho wo??tarja we far??kej cyrkwi w Krupcy. ??? T??n??amyn J. Wawrik na???	rijnoho woktarja we far??kej cyrkwi w Krupcy. ??? T??n	71.014496
twari z kublerjom Jakubom Kocorom na puc??u mjez Khanjecami a Swinja?????	twari 3 kublerjom Jakubom Kocorom na puczu miez Khanjecami a Swinjat-	92.753624
nju rjanu kapa??ku, kotru?? kniez bi??kop Ludwik Forwerk na 9. ??eptembra 1870	nju riann kapalku, kotruz kniez bi??kop Ludwik Forwerk na 9. ??eptembra 1870	94.5946
wo??wjec??i.	wo??wieczi.	80.0
1866 zawjed??echu ??o we Kulow??kej ??ar??kej cyrkwi mej??ke pobo??no??c??e	1866 zawjedzechu ??o we Kulow??kej far??kej eyrkwi mej??ke poboznofeze	89.393936
k c??e??c??i Mac??eri Bo??ej.	k cze??czi Maczeri Bozej.	83.333336
1867 na 10. novembra za??o??i knj. tachant??ki vikar Jakub Hermann (we	1867 na 10. novembra zakozi knj. tachant??ki vikar Jakub Hermann (we97.01492
w??jnje 1866 kathol??ki p??lny kap??an pola ??ak??koho w??j??twa) kathol??ke to???	w??jnje 1866 kathol??ki p??lny kaplan pola ??ak??koho w??j??twa) kathol??ke to???	94.366196
war??two rjemje????ni??kich we Budy??chinje, kotre?? po t??j??ch l??tach rjanu kh????u	war??two rjemje??kni??kich we Budy??chinje, kotrez po t??j??ch Itah rjanu khezu	89.333336
na garbar??kej ha??y kupi.	na garbar??kej ha??y kupi.	100.0
Po po??tajenju ??ak??koho mini??ter??twa ??o wot l??ta 1868 m????to Budy??chin	Po po??tajenju ??ak??toho mini??ter??twa ??o wot leta 1868 me??to Budy??chin95.588234
n??m??ki wjacy njemjenuje ???Budi????in", ale ???Bautzen".	n??m??ti wjacy njemjenuje ???Budi????in???, ale ???Bautzen???.	92.0
Na k??ncu l??ta 1867 p??ac??e??che k??rc p??che??cy 7 tol. 7?? n??l.; ro??ki 3 tol.	Na k??ncu l??ta 1867 placze??che k??re p??che??cy 7 tol. 7?? u??l.; rozki 3 tol.	87.5
20 n??l.; jec??mjenja 2 tol. 25 n??l.; wow??a 2 tol. 10 n??l.; jah??ow 7 tol.	20 ufl.; jeczmjenja 2 tol. 25 u??l.; wow??a 2 tol. 10 u??l.; jahkow 7 tol.	91.54929
20 n??l.; hejdu??che 5 tol. 25 n??l.; kana butry 22?? n??l. ??? Na k??ncu l??ta	20 ufl.; hejdu??che 5 tol. 25 n??l.; kana butry 22?? nfl. ??? Na k??ncu l??ta	92.85714
1868: k??rc p??che??cy 6 tol.; ro??ki 4 tol. 22?? nfl.; jec??mjenja 4 tol.;	1868: k??re p??che??cy 6 tol.; rozki 4 tol. 22 ?? n??l.; jeczmjenja 4 tol.;	90.0
```

</p>
</details>
<details><summary>file input, filename output</summary>
<p>

```
nmalign -f --files1 GT.SELECTED/FILE_0094_*.gt.txt --files2 GT/FILE_0094_*.gt.txt
GT.SELECTED/FILE_0094_GT.SELECTED_region0000_region0000_line0000.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0013.gt.txt	0.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0002_region0002_line0000.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0013.gt.txt	0.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0000.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0013.gt.txt	0.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0001.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0001.gt.txt	91.89189
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0002.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0002.gt.txt	100.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0003.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0003.gt.txt	91.04478
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0004.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0004.gt.txt	96.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0005.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0005.gt.txt	95.652176
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0006.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0006.gt.txt	90.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0007.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0007.gt.txt	92.753624
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0008.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0008.gt.txt	92.30769
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0009.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0009.gt.txt	93.93939
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0010.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0010.gt.txt	89.74359
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0011.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0011.gt.txt	90.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0012.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0012.gt.txt	89.333336
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0013.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0013.gt.txt	92.10526
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0014.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0014.gt.txt	97.01492
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0015.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0015.gt.txt	95.454544
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0016.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0016.gt.txt	90.54054
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0017.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0017.gt.txt	91.358025
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0018.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0018.gt.txt	96.15385
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0019.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0019.gt.txt	95.945946
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0020.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0020.gt.txt	93.589745
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0021.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0021.gt.txt	93.42105
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0022.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0022.gt.txt	92.77109
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0023.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0023.gt.txt	88.75
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0024.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0024.gt.txt	95.71429
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0025.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0025.gt.txt	92.95775
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0026.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0026.gt.txt	71.42857
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0027.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0029.gt.txt	92.85714
GT.SELECTED/FILE_0094_GT.SELECTED_region0005_region0005_line0028.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0002_FILE_0094_CROPPED_region0002_line0030.gt.txt	94.666664
GT.SELECTED/FILE_0094_GT.SELECTED_region0011_region0011_line0000.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0001.gt.txt	81.818184
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0000.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0002.gt.txt	89.55224
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0001.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0003.gt.txt	84.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0002.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0004.gt.txt	97.05882
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0003.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0005.gt.txt	94.44444
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0004.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0006.gt.txt	89.47369
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0005.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0007.gt.txt	100.0
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0006.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0008.gt.txt	95.652176
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0007.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0009.gt.txt	92.15686
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0008.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0010.gt.txt	87.671234
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0009.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0011.gt.txt	91.666664
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0010.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0012.gt.txt	92.95775
GT.SELECTED/FILE_0094_GT.SELECTED_region0012_region0012_line0011.gt.txt	GT/FILE_0094_GT_FILE_0094_CROPPED_region0003_FILE_0094_CROPPED_region0003_line0013.gt.txt	90.14085
```

</p>
</details>

### [OCR-D processor](https://ocr-d.de/en/spec/cli) interface `ocrd-nmalign-merge`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.de/en/about) annotation workflow.

```
Usage: ocrd-nmalign-merge [OPTIONS]

  forced alignment of lists of string by fuzzy string matching

  > Force-align the textlines text of both inputs for each page, then
  > insert the 2nd into the 1st.

  > Find file pairs in both input file groups of the workspace for the
  > same page IDs.

  > Open and deserialize PAGE input files, then iterate over the element
  > hierarchy down to the TextLine level, looking at each first
  > TextEquiv. (If the second input has no TextLines, but newline-
  > separated TextEquiv at the TextRegion level, then use these instead.
  > If either side has no lines, then skip that page.)

  > Align character sequences in all pairs of lines for any combination
  > of textlines from either side.

  > Then iteratively search the next closest match pair. Remember the
  > assigned result as injective mapping from first to second fileGrp.

  > When all lines of the first fileGrp have been assigned, or the
  > ``cutoff_dist`` has been reached, apply the mapping by inserting
  > each line from the second fileGrp into position 0 (and `@index=0`)
  > at the first fileGrp. Also mark the inserted TextEquiv via
  > `@dataType=other` and `@dataTypeDetails=GRP`.

  > (Unmatched or cut off lines will stay unchanged, except for their
  > `@index=1` asf.)

  > Produce a new PAGE output file by serialising the resulting
  > hierarchy.

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -P, --param-override KEY VAL    Override a single JSON object key-value pair,
                                  taking precedence over --parameter
  -s, --server HOST PORT WORKERS  Run web server instead of one-shot processing
                                  (shifts mets/working-dir/page-id options to
                                   HTTP request arguments); pass network interface
                                  to bind to, TCP port, number of worker processes
  -m, --mets URL-PATH             URL or file path of METS to process
  -w, --working-dir PATH          Working directory of local workspace
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -C, --show-resource RESNAME     Dump the content of processor resource RESNAME
  -L, --list-resources            List names of processor resources
  -J, --dump-json                 Dump tool description as JSON and exit
  -h, --help                      This help message
  -V, --version                   Show version
```

For example:

<details><summary>file input, index output</summary>
<p>

```
ocrd-nmalign-merge -I OCR-D-OCR,OCR-D-GT-SEG-BLOCK -O OCR-D-GT-SEG-LINE
```

</p>
</details>

## Open Tasks

Usually segmentation not only deviates w.r.t. granularity and reading order of the regions,
but also of the lines. Often, lines will only allow partial matching, because they have been
merged / split on one side.

So for practical relevance, we still need a mechanism for recursive sub-line assignment (among the
remaining / too low scoring pairs).

This will involve heuristics and may need adding some parameters to control them.

Also, it may help to offer some interface allowing an interactive UI in the loop.

