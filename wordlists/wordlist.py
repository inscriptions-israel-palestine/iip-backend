import csv
import logging
import os
import requests
import xml.etree.ElementTree as ET
from collections import OrderedDict
import unicodedata
import json

def main():  
    global tokenIDsToWord, lang   
    # build the tokenIDsToWord dictionary
    with requests.Session() as s:
        # adding another csv for kwic purposes
        download = s.get(ALL_TOKEN_IDS_TEST_URL)
        decoded = download.content.decode('utf-8')
        tokenIDs = csv.reader(decoded.splitlines(), delimiter=",")

    tokenIDsToWord = {}
    for row in tokenIDs:
        if row[0] == 'tokenID':
            continue
        fileID, tokenCount = row[0].split('-')
        if fileID not in tokenIDsToWord:
            tokenIDsToWord[fileID] = {}
        tokenIDsToWord[fileID][row[0]] = row[1], row[2]
        
    # iterate through languages and make wordlists
    langs = ['latin', 'greek', 'hebrew', 'aramaic']

    for lang in langs:
        downloadedCSV = download_csv(lang)
        
        # MAIN WORDLIST
        word_list = make_wordlists(downloadedCSV)

        with open(f"json/wordlist_{lang}.json", "w") as f:
            f.write(json.dumps(word_list))

        # PERSONAL NAMES
        name_list = make_wordlists(downloadedCSV, wordType='PERSON')

        with open(f"json/persName_{lang}.json", "w") as f:
            f.write(json.dumps(name_list))

        # OTHER INDICES
        fullDict = {}
        for indexType in INDEX_TYPES:
            fullDict[indexType] = make_wordlists(downloadedCSV, wordType=INDEX_TYPES[indexType])

        with open(f"json/indices_{lang}.json", "w") as f:
            f.write(json.dumps(fullDict))

log = logging.getLogger(__name__)

POSDICT = {"ADV": "adverb", "V": "verb", "N": "noun", "PREP": "preposition", "CC": "conjunction", "ADJ": "adjective"}
REVPOSDICT = {"noun": "N", "verb": "V", "modal": "V", "existential": "V", "bareinf": "V", "toinf": "V", "adjective": "ADJ", "Adj": "ADJ", "adverb": "ADV", "adv": "ADV", "adp": "PREP", "prep": "PREP", "cconj": "CC", "conj": "CC", "propn": "PROPN", "propername": 'PROPN', "num": "NUM", "ptcp": "PART", "pronoun": "PRON", "interjection": "INTERJ"} # adding more values from current csvs
MOODDICT = {"IND": "indicative", "PTC": "participle", "IMP": "imperative", "SUB": "subjunctive"}

# LATIN_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/dummy-data_latin.csv'
# LATIN_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/dummy-data_latin-corr.csv'
# LATIN_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/base_greek.csv'

# GREEK_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/corr_greek_test-data.csv'
# HEBREW_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/base_hebrew.csv'
# ARAMAIC_CSV_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/base_aramaic.csv'

LATIN_CSV = 'https://raw.githubusercontent.com/inscriptions-israel-palestine/iip-backend/main/wordlists/csv/latin.csv'
GREEK_CSV = 'https://raw.githubusercontent.com/inscriptions-israel-palestine/iip-backend/main/wordlists/csv/greek.csv'
ARAMAIC_CSV = 'https://raw.githubusercontent.com/inscriptions-israel-palestine/iip-backend/main/wordlists/csv/aramaic.csv'
HEBREW_CSV = 'https://raw.githubusercontent.com/inscriptions-israel-palestine/iip-backend/main/wordlists/csv/hebrew.csv'

# Update this!
ALL_TOKEN_IDS_TEST_URL = 'https://raw.githubusercontent.com/cmroughan/iip-wordlist_mockup/main/libs/wordlist/data/prelim_allWordIDs.csv'

# generic word information
NORM = 0
OCCUR = 1
LEMMA = 2
POS = 3
NORMID = 4
MORPH = 5

# personal name information
PERS_CHECK = 8
PERS_GENDER = 9
PERS_TYPE = 10
PERS_KEY = 11

# other index information
TITLE = 13
MILITARY = 16
ETHNICON = 18
RELATIONSHIP = 20
LOCATION = 22
DATE = 25
OCCUPATION = 28
MEASURE = 30
OBJECT = 32
RELIGIOUS = 34
OTHER = 36

INDEX_TYPES = {"title": TITLE, "military": MILITARY, "ethnicon": ETHNICON,
              "relationship": RELATIONSHIP, "location": LOCATION, "date": DATE,
              "occupation": OCCUPATION, "measure": MEASURE, "object": OBJECT,
              "religious": RELIGIOUS, "other": OTHER}

abjad = 'אבגדהוזחטיכךלמנסעפצקרשתםןףץ'

for langSelect in ['latin', 'greek', 'hebrew', 'aramaic']:
    with requests.Session() as s:
        if langSelect == 'latin':
            latin = s.get(LATIN_CSV).content.decode('utf-8')
        elif langSelect == 'greek':
            greek = s.get(GREEK_CSV).content.decode('utf-8')
        elif langSelect == 'hebrew':
            hebrew = s.get(HEBREW_CSV).content.decode('utf-8')
        elif langSelect == 'aramaic':
            aramaic = s.get(ARAMAIC_CSV).content.decode('utf-8')

