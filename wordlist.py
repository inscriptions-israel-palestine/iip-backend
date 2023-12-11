import csv
import logging
import os
import requests
import xml.etree.ElementTree as ET
from collections import OrderedDict
import unicodedata

def main():
    import json

    langs = ['latin', 'greek', 'hebrew', 'aramaic']
    for lang in langs:
        word_list = get_words_pos_new(lang)

        with open(f"wordlist_{lang}.json", "w") as f:
            f.write(json.dumps(word_list))

log = logging.getLogger(__name__)

POSDICT = {"ADV": "adverb", "V": "verb", "N": "noun", "PREP": "preposition", "CC": "conjunction", "ADJ": "adjective"}
REVPOSDICT = {"noun": "N", "verb": "V", "modal": "V", "existential": "V", "bareinf": "V", "toinf": "V", "adjective": "ADJ", "Adj": "ADJ", "adverb": "ADV", "adv": "ADV", "adp": "PREP", "prep": "PREP", "cconj": "CC", "conj": "CC", "propn": "PROPN", "propername": 'PROPN', "num": "NUM", "ptcp": "PART", "pronoun": "PRON", "interjection": "INTERJ"} # adding more values from current csvs
                                                          
MOODDICT = {"IND": "indicative", "PTC": "participle", "IMP": "imperative", "SUB": "subjunctive"}

#LATIN_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/dummy-data_latin.csv'
LATIN_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/dummy-data_latin-corr.csv'
#LATIN_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/base_greek.csv'

GREEK_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/corr_greek_test-data.csv'
HEBREW_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/base_hebrew.csv'
ARAMAIC_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/base_aramaic.csv'


ALL_TOKEN_IDS_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/prelim_allWordIDs.csv'

NORM = 0
OCCUR = 1
LEMMA = 2
POS = 3
NORMID = 4
MORPH = 5

abjad = 'אבגדהוזחטיכךלמנסעפצקרשתםןףץ'

with requests.Session() as s:
    # adding another csv for kwic purposes
    log.debug( f'ALL_TOKEN_IDS_TEST_URL, ``{ALL_TOKEN_IDS_TEST_URL}``')
    download = s.get(ALL_TOKEN_IDS_TEST_URL)
    log.debug( f'download, ``{download}``' )
    decoded = download.content.decode('utf-8')
    tokenIDs = csv.reader(decoded.splitlines(), delimiter=",")

# build the tokenIDsToWord dictionary
tokenIDsToWord = {}
for row in tokenIDs:
    if row[0] == 'tokenID':
        continue
    fileID, tokenCount = row[0].split('-')
    if fileID not in tokenIDsToWord:
        tokenIDsToWord[fileID] = {}
    tokenIDsToWord[fileID][row[0]] = row[1], row[2]


# data is formatted as a list of dictionaries
# each dictionary is a lemma
# LEMMA DICTIONARY FORMAT
# [ lemma: normalized form of word
#   pos: part of speech of lemma
#   count: # of times word appears in inscriptions
#   forms : dictionary of different forms of word]
# FORMS DICTIONARY FORMAT
# [ form: string of form
#   count: # of times form appears
#   pos: pos information about the form
#   kwics: list of duples of the form, first index is kwic, second is inscrp id]
# (kwics and inscription ids should correspond to each other)

def get_words_pos_new(langSelect):
    global tokenIDsToWord
    global lang
    
    lang = langSelect

    log.debug( 'start' )

    with requests.Session() as s:
        if langSelect == 'latin':
#           log.debug( f'LATIN_CSV_NEW_URL, ``{settings_app.LATIN_CSV_NEW_URL}``' )
            log.debug( f'LATIN_CSV_TEST_URL, ``{LATIN_CSV_TEST_URL}``' )
