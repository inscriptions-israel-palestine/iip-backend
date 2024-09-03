import os
import csv
import time
import pickle
import datetime
import threading
import unicodedata
from nicegui import ui
from nicegui.events import KeyEventArguments
from tkinter import * 
from tkinter.filedialog import askopenfilename, askdirectory

version_num = 'v 0.1.0'
ui.page_title(f'Inscriptions of Israel/Palestine Wordlist Utility ({version_num})')
ui.html('<style>.multi-line-notification { white-space: pre-line; }')

## TEXTS ########################################################################################

markdown_intro = f"""**Inscriptions of Israel/Palestine Wordlist Utility ({version_num})**

This is a utility for the Inscriptions of Israel / Palestine project. Its purpose is to facilitate matching words exported from the segmented \<div\>s to the parsed forms of the words in the IIP's wordlists for each language.

Usage expects (1) a wordlist CSV to work from and (2) a directory which contains the tagged CSVs for each language. The tagged language CSVs should have the language in question in their respective filenames (e.g. the CSV for Greek should include 'Greek' in the filename, Latin should include 'Latin', etc). Be sure you do not have multiple CSVs in this directory that have these languages in their name -- the utility will only load the last file it finds for each language.

The user will be presented with a word, its context, and a series of possible matches in the tagged spreadsheets. If there is a match, click or use the arrow keys to select the match in question, then click 'Next' or press Enter to go to the next word. If there are no matches, select 'No matches'. The user can skip a word by selecting 'Pass' -- at the end, any such skipped words will not be added to the tagged CSVs and will be output to a separate unprocessed word list CSV.

The tagged CSVs for each language will not be edited until the user has proceeded through all the words in the wordlist CSV. Progress however can be saved so that work on a wordlist can resume later. If this utility detects save data, it will be declared in the space below.
"""

markdown_help = f"""**Inscriptions of Israel/Palestine Wordlist Utility ({version_num})**

This is a utility for the Inscriptions of Israel / Palestine project. Its purpose is to facilitate matching words exported from the segmented \<div\>s to the parsed forms of the words in the IIP's wordlists for each language.

The user will be presented with a word, its context, and a series of possible matches in the tagged spreadsheets. If there is a match, click or use the arrow keys to select the match in question, then click 'Next' or press Enter to go to the next word. If there are no matches, select 'No matches'. The user can skip a word by selecting 'Pass' -- at the end, any such skipped words will not be added to the tagged CSVs and will be output to a separate unprocessed word list CSV.

The tagged CSVs for each language will not be edited until the user has proceeded through all the words in the wordlist CSV. Progress however can be saved so that work on a wordlist can resume later.
"""

markdown_summary = """**Summary:**

Below is an overview of the matches and non-matches found for the current wordlist CSV, along with counts of any words skipped.
    
Click 'Save to Tagged Wordlists' below to update the tagged language CSVs. This will result in the following:

- Matches will have their wordID added to the 'Occurrences' column of their respective match.
- Words that are not matches will be added as new rows at the bottom of the relevant language spreadsheets. Data on their parsed forms will have to be added manually.
- Skipped words will be output to a separate wordlist CSV, so that they may be matched with the parsed CSVs at a later time.
- If you had loaded partial progress on this wordlist from a savefile, this savefile will be deleted."""

## BUTTONS ######################################################################################

# Function to handle file selection in a separate thread
def open_file():
    threading.Thread(target=open_file_thread).start()
# The actual function running in a separate thread
def open_file_thread():
    global filepath
    root = Tk()
    root.withdraw()
    filepath = askopenfilename(filetypes=[("CSV Files", "*.csv")], initialdir='../word-segmentation/word_segmentation_lists')
    root.quit()
    root.destroy()
    refresh_start()
    
# Function to handle directory selection in a separate thread
def open_dir():
    threading.Thread(target=open_dir_thread).start()
