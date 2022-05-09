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
zo ſo wbohim wotpalenym we jich nuzy a pſchi natwarjenju ze wſchěch ſtro⸗	zo ſo wbohim wotpalenym we jih nuzy a pihi natwarjenju ze wſchech ftro-	91.78082
now a podwolnje pomhaſche.	now a podwolnje pomhaſche.	100.0
We lěcźe wójny mjez pruſkim kralom a rakuſkim khěžorom 1866 na 13.	We löcze wöjny mjez pruſkim kralom a rakuſtim khezorom 1866 na 13.	90.90909
januara rano we 4 hodźinach wozjewi ſo we drjewjanej khěžcy we Filipsdorfu	januara rano we 4 hodzinach wozjewi ſo we drjewjanej khezcy we Filipsdorfu	95.945946
pola Rumburka Macź Boža khorej knježnje Madlenje Kadec, jej prajicy:	pola Rumburka Macz Boza khorej knjeznje Madlenje Kadec, jej prajicy:95.588234
„Moje dźěcźo, z nětka zažije" (twoja bolaca rana). We Filipsdorfu na⸗	„Moje dzéczo, z nétka zazije“ (twoja bolaca rana). We Filipsdorfu na-	89.85507
twari ſo wot lěta 1870 z darow pobožnych wěriwych wulka rjana cyrkej	twari ſo wot leta 1870 z darow pobozuych weriwych wulka rjana eyrkej92.64706
a Serbja k ſwj. Marji tam rad pucźuja.	a Serbja É fwj. Marji tam rad puczuja.	92.10526
Do Rumburka (1 hodźinu wot Filipsdorfa daloko) Serbja hižom dlěhe	Do Rumburka (1 hodjinu wot Filipsdorfa daloko) Serbia hijom dlehe	93.84615
hacž 100 lět na porciunkulu (na 1. a 2. auguſcźe) k kapucinarjam z proceſſio⸗	haci 100 ſet na porciunkulu (na 1. a 2. auquſcze) É kapucinarjam z proceſſiv-	89.61039
nom khodźa: do ſtareje a noweje Krupki we Cžechach (k cźeŕpjacomu Jě⸗	nom khodja: do ſtareje a noweje Krupki we Czechach (f czetpjacomu Jè-	89.85507
zuſej na ſwjatym ſkhodźe a k boloſcźiwej Macźeri Božej) dwójcy za lěto, na	zuſej na ſwjatym ſkhodze a É boloſcziwej Maczeri Bozej) dwöjcy za Leto, na	89.189186
ſwjatki a na ſwj. dźeń Marijnoho naroda (8. ſeptembra), tež tak dołho. Prě⸗	ſwjatki a na fwj. dzeü Marijnoho naroda (8. ſeptembra), tež tak dolho. Pre-	92.0
nja ſerbſka putnica do Krupki bě wěſta Korchowa z Nowoſlic (1754).	nja ſerbſka putnica do Krupki be weſta Korchowa z Nowoſlic (1754).	96.969696
Hdyž we ſeptembrje 1865 ſerbſki proceſſion do Krupki dźěſche a do	Hdyi we ſeptembrje 1865 ſerbſki proceſſion do Krupki dzeſche a do	95.38461
měſtacžka Gottleuby pſchińdźe, hanjachu a wuſměchowachu pobožnych Serbow.	miſtaczka Gottleuby pſchindze, hanjachu a wuſmächowachu pobozuych Serbow.	90.41096
Krótki cžas na to, na 4. oktobrje 1865, wulki dźěl měſtacžka ſo wotpali. Młynſki	Krótki czas na to, na 4. oktobrje 1865, wulki dzel méſtaczka ſo wotpali. Mtynſei	91.25
miſchtr k. Jurij Wawrik z Khanjec, kotryž bě pſchi proceſſionje pobył, nahro⸗	miſchtr k. Jurij Wawrik z Khanjec, kotryz be pſchi proceſſionje pobyk, nahro⸗	96.1039
madźi za wotpalenych mjez Serbami 110 toleri a pſchipóſła je do Gottleuby	madzi za wotpalenych mjez Serbami 110 toleri a pſchipöſta je do Gottleuby	95.89041
z liſtom: „Dar luboſcźe za wotpalenych wot katholſkich Serbow, kiž kóžde lěto	z liſtom: „Dar luboſcze za wotpalenych wot katholſkich Serbow, kiz közde léto	93.50649
pſchez Gottleubu do Krupki pucźuja." Hdyž ſerbſki proceſſion we ſcźehowacym	pſchez Gottleubu do Krupki puczuja.“ Hdyz ſerbſki proceſſion we ſczehowaeym	93.333336
lěcźe 1866 ſo zaſy Gottleubje pſchibliži, cźehnjechu jomu měſchcźanoſta, lutherſki	lécze 1866 ſo zaſy Gottleubje pſchiblizi, czehnjechu jomu meſchczanoſta, lutherſki	92.68293
duchowny a ſchulſke dźěcźi napſchecźo, powitachu jón luboznje z rycžu a z khěr⸗	duchowny a ſchulſke dzẽczi napſcheczo, powitachu jón luboznje 3 ryczu a 3 kher—	88.6076
luſchom a podźakowachu ſo za doſtaty pjenježny dar. Knj. Jurij Wawrik	luſchom a podzakowachu ſo za doſtaty pjenjezuy dar. Knj. Jurij Wawrik	95.652176
nahromadźi tež we lěcźe 1865 mjez Serbami 60 toleri na wobnowjenjo Ma⸗	nahromadzi te} we lecze 1865 mjez Serbami 60 toleri na wobnowjenjo Ma-	92.85714
rijnoho wołtarja we farſkej cyrkwi w Krupcy. — Tónſamyn J. Wawrik na⸗	rijnoho woktarja we farſkej cyrkwi w Krupcy. — Tón	71.014496
twari z kublerjom Jakubom Kocorom na pucźu mjez Khanjecami a Swinjaŕ⸗	twari 3 kublerjom Jakubom Kocorom na puczu miez Khanjecami a Swinjat-	92.753624
nju rjanu kapałku, kotruž kniez biſkop Ludwik Forwerk na 9. ſeptembra 1870	nju riann kapalku, kotruz kniez biſkop Ludwik Forwerk na 9. ſeptembra 1870	94.5946
woſwjecźi.	woſwieczi.	80.0
1866 zawjedźechu ſo we Kulowſkej ſarſkej cyrkwi mejſke pobožnoſcźe	1866 zawjedzechu ſo we Kulowſkej farſkej eyrkwi mejſke poboznofeze	89.393936
k cžeſcźi Macźeri Božej.	k czeſczi Maczeri Bozej.	83.333336
1867 na 10. novembra załoži knj. tachantſki vikar Jakub Hermann (we	1867 na 10. novembra zakozi knj. tachantſki vikar Jakub Hermann (we97.01492
wójnje 1866 katholſki pólny kapłan pola ſakſkoho wójſtwa) katholſke to⸗	wöjnje 1866 katholſki pölny kaplan pola ſakſkoho wöjſtwa) katholſke to⸗	94.366196
warſtwo rjemjeſłniſkich we Budyſchinje, kotrež po tſjóch lětach rjanu khěžu	warſtwo rjemjeſkniſkich we Budyſchinje, kotrez po tſjöch Itah rjanu khezu	89.333336
na garbarſkej haſy kupi.	na garbarſkej haſy kupi.	100.0
Po poſtajenju ſakſkoho miniſterſtwa ſo wot lěta 1868 měſto Budyſchin	Po poſtajenju ſakſtoho miniſterſtwa ſo wot leta 1868 meſto Budyſchin95.588234
němſki wjacy njemjenuje „Budiſſin", ale „Bautzen".	nämſti wjacy njemjenuje „Budiſſin“, ale „Bautzen“.	92.0
Na kóncu lěta 1867 płacźeſche kórc pſcheńcy 7 tol. 7½ nſl.; rožki 3 tol.	Na köncu léta 1867 placzeſche köre pſcheücy 7 tol. 7½ uſl.; rozki 3 tol.	87.5
20 nſl.; jecžmjenja 2 tol. 25 nſl.; wowſa 2 tol. 10 nſl.; jahłow 7 tol.	20 ufl.; jeczmjenja 2 tol. 25 uſl.; wowſa 2 tol. 10 uſl.; jahkow 7 tol.	91.54929
20 nſl.; hejduſche 5 tol. 25 nſl.; kana butry 22½ nſl. — Na kóncu lěta	20 ufl.; hejduſche 5 tol. 25 nſl.; kana butry 22½ nfl. — Na köncu léta	92.85714
1868: kórc pſcheńcy 6 tol.; rožki 4 tol. 22½ nfl.; jecžmjenja 4 tol.;	1868: köre pſcheücy 6 tol.; rozki 4 tol. 22 ½ nſl.; jeczmjenja 4 tol.;	90.0
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

