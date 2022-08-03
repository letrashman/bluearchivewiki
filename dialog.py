from genericpath import exists
import os
import sys
import traceback
import argparse
import json

from jinja2 import Environment, FileSystemLoader

from pywikiapi import Site, ApiError
#import wikitextparser as wtp

from data import load_data
from model import Character
from generate import colorize, wiki_init

WIKI_API = 'https://bluearchive.wiki/w/api.php'

args = None
site = None



def generate():
    global args
    global site
    #lines = []
    data = load_data(args['data_primary'], args['data_secondary'], args['translation'])

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    env.filters['colorize'] = colorize
    template = env.get_template('template_dialog.txt')


    for character in data.characters.values():
        lines = []
        event_lines = []
        missing_tl = {}
        missing_tl['DataList'] = []
        character_variation_ids = []

        if not character['IsPlayableCharacter'] or character['ProductionStep'] != 'Release':
            continue

        if (args['character_id'] != None) and (character['Id'] != int(args['character_id'])):
            continue

        try:
            character = Character.from_data(character['Id'], data)
            #if character.club == character._club and character.club != 'Veritas': print(f' Unknown club name {character.name_translated} {character.club}')
        except Exception as err:
            print(f'Failed to parse for DevName {character["DevName"]}: {err}')
            traceback.print_exc()
            continue

        #get event versions of the character
        for character_variant in data.characters.values():
            if character_variant['DevName'].startswith(character.dev_name):
                character_variation_ids.append(character_variant['Id'])
                #print (character_variant['DevName'])


        lines, missing_tl['DataList'] = get_dialog_lines(character, data.character_dialog)

        for id in character_variation_ids:
            lines_list = []
            lines_tl_list = []
            character_variant = character
            character_variant.id = id
            lines_list, lines_tl_list = get_dialog_lines(character_variant, data.character_dialog_event)
            if len(lines_list)>0 or len(lines_tl_list)>0: print(f"Found {len(lines_list)} event lines and {len(lines_tl_list)} missing translation lines for {character.name_translated} (id {character.id})")
            if len(lines_list)>0: event_lines.extend(lines_list)
            if len(lines_tl_list)>0: missing_tl['DataList'].append(lines_tl_list)
            

        #print(f"JP_{character.dev_name.replace('_default','').replace('_','')}")
        if site != None: page_list = wiki_page_list(f"File:{character.name_translated}")
        else: page_list = []

        for index, line in enumerate(lines):
            process_file(character, index, line, lines, page_list)

        for index, line in enumerate(event_lines):
            process_file(character, index, line, lines, page_list)
            


        
        with open(os.path.join(args['outdir'], f'{character.name_translated}_dialog.txt'), 'w', encoding="utf8") as f:
            wikitext = template.render(character=character,lines=lines,event_lines=event_lines)
            f.write(wikitext)
            

        if site != None:
            wikipath = character.name_translated + '/audio'

            #if not wiki_page_exists(wikipath):
            print(f'Publishing {wikipath}')
            
            site(
            action='edit',
            title=wikipath,
            text=wikitext,
            summary=f'Generated character audio page',
            token=site.token()
            )

        
        if len(missing_tl['DataList'])>1 : 
            print(f"Missing {character.name_translated} translations: {len(missing_tl['DataList'])}")
            save_missing_translations('missing_tl_audio_'+character.name_translated.replace(' ', '_'), missing_tl)
            