# The actual function running in a separate thread
def open_dir_thread():
    global dirpath, dir_selected
    root = Tk()
    root.withdraw()
    dirpath = askdirectory(initialdir='./csv')
    root.quit()
    root.destroy()
    dir_selected = True
    refresh_start()

def start_button_click():
    global back_button_disabled, next_button_disabled, keyboard_active, loaded, load_error
    if loaded == False:
        find_matches()
    if load_error:
        refresh_error('lang')
        return
    if loaded == True:
        back_button_disabled = False
    else:
        back_button_disabled = True
    next_button_disabled = False
    keyboard_active = True
    refresh()
    
def reset_button_click():
    global filepath, dirpath, loaded, greekCSV, latinCSV, hebrewCSV, aramaicCSV, progress, words, possibilities, index, loaded
    filepath, dirpath, greekCSV, latinCSV, hebrewCSV, aramaicCSV = '', '', '', '', '', ''
    loadstate = []
    progress = 0        # progress tracks how far in a wordlist a user has gotten
    words = []
    possibilities = []
    index = progress    # index tracks where in a wordlist the user is now
    loaded = False
    refresh_start()

def record():
    global index, possibilities, possRadio
    current_value = possRadio.value - 1
    for i in range(len(possibilities[index])):
        possibilities[index][i][1] = 0
        if i == current_value:
            possibilities[index][i][1] = 1

def next_button_click():
    global back_button_disabled, next_button_disabled, words, index, progress
    back_button_disabled = False
    next_button_disabled = True
    record()
    index = min(index + 1, len(words)-1)
    progress = max(index, progress)
    refresh()

def back_button_click():
    global back_button_click, next_button_disabled, index
    next_button_disabled = False
    record()
    index = max(index - 1, 0)
    refresh()
    
def back_button_click2():
    global back_button_disabled, next_button_disabled, index
    next_button_disabled = True
    back_button_disabled = False
    index = len(words)-1
    refresh()
    
def review_button_click():
    global back_button_disabled, next_button_disabled
    record()
    next_button_disabled = True
    back_button_disabled = True
    build_review()
    refresh_review()
        
def build_review():
    global possibilities, words, resultsDict
    resultsDict = {'matches': {
                    'grc': [], 'lat': [], 'heb': [], 'arc': []
                    }, 'no matches': {
                    'grc': [], 'lat': [], 'heb': [], 'arc': []
                    }, 'skipped': {
                    'grc': [], 'lat': [], 'heb': [], 'arc': []
                    } }
    for i in range(0, len(words)):
        lang = words[i][-1]
        if possibilities[i][0][1] == 1:
            resultsDict['skipped'][lang].append(words[i][0])
        elif possibilities[i][-1][1] == 1:
            resultsDict['no matches'][lang].append(words[i][0])
        else:
            for entry in possibilities[i]:
                if entry[1] == 1:
                    resultsDict['matches'][lang].append([words[i][0], entry[0]])
                
## KEYBOARD ######################################################################################

# Function to handle keyboard events
def handle_key(e: KeyEventArguments):
    global possDict
    if not keyboard_active:
        return
    current_value = possRadio.value  # Get the current value of the radio button

    # Handle arrow key navigation for radio buttons
    if e.action.keydown and e.key.arrow_down:
        new_value = min(current_value + 1, len(possDict))
        possRadio.set_value(new_value)
    elif e.action.keydown and e.key.arrow_up:
        new_value = max(current_value - 1, 1)
        possRadio.set_value(new_value)

    # Handle Enter key to click the "Next" button
    elif e.action.keydown and e.key.enter:
        if not next_button_disabled:
            next_button_click()

    # Handle Backspace key to click the "Back" button
    elif e.action.keydown and e.key.backspace:
        if not back_button_disabled:
            back_button_click()

    # Handle right arrow key to click the "Next" button
    elif e.action.keydown and e.key.arrow_right:
        if not next_button_disabled:
            next_button_click()

    # Handle left arrow key to click the "Back" button
    elif e.action.keydown and e.key.arrow_left:
        if not back_button_disabled:
            back_button_click()