#           download = s.get(settings_app.LATIN_CSV_TEST_URL)
            download = s.get(LATIN_CSV_TEST_URL)
        elif langSelect == 'greek':
            log.debug( f'GREEK_CSV_TEST_URL, ``{GREEK_CSV_TEST_URL}``' )
            download = s.get(GREEK_CSV_TEST_URL)
        elif langSelect == 'hebrew':
            log.debug( f'HEBREW_CSV_TEST_URL, ``{HEBREW_CSV_TEST_URL}``' )
            download = s.get(HEBREW_CSV_TEST_URL)
        elif langSelect == 'aramaic':
            log.debug( f'ARAMAIC_CSV_TEST_URL, ``{ARAMAIC_CSV_TEST_URL}``' )
            download = s.get(ARAMAIC_CSV_TEST_URL)
        log.debug( f'download, ``{download}``' )
        decoded = download.content.decode('utf-8')
        words = {} 
        csv_reader = csv.reader(decoded.splitlines(), delimiter=",")
        dbwords = []
        inscriptions_seen = []
        
        wordsCSV = list(csv_reader)
        wordIDtoPOS = create_wordIDtoPOS(wordsCSV)
        
        for row in wordsCSV:
            # Latin CSV starts with two header rows, should be fixed
            if row[0] == 'Normalized' or row[0] == '':
                continue
                
            row_occurs = row[OCCUR]
            for occur in row_occurs.split(', '):
                inscrID = occur.split('-')[0]
                
                # there are some old broken inscrIDs that need to be skipped
                if inscrID not in tokenIDsToWord:
                    continue
                    
                if inscrID in inscriptions_seen:
                    continue
                inscriptions_seen.append(inscrID)
                prepare_dbwords(inscrID, wordIDtoPOS, dbwords)
            
            row_word = row[NORM]
            
            extract_from_rows(row, words, wordIDtoPOS)
        sorted_words = {k: v for k, v in sorted(words.items(), key = noAccent)}
        
        mapped_db = map(lambda x: "\n".join(x), dbwords)
        
#         with open('SORTED_WORDS.txt','w') as f:
#             f.write(str(sorted_words))
#         with open('MAPPED_DB.txt','w') as f:
#             f.write("\n\n\n".join(mapped_db))
#         with open('DBWORDS.txt','w') as f:
#             f.write(str(dbwords))
        
    return {"lemmas": count_words(sorted_words), "db_list": "\n\n\n".join(mapped_db)}
    
###############################################

def noAccent(wordDict):
    return "".join([unicodedata.normalize("NFD", ch)[0].lower() for ch in wordDict[1]['lemma']])
    
################################################

def create_wordIDtoPOS(csvIn):
    wordIDtoPOS = {}
    for row in csvIn:
        if row[0] == 'Normalized' or row[0] == '':
            continue
        for wordID in row[OCCUR].split(', '):
            lemma = row[LEMMA]
            # remove points / accents from hebrew/aramaic
            if lang == 'hebrew' or lang == 'aramaic':
                lemma = ''.join([ch for ch in row[LEMMA] if ch in abjad])
            pos = row[POS]
            # handle empty pos
            if pos.strip() == '':
                pos = 'X'
            wordIDtoPOS[wordID] = lemma, pos
    return wordIDtoPOS
    
###############################################

# Preparing DBwords should happen separately, and on an inscrID basis, not a wordID basis
def prepare_dbwords(inscrID, wordIDtoPOS, dbwords):
    dbwordlist = []
    for token in tokenIDsToWord[inscrID]:
        wordform, w_n_naw = tokenIDsToWord[inscrID][token]
        # get the lemma and pos for <w>
        if w_n_naw == 'w':
            if token in wordIDtoPOS:
                pos = wordIDtoPOS[token][1]
                if pos.lower().strip() in REVPOSDICT:
                    pos = REVPOSDICT[pos.lower().strip()]
                dbwordlist.append(f"{wordIDtoPOS[token][0].upper()}/{pos}")
            else:
                dbwordlist.append('[...]/X')
                
        # return [NUM]/N for <num> 'lemmas'
        elif w_n_naw == 'n':
            dbwordlist.append('[NUM]/NUM')
            
        # return [...]/X for <orig> 'lemmas'
        elif w_n_naw == 'naw':
            dbwordlist.append('[...]/X')
            
    dbwords.append(dbwordlist)
    
###############################################

def count_words(words):
    counted = []
    for lemma, lemma_dict in words.items():
        total = 0
        for form, form_dict in lemma_dict["forms"].items():
            formlen = len(form_dict["kwics"])
            total += formlen
#             form_dict["count"] = formlen
        lemma_dict["count"] = total
        counted.append(lemma_dict)
    return counted
    
###############################################