def get_dialog_lines(character, dialog_data):
    lines = []
    missing_tl = []

    for index, line in enumerate(dialog_data):
        if line['CharacterId'] == character.id and line['VoiceClipsJp'] != []:
            line = merge_followup(index, dialog_data)

            #dump missing translations
            if 'LocalizeEN' not in line or line['LocalizeEN'] == None: line['LocalizeEN'] = ''
            if len(line['LocalizeJP'])>0 and len(line['LocalizeEN'])==0: missing_tl.append({'CharacterId':character.id, 'DialogCategory': line['DialogCategory'], 'DialogCondition': line['DialogCondition'], 'GroupId': line['GroupId'], 'LocalizeKR': line['LocalizeKR'], 'LocalizeJP': line['LocalizeJP'], 'LocalizeEN': '', 'VoiceClipsJp': line['VoiceClipsJp']})

            line['VoiceClipsJp'][0] = line['VoiceClipsJp'][0].replace('Memoriallobby', 'MemorialLobby')
            line['Title'] = line['VoiceClipsJp'][0].split('_', 1)[1]

            line['WikiVoiceClip'] = []
            line['WikiVoiceClip'].append(character.name_translated.replace(' ', '_') + '_' + line['Title'])
            
            line['LocalizeJP'] = len(line['LocalizeJP'])>0 and '<p>' + line['LocalizeJP'].replace("\n\n",'</p><p>').replace("\n",'<br>') + '</p>' or ''
            line['LocalizeEN'] = len(line['LocalizeEN'])>0 and '<p>' + line['LocalizeEN'].replace("\n\n",'</p><p>').replace("\n",'<br>') + '</p>' or ''

            lines.append(line)
            
    return lines, missing_tl


def merge_followup(index, dialog_data):
    current = dialog_data[index]
    try: next = dialog_data[index+1]
    except KeyError: return current
    
    if current['CharacterId'] == next['CharacterId'] and current['GroupId'] == next['GroupId'] and current['DialogCategory'] == next['DialogCategory'] and next['VoiceClipsJp'] == []:
        next = merge_followup(index + 1, dialog_data)
        if 'LocalizeEN' not in current or current['LocalizeEN'] == None: current['LocalizeEN'] = ''
        if 'LocalizeEN' not in next or next['LocalizeEN'] == None: next['LocalizeEN'] = ''
        current['LocalizeJP'] += '\n\n' + next['LocalizeJP']
        current['LocalizeEN'] += ( len(current['LocalizeEN'])>0 and '\n\n' or '' ) + next['LocalizeEN']
        #print(f'Merged followup at index {index}')
   
    return current
    