keyboard = ui.keyboard(on_key=handle_key, active=True)

## MATCHES ########################################################################################

def getContext(wordID):
    global newDictFull
    context = []
    ids = wordID.split('-')
    before = '...'
    after = '...'
    for i in range(int(ids[1])-5,int(ids[1])+5):
        testkey = ids[0]+'-'+str(i)
        if i == int(ids[1]):
            context.append('<mark style="background-color:#4ef542">' + newDictFull[testkey][2] + '</mark>')
        else:
            if testkey in newDictFull:
                context.append(newDictFull[testkey][2])
            else:
                if i < 0 and before == '...':
                    before = ''
                elif i > 0 and after == '...':
                    after = ''
    if before == '...':
        if ids[0]+'-'+str(int(ids[1])-6) not in newDictFull:
            before = ''
    if after == '...':
        if ids[0]+'-'+str(int(ids[1])+5) not in newDictFull:
            after = ''
    context = before+' '.join(context)+after
    return(context)

# If no saved progress, start from scratch
def find_matches():
    global newDict, newDictFull, matches, words, possibilities, index, progress, filepath, wordLookup, load_error
    try:
        # Load CSVs into dictionaries
        newCSV = open(filepath, newline='')
        new = list(csv.reader(newCSV))
        newCSV.close()
        newDict = {}
        newDictFull = {}
        wordLookup = {}
        load_error = None
        if new[0][0] != 'FileID':
            load_error = 'lang'
        for row in new:
            if len(row) < 4:
                load_error = 'lang'
                return
            if row[0] == 'FileID':
                continue
            if len(row) > 1:
                wordID = '-'.join([row[0].strip().rstrip('.xml'),row[1].strip()])
                if row[4] == 'w':
                    newDict[wordID] = row
                    wordLookup[wordID] = row[2]
                newDictFull[wordID] = row
        new = ''

        grcCSV = open(greekCSV, newline='')
        grc = list(csv.reader(grcCSV))
        grcCSV.close()
        grcDict = {}
        for row in grc:
            norm = ''.join([unicodedata.normalize('NFD',char)[0] for char in row[0]])
            norm = norm.lower()
            if norm not in grcDict:
                grcDict[norm] = []
            grcDict[norm].append(row)
        grc = ''

        latCSV = open(latinCSV, newline='')
        lat = list(csv.reader(latCSV))
        latCSV.close()
        latDict = {}
        for row in lat:
            norm = row[0].lower()
            if norm not in latDict:
                latDict[norm] = []
            latDict[norm].append(row)
        lat = ''

        hebCSV = open(hebrewCSV, newline='')
        heb = list(csv.reader(hebCSV))
        hebCSV.close()
        hebDict = {}
        for row in heb:
            norm = ''.join(c for c in row[0] if 'POINT' not in unicodedata.name(c))
            if norm not in hebDict:
                hebDict[norm] = []
            hebDict[norm].append(row)
        heb = ''
        
        arcCSV = open(aramaicCSV, newline='')
        arc = list(csv.reader(arcCSV))
        arcCSV.close()
        arcDict = {}
        for row in arc:
            norm = ''.join(c for c in row[0] if 'POINT' not in unicodedata.name(c))
            if norm not in arcDict:
                arcDict[norm] = []
            arcDict[norm].append(row)
        arc = ''

        # Sort by lang
        matches = {'grc':[],'lat':[],'heb':[],'arc':[]}
        for wordID in newDict:
            row = newDict[wordID]
            # GREEK
            if "grc" in row[3]:
                matches['grc'].append(wordID)
            # LATIN
            elif "la" in row[3]:
                matches['lat'].append(wordID)
            # HEBREW
            elif "he" in row[3]:
                matches['heb'].append(wordID)
            # ARAMAIC
            elif "arc" in row[3]:
                matches['arc'].append(wordID)
            else:
                load_error = 'lang'
                return

        langs = [('grc',grcDict), ('lat',latDict), ('heb',hebDict), ('arc', arcDict)]
        words = []
        possibilities = []

        for lang in langs:
            for wordID in matches[lang[0]]:
                words.append([wordID, newDict[wordID][2], getContext(wordID), lang[0]])
                if lang[0] == 'grc':
                    word = ''.join([unicodedata.normalize('NFD',char)[0] for char in newDict[wordID][2]])
                elif lang[0] in ['heb', 'arc']:
                    word = ''.join(c for c in newDict[wordID][2] if 'POINT' not in unicodedata.name(c))
                else:
                    word = newDict[wordID][2]
                poss = []
                poss.append(['[ Pass ]',0])
                if word.lower() in lang[1]:
                    for entry in lang[1][word.lower()]:
                        e_wordform = entry[0]
                        e_lemma = entry[2]
                        poss.append([e_wordform+' ('+' | '.join([e_lemma,entry[3],entry[5]])+')',0])
                poss.append(['[ No matches ]',0])
                possibilities.append(poss)

        index=0
        progress=0
    except Exception as e:
        print(e)