# build the persKey_toLemmas dictionary
persKey_toLemmas = {}
for lang, rawCSV in [('latin', latin), ('greek', greek), ('hebrew', hebrew), ('aramaic', aramaic)]:
    csv_reader = csv.reader(rawCSV.splitlines(), delimiter=",")
    wordsCSV = list(csv_reader)
    for row in wordsCSV:
        # Latin CSV starts with two header rows, should be fixed
        if row[0] == 'Normalized' or row[0] == '':
            continue

        if row[POS].strip().lower() == 'propn' and row[PERS_CHECK] == 'y':
            if row[PERS_KEY].strip() == '':
                continue
            if row[PERS_KEY] not in persKey_toLemmas:
                persKey_toLemmas[row[PERS_KEY]] = []
            persLemma = row[LEMMA]
            if len(persLemma) > 0:
                persLemma = persLemma[0].upper() + persLemma[1:]
            if persLemma not in persKey_toLemmas[row[PERS_KEY]]:
                persKey_toLemmas[row[PERS_KEY]].append(persLemma)
        
        elif row[POS].strip().lower() == 'propername':
            
            if row[PERS_KEY].strip() == '':
                continue
            if row[PERS_KEY] not in persKey_toLemmas:
                persKey_toLemmas[row[PERS_KEY]] = []
            persLemma = row[LEMMA]
            if len(persLemma) > 0:
                persLemma = persLemma[0].upper() + persLemma[1:]
            if persLemma not in persKey_toLemmas[row[PERS_KEY]]:
                persKey_toLemmas[row[PERS_KEY]].append(persLemma)
                
################################################

def make_wordlists(downloadedCSV, wordType=None):
    global tokenIDsToWord
    
    words = {} 
    csv_reader = csv.reader(downloadedCSV.splitlines(), delimiter=",")
    dbwords = []
    inscriptions_seen = []

    wordsCSV = list(csv_reader)
    wordIDtoPOS = create_wordIDtoPOS(wordsCSV)
    
    # handle personal names
    if wordType == 'PERSON':
        wordsCSV = filter_csv_toNames(wordsCSV) 
    # handle other indices
    elif wordType:
        wordsCSV = filter_csv_toIndex(wordsCSV, wordType) 

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
            if wordType != 'PERSON':
                prepare_dbwords(inscrID, wordIDtoPOS, dbwords)

        row_word = row[NORM]

        extract_from_rows(row, words, wordIDtoPOS, wordType)
    sorted_words = {k: v for k, v in sorted(words.items(), key = noAccent)}

    if wordType == 'PERSON':
        return {"lemmas": count_words(sorted_words)}
    else:
        mapped_db = map(lambda x: "\n".join(x), dbwords)
        return {"lemmas": count_words(sorted_words), "db_list": "\n\n\n".join(mapped_db)}

################################################
       
def download_csv(langSelect):
    with requests.Session() as s:
        if langSelect == 'latin':
            download = s.get(LATIN_CSV)
        elif langSelect == 'greek':
            download = s.get(GREEK_CSV)
        elif langSelect == 'hebrew':
            download = s.get(HEBREW_CSV)
        elif langSelect == 'aramaic':
            download = s.get(ARAMAIC_CSV)
        decoded = download.content.decode('utf-8')
    return decoded

################################################

def noAccent(wordDict):
    return "".join([unicodedata.normalize("NFD", ch)[0].lower() for ch in wordDict[1]['lemma']])
    
################################################
    
def filter_csv_toNames(csvList):
    newCSV = []
    for row in csvList:
        if row[POS].strip().lower() == 'propn' and row[PERS_CHECK] == 'y':
            newCSV.append(row)
        elif row[POS].strip().lower() == 'propername':
            newCSV.append(row)
            
    return newCSV
    
################################################

def filter_csv_toIndex(csvList, INDEX):
    newCSV = []
    for row in csvList:
        if row[INDEX] == 'y':
            newCSV.append(row)
            
    return newCSV
    
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

def extract_from_rows(row, words, wordIDtoPOS, wordType=None):
    # wordType expects None for regular wordlists.
    # Personal name lists are indicated with wordType='PERSON'.
    # Other indices will input the relevant wordType.
    
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
        lemma = lemma.capitalize()
        wordform = wordform.capitalize()
        
    # strip points and accents from hebrew/aramaic
    if lang == 'hebrew' or lang == 'aramaic':
         lemma = ''.join([ch for ch in lemma if ch in abjad])
    
    if lemma not in words:
        words[lemma] = dict()
        words[lemma]['lemma'] = lemma
        words[lemma]['pos'] = pos
        words[lemma]['forms'] = dict()
        
        if wordType == 'PERSON':
            words[lemma]['gender'] = row[PERS_GENDER]
            words[lemma]['type'] = row[PERS_TYPE]
            words[lemma]['key'] = row[PERS_KEY]
            if row[PERS_KEY] != '':
                words[lemma]['cf'] = [l for l in persKey_toLemmas[row[PERS_KEY]] if l != lemma]
            else:
                words[lemma]['cf'] = []
            words[lemma]['forms'] = dict()
            
        elif wordType:
            words[lemma]['type'] = row[wordType+1]
    
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
    
###############################################
    
if __name__ == "__main__":
    main()