def extract_from_rows(row, words, wordIDtoPOS):
    lemma = row[LEMMA].lower()
    wordform = row[NORM].lower()
    pos = row[POS]
    wordIDs = row[OCCUR].split(', ')
    count_wordform = len(wordIDs)
    morph = row[MORPH]
    
    if pos.lower().strip() in REVPOSDICT:
        pos = REVPOSDICT.get(pos.lower().strip())
    elif pos.strip() == '':
        pos = 'X'
    else:
        pos = pos
        
    # handle proper noun capitalization
    if pos == 'PROPN':
        lemma = lemma.title()
        wordform = wordform.title()
        
    # strip points and accents from hebrew/aramaic
    if lang == 'hebrew' or lang == 'aramaic':
         lemma = ''.join([ch for ch in lemma if ch in abjad])
    
    if lemma not in words:
        words[lemma] = dict()
        words[lemma]['lemma'] = lemma
        words[lemma]['pos'] = pos
        words[lemma]['forms'] = dict()
    
    listKWICstrings = []
    for wordID in wordIDs:
        fileID, tokenCount = wordID.split('-')
        
        # there are some old broken inscrIDs that need to be skipped
        if fileID not in tokenIDsToWord:
            continue
        
        # KWIC strings
        KWICstring = get_kwicTuple(wordID)
        listKWICstrings.append([KWICstring, fileID])
        
    if morph != 'None':
        morph = morph.replace('UNSPECIFIED','').strip()
        try:
            morph = " ".join([morphdata.split('=')[1].lower() for morphdata in morph.split('|')])
        except:
            morph = morph.lower()
            morph = morph.replace('1-prelets','').strip()
            morph = morph.replace('2-prelets','').strip()
            morph = morph.replace('prelets-1','').strip()
            morph = morph.replace('prelets-2','').strip()
            #print(morph)
    else:
        morph = pos.lower()
        
    
    forms = {'form': wordform, 'pos': morph, 'kwics': listKWICstrings, 'count': count_wordform}
        
    pos_string = f'{wordform} {morph}'
    words[lemma]['forms'][pos_string] = forms
    
###############################################

# defining a function to get KWIC from an input wordID and the tokenIDsToWord dictionary
# returns an ordered dictionary
def get_kwic(wordID, extent=2):
    fileID, tokenCount = wordID.split('-')
    tokenCount = int(tokenCount)
    possTokenStart = max(tokenCount - extent, 1)
    possTokenEnd = tokenCount + extent
    
    kwicList = OrderedDict()
    for i in range(possTokenStart, possTokenEnd+1):
        possTokenID = f"{fileID}-{i}"
        if possTokenID in tokenIDsToWord[fileID].keys():
            # the ''.join([unicodedata.normalize('NFC',c)... bit is temporary
            # really this should be handled in the underlying data
            # or in the underlying scripts that produce that data
            # but we can't expect the data in the underlying XML files to stay consistent
            # because it is being encoded by different machines and keyboards etc etc
            kwicList[possTokenID] = ''.join([unicodedata.normalize('NFC',c) for c in tokenIDsToWord[fileID][possTokenID][0]])
    return(kwicList)
    
###############################################

# defining a function to get KWIC from an input wordID and the tokenIDsToWord dictionary
# returns an ordered dictionary
def get_kwicTuple(wordID, extent=2):
    fileID, tokenCount = wordID.split('-')
    tokenCount = int(tokenCount)
    possTokenStart = max(tokenCount - extent, 1)
    possTokenEnd = tokenCount + extent
    
    kwicList = OrderedDict()
    pre_token = []
    for i in range(possTokenStart, tokenCount):
        possTokenID = f"{fileID}-{i}"
        if possTokenID in tokenIDsToWord[fileID].keys():
            pre_token.append(tokenIDsToWord[fileID][possTokenID][0])
    # temporary, while hebrew data isn't updated yet
    try:
        token = tokenIDsToWord[fileID][wordID][0]
    except:
        token = ''
    post_token = []
    for i in range(tokenCount+1, possTokenEnd+1):
        possTokenID = f"{fileID}-{i}"
        if possTokenID in tokenIDsToWord[fileID].keys():
            post_token.append(tokenIDsToWord[fileID][possTokenID][0])
        
    kwicTuple = (" ".join(pre_token), token, " ".join(post_token))

    return(kwicTuple)
    
if __name__ == "__main__":
    main()