## PAGES ########################################################################################

# Word matching
def refresh():
    global filepath, latinCSV, greekCSV, hebrewCSV, aramaicCSV, review, progress, index, words, next_button_disabled, possDict
    # Clear the container before adding new elements
    content_container.clear()

    with content_container:  # Add new content to the container
        with ui.row().classes('w-full'):
            word_url = f"http://search.inscriptionsisraelpalestine.org/inscriptions/{words[index][0].split('-')[0]}"
            word_link = words[index][0]
            ui.html(f'<a href="{word_url}" target="_blank" style="color: blue; text-decoration: underline;">{word_link}</a><br>Language: {words[index][-1]}')
            ui.space()
            ui.button('Help', on_click=help_button_click)
            ui.button('Save', on_click=save_progress)
        ui.separator()

        with ui.grid(columns=2).style('grid-template-columns: auto 1fr; gap: 10px;'):
            ui.label('Word:')
            ui.html(words[index][1])

            ui.label('Context:')
            ui.html(words[index][2])


        ui.separator()

        ui.label('POSSIBLE MATCHES')
        
        global possRadio
        # Define the initial radio buttons
        i = 1
        selection = 1
        possDict = {}
        for entry in possibilities[index]:
            if entry[1] == 1:
                selection = i
            possDict[i] = entry[0]
            i = i + 1
        possRadio = ui.radio(possDict, value=selection)

        # Create the buttons and store them in variables
        with ui.row().classes('w-full'):
            back_button = ui.button('Back', on_click=back_button_click)
            if index == 0:
                back_button.disable()
            next_button = ui.button('Next', on_click=next_button_click)
            if index == len(words)-1:
                next_button.disable() 
                review = True
            else:
                next_button_disabled = False
            if review:
                ui.button('REVIEW', color='green', on_click=review_button_click)
                
            ui.space()
            ui.html(f'Word: {index+1} / {len(words)}<br>Progress: {progress+1} / {len(words)}')
            
        ui.separator()
        ui.html(f"<small><tt>Wordlist CSV: {'/'.join(filepath.split('/')[-2:])}<br>Latin:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(latinCSV.split('/')[-2:])}<br>Greek:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(greekCSV.split('/')[-2:])} <br>Hebrew:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(hebrewCSV.split('/')[-2:])} <br>Aramaic:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(aramaicCSV.split('/')[-2:])}</tt></small>")

