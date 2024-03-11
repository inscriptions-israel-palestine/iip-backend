#!/usr/bin/env python3

import sys
sys.path.append('../iip_search')

import os
import re
import csv
from lxml import etree
from datetime import date
from epidoc_parser import EpidocParser

def list_directory_xml(directory):
    return [f for f in os.listdir(directory) if f[-4:] == ".xml"]
    
def condense_whitespace(txt):
    if txt:
        txt = txt.replace('\n','')
        txt = re.sub(r'\s+', ' ', txt)
    return txt

EPIDOC_FILES_DIR = "../epidoc-files/"

files = list_directory_xml(EPIDOC_FILES_DIR)
files = [file for file in files if 'TestFile' not in file]

# reset file
header = ['inscriptionID', 'placename', 'pleiades_ref', 'description', 'depth', 'height', 'width', 
          'dimension_type', 'units', 'figures', 'forms', 'genres', 'materials', 'preservation', 'religions', 
          'writings', 'languages', 'coordinates', 'site', 'locus', 'not_before', 'not_after', 'provenance', 
          'region', 'diplomatic_xml', 'transcription_xml', 'translation', 'bibl']
          
out = open(f'iip_database_{date.today()}.csv', 'w')
writer = csv.writer(out)
writer.writerow(header)
    
for file in files:
    inscriptionID = file.split('.')[0]
    
    try:
        parser = EpidocParser(f"{EPIDOC_FILES_DIR}{file}")
    except Exception as e:
        print(e)
        continue
    
    bibliographic_entries_raw = parser.get_bibliography()
    city_raw = parser.get_city()
    description_raw = parser.get_description()
    dimensions_raw = parser.get_dimensions()
    figures_raw = parser.get_figures()
    iip_forms_raw = parser.get_iip_forms()
    iip_genres_raw = parser.get_iip_genres()
    iip_materials_raw = parser.get_iip_materials()
    iip_preservation_raw = parser.get_iip_preservation()
    iip_religions_raw = parser.get_iip_religions()
    iip_writings_raw = parser.get_iip_writings()
    images_raw = parser.get_images()
    languages_raw = parser.get_languages()
    location_coordinates = parser.get_location_coordinates()
    location_metadata = parser.get_location_metadata()
    not_after_raw = parser.get_not_after()
    not_before_raw = parser.get_not_before()
    provenance_raw = parser.get_provenance()
    region_raw = parser.get_region()
    short_description_raw = parser.get_short_description()
    title_raw = parser.get_title()
    
    bibl = ', '.join([str(item['ptr_target']) for item in bibliographic_entries_raw])
    placename = city_raw['placename']
    pleiades = city_raw['pleiades_ref']
    if description_raw:
        description = description_raw.strip()
    else:
        description = ''
    depth = dimensions_raw[0]['depth']
    height = dimensions_raw[0]['height']
    width = dimensions_raw[0]['width']
    dimension_type = dimensions_raw[0]['type']
    if 'unit' in dimensions_raw[0]:
        dimension_unit = dimensions_raw[0]['unit']
    else:
        dimension_unit = ''
    if figures_raw != []:
        figures = ', '.join([f"{condense_whitespace(item['name']).strip('. ')} ({condense_whitespace(item['locus']).strip('. ')})" for item in figures_raw])
    else:
        figures = ''
    
    if iip_forms_raw:
        iip_forms = ', '.join([item['xml_id'] for item in iip_forms_raw])
    else:
        iip_forms = ''
    if iip_genres_raw:
        iip_genres = ', '.join([item['xml_id'] for item in iip_genres_raw])
    else:
        iip_genres = ''
    if iip_materials_raw:
        iip_materials = ', '.join([item['xml_id'] for item in iip_materials_raw])
    else:
        iip_materials = ''
    if iip_preservation_raw:
        iip_preservation = iip_preservation_raw['xml_id']
    else:
        iip_preservation = ''
    if iip_religions_raw:
        iip_religions = ', '.join([item['xml_id'] for item in iip_religions_raw])
    else:
        iip_religions = ''
    if iip_writings_raw:
        iip_writings = ', '.join([item['xml_id'] for item in iip_writings_raw])
    else:
        iip_writings = ''
    languages = ', '.join([item['label'] for item in languages_raw])
    if 'site' in location_metadata:
        site = condense_whitespace(location_metadata['site'])
    else:
        site = ''
    if 'locus' in location_metadata:
        locus = condense_whitespace(location_metadata['locus'])
    else:
        locus = ''
    provenance = condense_whitespace(provenance_raw['placename'])
        
    diplomatic_xml = condense_whitespace(parser.get_diplomatic().xml)
    diplomatic = condense_whitespace(parser.get_diplomatic().text)
    
    transcription_xml = condense_whitespace(parser.get_transcription().xml)
    transcription = condense_whitespace(parser.get_transcription().text)
        
    translation_xml = condense_whitespace(parser.get_translation().xml)
    translation = condense_whitespace(parser.get_translation().text)
    
    

    newRow = [inscriptionID, placename, pleiades, description, depth, height, width, 
                dimension_type, dimension_unit, figures, iip_forms, iip_genres, 
                iip_materials, iip_preservation, iip_religions, iip_writings, languages, 
                location_coordinates, site, locus, not_before_raw, not_after_raw,
                provenance, region_raw, diplomatic_xml, transcription_xml,
                translation, bibl]
    
    writer.writerow(newRow)
    
out.close()
print(f'Output CSV written to: iip_database_{date.today()}.csv')