def process_file(character, index, line, lines, page_list):
    if not exists(f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/{line['VoiceClipsJp'][0]}.ogg"):
        #print (f"WARNING - Local file {line['VoiceClipsJp'][0]}.ogg not found")
        partial_file_path = f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/"
        partial_file_name = f"{line['VoiceClipsJp'][0]}"
        
        lines[index]['VoiceClipsJp'].clear()
        lines[index]['WikiVoiceClip'].clear()

        i=0
        while exists(f"{partial_file_path}{partial_file_name}_{i+1}.ogg"):
            lines[index]['VoiceClipsJp'].append(f"{partial_file_name}_{i+1}")
            lines[index]['WikiVoiceClip'].append(character.name_translated.replace(' ', '_') + '_' + f"{partial_file_name.split('_', 1)[1]}_{i+1}")
            #print(f"Added {lines[index]['VoiceClipsJp'][i]}/{lines[index]['WikiVoiceClip'][i]} partial voiceline to the list")
            i += 1

    if site != None:
        for index, wiki_voice_clip in enumerate(line['WikiVoiceClip']):
            #if not wiki_page_exists(f"File:{wiki_voice_clip}.ogg"):
            if f"File:{wiki_voice_clip}.ogg" not in page_list: 
                print (f"Uploading {wiki_voice_clip}.ogg")
                wiki_upload(f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/{line['VoiceClipsJp'][index]}.ogg", f"{wiki_voice_clip}.ogg")


def wiki_init():
    global site

    try:
        site = Site(WIKI_API)
        site.login(args['wiki'][0], args['wiki'][1])
        print(f'Logged in to wiki, token {site.token()}')

    except Exception as err:
        print(f'Wiki error: {err}')
        traceback.print_exc()



def wiki_page_exists(page):
    global site

    try:
        text = site('parse', page=page, prop='wikitext')
        print (f"Found wiki page {text['parse']['title']}")
        return True
    except ApiError as error:
        #print (f"ERROR = {error.data['code']}")
        if error.data['code'] == 'missingtitle':
            print (f"Page {page} not found")
            return False
        else:
            print (f"Unknown error {error}, retrying")
            wiki_page_exists(page)
        


def wiki_page_list(match):
    global site
    page_list = []

    try: 
        for r in site.query(list='search', srwhat='title', srsearch=match, srlimit=100, srprop='isfilematch'):
            for page in r['search']:
                page_list.append(page['title'].replace(' ', '_'))
    except ApiError as error:
        #print(error.message)
        if error.message == 'Call failed':
            print (f"Call failed, retrying")
            wiki_page_list(match)
        elif error.data['code'] == 'fileexists-no-change':
            print (f"{error.data['info']}")
            return True
        else:
            print (f"Unknown upload error {error}")

    print(f"Fetched {len(page_list)} pages that match {match}")
    return page_list



def wiki_upload(file, name):
    global site

    f = open(file, "rb")

    try: 
        site(
            action='upload',
            filename=name,
            comment=f'Character audio upload',
            ignorewarnings=True,
            token=site.token(),
            POST=True,
            EXTRAS={
                'files': {
                    'file': f.read()
                }
            }
        )
    except ApiError as error:
        #print(error.message)
        if error.message == 'Call failed':
            print (f"Call failed, retrying")
            wiki_upload(file, name)
        elif error.data['code'] == 'fileexists-no-change':
            print (f"{error.data['info']}")
            return True
        else:
            print (f"Unknown upload error {error}")


def save_missing_translations(name, data):
    global args

    f = open(args['translation'] + '/missing/' + name + '.json', "w", encoding='utf8' )
    f.write(json.dumps(data, sort_keys=False, indent=4, ensure_ascii=False))
    f.close()
    return True


def main():
    global args

    parser = argparse.ArgumentParser()

    parser.add_argument('-data_primary', metavar='DIR', help='Fullest (JP) game version data')
    parser.add_argument('-data_secondary', metavar='DIR', help='Secondary (Global) version data to include localisation from')
    parser.add_argument('-translation', metavar='DIR', help='Additional translations directory')
    parser.add_argument('-outdir', metavar='DIR', help='Output directory')
    parser.add_argument('-character_id', metavar='ID', help='Id of a single character to export')
    parser.add_argument('-data_audio', metavar='DIR', help='Audio files directory')
    parser.add_argument('-wiki', nargs=2, metavar=('LOGIN', 'PASSWORD'), help='Publish data to wiki, requires wiki_template to be set')
    parser.add_argument('-upload_files', metavar=('BOOL'), help='Check if audio file is already on the wiki and upload it if not')

    args = vars(parser.parse_args())
    args['data_primary'] = args['data_primary'] == None and '../ba-data/jp' or args['data_primary']
    args['data_secondary'] = args['data_secondary'] == None and '../ba-data/global' or args['data_secondary']
    args['translation'] = args['translation'] == None and 'translation' or args['translation']
    args['outdir'] = args['outdir'] == None and 'out' or args['outdir']
    args['character_id'] = args['character_id'] == None and '' or args['character_id']
    args['data_audio'] = args['data_audio'] == None and 'C:\\Utilities\\bluearchive_cdn\\r46_1_21_0720_7jenie3bdyqpazmdyipp\\MediaResources\\Audio\\VOC_JP' or args['data_audio']
    args['upload_files'] = args['upload_files'] == None and True or args['character_id']
    print(args)

    if args['wiki'] != None:
        wiki_init()


    try:
        generate()
    except:
        parser.print_help()
        traceback.print_exc()


if __name__ == '__main__':
    main()