# Initial page
def refresh_start():
    global filepath, dirpath, greekCSV, latinCSV, hebrewCSV, aramaicCSV
    if dirpath == () or dirpath == '':
        if loaded == False:
            dirpath = ''
            greekCSV, latinCSV, hebrewCSV, aramaicCSV = '', '', '', ''
    if filepath == ():
        filepath = ''
    if dirpath != '':
        directoryFiles = os.listdir(dirpath)
        for f in directoryFiles:
            if 'greek' in f.lower() and '.csv' in f.lower():
                greekCSV = dirpath + '/' + f
            elif 'latin' in f.lower() and '.csv' in f.lower():
                latinCSV = dirpath + '/' + f
            elif 'hebrew' in f.lower() and '.csv' in f.lower():
                hebrewCSV = dirpath + '/' + f
            elif 'aramaic' in f.lower() and '.csv' in f.lower():
                aramaicCSV = dirpath + '/' + f
    
    # Clear the container before adding new elements
    content_container.clear()
    with content_container:
    
        if dir_selected == True:
            no_CSVs = []
            for c in [['Greek', greekCSV], ['Latin', latinCSV], ['Hebrew', hebrewCSV], ['Aramaic', aramaicCSV]]:
                if c[1] == '':
                    no_CSVs.append(c[0])
            if len(no_CSVs) > 0:
                error_popup(no_CSVs)
                dirpath = ''
    
        ui.markdown(markdown_intro)
        ui.separator()
        with ui.row():
            ui.label('Files to load:')
            file_button = ui.button('Select wordlist CSV', on_click=open_file)
            if loaded:
                file_button.disable()
            dir_button = ui.button('Select directory containing parsed CSVs', on_click=open_dir)
            if loaded:
                dir_button.disable()
        with ui.card().classes('w-full'):
            if loaded:
                ui.html(f"<tt>Saved progress found in wordlist-to-tagged_progress.p. <br>Progress: {progress}/{len(words)} words from file: <br>&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(filepath.split('/')[-2:])} <br>Click 'Start' to load. Click 'Reset' to ignore.</tt>")
            else:
                ui.html(f"<tt>Wordlist CSV: {'/'.join(filepath.split('/')[-2:])}<br>Latin:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(latinCSV.split('/')[-2:])}<br>Greek:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(greekCSV.split('/')[-2:])} <br>Hebrew:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(hebrewCSV.split('/')[-2:])} <br>Aramaic:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'/'.join(aramaicCSV.split('/')[-2:])}</tt>")
        with ui.row():
            start_button = ui.button('Start', on_click=start_button_click, color='green')
            if filepath == '' or dirpath == '':
                if loaded == False:
                    start_button.disable()
            reset_button = ui.button('Reset', on_click=reset_button_click, color='red')
            if filepath == '' and dirpath == '':
                if loaded == False:
                    reset_button.disable()
                                     
def refresh_review():
    global words, possibilities, resultsDict, wordLookup
    content_container.clear()
    with content_container:
        ui.markdown(markdown_summary)
        ui.separator()
        ui.markdown(f"**Current wordlist CSV:** `{filepath}`")
        with ui.row():
            c_match = {}
            for l in resultsDict["matches"]:
                c_match[l] = len(resultsDict["matches"][l])
            c_noMatch = {}
            for l in resultsDict["no matches"]:
                c_noMatch[l] = len(resultsDict["no matches"][l])
            c_skipped = {}
            for l in resultsDict["skipped"]:
                c_skipped[l] = len(resultsDict["skipped"][l])
                
            with ui.card():
                get_summary_string(c_match, 'MATCHES')
                with ui.scroll_area().classes('h-32 border'):
                    words_html = []
                    for l in resultsDict["matches"]:
                        for w in resultsDict["matches"][l]:
                            words_html.append(f'{w[0]}: {wordLookup[w[0]]}')
                    words_html = '<small><tt>' + '<br>'.join(words_html)
                    ui.html(words_html)
                            
            with ui.card():
                get_summary_string(c_noMatch, 'NO MATCHES')
                with ui.scroll_area().classes('h-32 border'):
                    words_html = []
                    for l in resultsDict["no matches"]:
                        for w in resultsDict["no matches"][l]:
                            words_html.append(f'{w}: {wordLookup[w]}')
                    words_html = '<small><tt>' + '<br>'.join(words_html)
                    ui.html(words_html)
                
            with ui.card():
                get_summary_string(c_skipped, 'SKIPPED')
                with ui.scroll_area().classes('h-32 border'):
                    words_html = []
                    for l in resultsDict["skipped"]:
                        for w in resultsDict["skipped"][l]:
                            words_html.append(f'{w}: {wordLookup[w]}')
                    words_html = '<small><tt>' + '<br>'.join(words_html)
                    ui.html(words_html)
                
        with ui.row():
            ui.button('Return to matching', on_click=back_button_click2, color='red')
            ui.button('Save to Tagged Wordlists', on_click=save_results, color='green')

def get_summary_string(d, h):
    s = 'style="border: 1px solid; padding: 6px"'
    return ui.html(f'<span style="font-weight:bold;">{h}</span><br><table><tr><td {s}>Greek: {d["grc"]} words</td><td {s}>Latin: {d["lat"]} words</td></tr><tr><td {s}>Hebrew: {d["heb"]} words</td><td {s}>Aramaic: {d["arc"]} words</td></tr></table>')
    
def refresh_error(e):
    if e == 'lang':
        content_container.clear()
        with content_container:
            ui.markdown("**Error:** no suitable entries found. This code expects the fourth column of the input segmented word CSV to be the `Language` column, and for languages to be one of the following:\n\n- Greek (grc)\n- Latin (la, lat)\n- Hebrew (he, heb)\n- Aramaic (arc)")
            ui.markdown("Please ensure that a suitable wordlist CSV is selected to be sorted and try again.")
            ui.button("Back to start", on_click=refresh_start)

## DIALOGS ########################################################################################
        
def save_progress():
    save_dialog.open()
    
with ui.dialog() as help_dialog, ui.card():
    ui.markdown(markdown_help)
    ui.button('Back', on_click=help_dialog.close)
def help_button_click():
    help_dialog.open()
        
def save_progress():
    global progress, words, possibilities, filepath, greekCSV, latinCSV, hebrewCSV, aramaicCSV, wordLookup, newDict
    savestate = [filepath, greekCSV, latinCSV, hebrewCSV, aramaicCSV, progress, words, possibilities, wordLookup, newDict]
    pickle.dump(savestate, open("wordlist-to-tagged_progress.p", "wb"))
    with ui.dialog() as save_dialog, ui.card():
        ui.label(f'Saved progress on {progress+1} words: progress recorded in file `wordlist-to-tagged_progress.p`. You may close the application.')
        ui.button('Back', on_click=save_dialog.close)
    save_dialog.open()
    
def error_popup(lang_list):
    with ui.dialog() as error_dialog, ui.card():
        ui.markdown(f'**Warning:** no candidate CSVs found for {", ".join(lang_list)}. Please select the directory that contains the tagged CSVs for all four languages. This can usually be found in `iip-backend/wordlists/csv`.')
        ui.button('Back', on_click=error_dialog.close)
    error_dialog.open()
    
def save_results():
    global greekCSV, latinCSV, hebrewCSV, aramaicCSV, filepath, resultsDict
    greek_out = '.'.join(greekCSV.split('.')[:-1]) + '_edited.csv'
    latin_out = '.'.join(latinCSV.split('.')[:-1]) + '_edited.csv'
    hebrew_out = '.'.join(hebrewCSV.split('.')[:-1]) + '_edited.csv'
    aramaic_out = '.'.join(aramaicCSV.split('.')[:-1]) + '_edited.csv'
    
    saveDict = {'grc': False, 'lat': False, 'heb': False, 'arc': False}
    for l in resultsDict['matches']:
        if len(resultsDict['matches'][l]) > 0:
            saveDict[l] = True
            break
    for l in resultsDict['no matches']:
        if len(resultsDict['no matches'][l]) > 0:
            saveDict[l] = True
            break
    
    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    skipped_out = '/'.join(filepath.split('/')[:-1]) + '/unsorted_' + date + '.csv'
    saveSkipped = False
    
    for l in resultsDict['skipped']:
        if len(resultsDict['skipped'][l]) > 0:
            saveSkipped = True
            break
    
    written_csvs = []
    for c in [['grc', greek_out], ['lat', latin_out], ['heb', hebrew_out], ['arc', aramaic_out]]:
        if saveDict[c[0]] == True:
            written_csvs.append(c[1])
            save_csv(c[0], c[1])
    written_csvs = '\n- '.join(written_csvs)
    
    saveMsg = f'Tagged wordlists saved to the following file(s). Please be sure to add lexical information to any words which did not have an existing match:\n\n- `{written_csvs}`'
    if saveSkipped == True:
        save_skipped_file(skipped_out)
        saveMsg = saveMsg + f'\n\nWords which were selected to be skipped have been saved in the following CSV:\n\n- `{skipped_out}`'
    saveMsg = saveMsg + '\n\nYou may now close the application.'
    
    if "wordlist-to-tagged_progress.p" in os.listdir("."):
        os.remove("wordlist-to-tagged_progress.p")
        
    with ui.dialog() as save2_dialog, ui.card():
        ui.markdown(saveMsg)
        ui.button('Back', on_click=save2_dialog.close)
    save2_dialog.open()
    
def save_skipped_file(outFile):
    global newDict, resultsDict
    outCSV = [['FileID','Word Num','Normalized','Language','w/n/naw','Element']]
    for l in resultsDict['skipped']:
        for wordID in resultsDict['skipped'][l]:
            outCSV.append(newDict[wordID])
    with open(outFile, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(outCSV)
        
def save_csv(lang, outFile):
    global resultsDict, greekCSV, latinCSV, hebrewCSV, aramaicCSV, wordLookup
    csvLangs = {'grc': greekCSV, 'lat': latinCSV, 'heb': hebrewCSV, 'arc': aramaicCSV}
    
    with open(csvLangs[lang]) as inFile:
        currCSV = list(csv.reader(inFile))
        
    for match in resultsDict['matches'][lang]:
        for row in currCSV:
            possString = row[0]+' ('+' | '.join([row[2],row[3],row[5]])+')'
            if match[1] == possString:
                occurs = [occ.strip() for occ in row[1].split(',')]
                occurs = [occ.split('.')[0] for occ in occurs]
                occurs.append(match[0])
                occurs = list(set(occurs))
                row[1] = ', '.join(occurs)
    for wordID in resultsDict['no matches'][lang]:
        newRow = ['' for entry in currCSV[0]]
        newRow[0] = wordLookup[wordID]
        newRow[1] = wordID
        currCSV.append(newRow)
    with open(outFile, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(currCSV)
            

## START ########################################################################################

# Starting variables
back_button_disabled = True  # Initially disabled
next_button_disabled = False  # Initially enabled
keyboard_active = False
filepath, dirpath, greekCSV, latinCSV, hebrewCSV, aramaicCSV = '', '', '', '', '', ''
loadstate = []
progress = 0        # progress tracks how far in a wordlist a user has gotten
words = []
possibilities = []
index = progress    # index tracks where in a wordlist the user is now
review = False
dir_selected = False
load_error = None

# Create a container for the dynamic content
content_container = ui.card().classes('w-full')  # Container for dynamic UI elements

# Check for saved progress
loaded = False
dir_list = os.listdir(".")
if "wordlist-to-tagged_progress.p" in dir_list:
    loadstate = pickle.load(open("wordlist-to-tagged_progress.p", "rb"))
    filepath = loadstate[0]
    greekCSV = loadstate[1]
    latinCSV = loadstate[2]
    aramaicCSV = loadstate[3]
    hebrewCSV = loadstate[4]
    progress = loadstate[5]
    words = loadstate[6]
    possibilities = loadstate[7]
    wordLookup = loadstate[8]
    newDict = loadstate[9]
    
    index = progress
    
    loaded = True

refresh_start()
    
## RUN ###########################################################################################

ui.run()

