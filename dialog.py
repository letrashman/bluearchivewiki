from genericpath import exists
import os
import sys
import traceback
import argparse
import json
import copy
import re

from jinja2 import Environment, FileSystemLoader

from pywikiapi import Site, ApiError
#import wikitextparser as wtp

from data import load_data, load_scenario_data
from model import Character
from generate import colorize

WIKI_API = 'https://bluearchive.wiki/w/api.php'

args = None
site = None


def generate():
    global args
    global site

    data = load_data(args['data_primary'], args['data_secondary'], args['translation'])
    scenario_data = load_scenario_data(args['data_primary'], args['data_secondary'], args['translation'])


    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    env.filters['colorize'] = colorize
    template = env.get_template('template_dialog.txt')


    for character in data.characters.values():      
        lines = []
        event_lines = []
        memorial_lines = []

        standard_lines = [] 
        standard_line_types = [
            'Formation', 'Tactic', 'Battle', 'CommonSkill', 'CommonTSASkill', 'ExSkill', 'Summon', #those do not have ingame transcriptions
            'Growup', 'Relationship'
                            ] 

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


        #dump missing translations
        missing_tl = [x for x in data.character_dialog if x['CharacterId']==character.id and x['LocalizeEN'] == '' and x['LocalizeJP'] != '']
        if len(missing_tl)>1 : 
            print(f"Missing {character.name_translated} translations: {len(missing_tl)}")
            save_missing_translations('dialog_'+character.name_translated.replace(' ', '_'), missing_tl)

        missing_tl = [x for x in data.character_dialog_event if x['CharacterId'] in character_variation_ids and x['LocalizeEN'] == '' and x['LocalizeJP'] != '']
        if len(missing_tl)>1 : 
            print(f"Missing {character.name_translated} event translations: {len(missing_tl)}")
            save_missing_translations('event_dialog_'+character.name_translated.replace(' ', '_'), missing_tl)
        


        #Memorial lobby unlock text from affection level script
        memorial_unlock = []
        first_memolobby_line = [x for x in data.character_dialog if x['CharacterId'] == character.id and x['DialogCategory'] == 'UILobbySpecial' and x['LocalizeJP'] != '']
        if first_memolobby_line: first_memolobby_line = first_memolobby_line[0]['LocalizeJP'].replace('\n','')
        #print(f"FIRST LINE {first_memolobby_line}")

        favor_rewards = [x for x in data.favor_rewards.values() if x['CharacterId'] == character.id and 'MemoryLobby' in x['RewardParcelType'] ]
        if favor_rewards: 
            sdf = [x for x in scenario_data.scenario_script_favor if x['GroupId'] == favor_rewards[0]['ScenarioSriptGroupId']]
            for line in sdf:
                if re.sub(r"\[wa:\d+\]", "", line['TextJp'], 0).replace('\n','').find(first_memolobby_line) > -1: 
                    #print (line)
                    break
                if line['TextJp'] and line['TextJp'].startswith('―'): 
                    line['CharacterId'] = character.id
                    line['DialogCategory'] = 'UILobbySpecial'
                    line['GroupId'] = 0
                    line['LocalizeJP'] = re.sub(r"\[wa:\d+\]", "", line['TextJp'].replace('― ',''), 0)
                    line['LocalizeEN'] = re.sub(r"\[wa:\d+\]", "", line['TextEn'].replace('— ','').replace('― ',''), 0)
                    line['VoiceClipsJp'] = []
                    
                    memorial_unlock.append(line)
            memorial_lines += get_memorial_lines(character, memorial_unlock, 0)


        lines = get_dialog_lines(character, data.character_dialog)


        memorial_lines += get_memorial_lines(character, data.character_dialog)

        for id in character_variation_ids:
            lines_list = []
            character_variant = copy.copy(character)
            character_variant.id = id
            lines_list = get_dialog_lines(character_variant, data.character_dialog_event)
            if len(lines_list)>0: event_lines.extend(lines_list)
            


        #print(f"JP_{character.dev_name.replace('_default','').replace('_','')}")
        if site != None: page_list = wiki_page_list(f"File:{character.name_translated}")
        else: page_list = []

        for line in lines:
            process_file(character, line, page_list)

        for line in event_lines:
            process_file(character, line, page_list)


        ml = []
        #Guess memorial lobby unlock audio if it had no text
        if (exists(f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/{character.dev_name.replace('_default','').replace('_','')}_MemorialLobby_0.ogg") or exists(f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/{character.dev_name.replace('_default','').replace('_','')}_MemorialLobby_0_1.ogg")) and not memorial_unlock:
            print(f'Found memorial lobby unlock audio for {character.name_translated}, but no text')
            ml.append(process_file(character, {'CharacterId': character.id, 'ProductionStep': 'Release', 'DialogCategory': 'UILobbySpecial', 'DialogCondition': 'Idle', 'Anniversary': 'None', 'StartDate': '', 'EndDate': '', 'GroupId': 0, 'DialogType': 'Talk', 'ActionName': '', 'Duration': 0, 'AnimationName': 'Talk_00_M', 'LocalizeKR': '', 'LocalizeJP': '', 'VoiceClipsKr': [], 'VoiceClipsJp': [], 'LocalizeEN': ""}, page_list))

        for line in memorial_lines:
            ml.append(process_file(character, line, page_list))
        memorial_lines = ml
            

        file_list = os.listdir(args['data_audio'] != None and f"{args['data_audio']}/JP_{character.model_prefab_name.replace('_Original','').replace('_','')}/" or [])
        for type in standard_line_types:
            #print(f"Gathering {type}-type standard lines")
            standard_lines += [x for x in file_list if type in x.split('_')[1]]

        for file in standard_lines:
            wiki_filename = f"{character.name_translated.replace(' ', '_') + '_' + file.split('_', 1)[1]}"
            if f"File:{wiki_filename}" not in page_list and site != None:
                print (f"Uploading {wiki_filename}")
                wiki_upload(f"{args['data_audio']}/JP_{character.model_prefab_name.replace('_Original','').replace('_','')}/{file}", wiki_filename)



        with open(os.path.join(args['outdir'], f'{character.name_translated}_dialog.txt'), 'w', encoding="utf8") as f:
            wikitext = template.render(character=character,lines=lines,event_lines=event_lines,memorial_lines=memorial_lines,standard_lines=standard_lines)
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

            

            

def get_memorial_lines(character, dialog_data, processing_group = 1):
    lines = []
    
    for index, line in enumerate(dialog_data):
        if line['CharacterId'] == character.id and line['DialogCategory'] == 'UILobbySpecial' and line['GroupId'] == processing_group:
            processing_group +=1
            
            line = merge_followup(index, dialog_data)
        
            if 'LocalizeEN' not in line or line['LocalizeEN'] == None: line['LocalizeEN'] = ''
            
            line['LocalizeJP'] = len(line['LocalizeJP'])>0 and '<p>' + line['LocalizeJP'].replace("\n\n",'</p><p>').replace("\n",'<br>') + '</p>' or ''
            line['LocalizeEN'] = len(line['LocalizeEN'])>0 and '<p>' + line['LocalizeEN'].replace("\n\n",'</p><p>').replace("\n",'<br>') + '</p>' or ''

            lines.append(line)

    return lines



def get_dialog_lines(character, dialog_data):
    lines = []

    for index, line in enumerate(dialog_data):
        if line['CharacterId'] == character.id and line['VoiceClipsJp'] != []:
            line = merge_followup(index, dialog_data)

            if line['VoiceClipsJp']: 
                line['VoiceClipsJp'][0] = line['VoiceClipsJp'][0].replace('Memoriallobby', 'MemorialLobby')
                line['Title'] = line['VoiceClipsJp'][0].split('_', 1)[1]

                line['WikiVoiceClip'] = []
                line['WikiVoiceClip'].append(character.name_translated.replace(' ', '_') + '_' + line['Title'])
            
            if 'LocalizeEN' not in line or line['LocalizeEN'] == None: line['LocalizeEN'] = ''

            line['LocalizeJP'] = len(line['LocalizeJP'])>0 and '<p>' + line['LocalizeJP'].replace("\n\n",'</p><p>').replace("\n",'<br>') + '</p>' or ''
            line['LocalizeEN'] = len(line['LocalizeEN'])>0 and '<p>' + line['LocalizeEN'].replace("\n\n",'</p><p>').replace("\n",'<br>') + '</p>' or ''

            lines.append(line)

    return lines



def merge_followup(index, dialog_data):
    current = dialog_data[index]
    try: next = dialog_data[index+1]
    except IndexError: 
        return current
    
    if current['CharacterId'] == next['CharacterId'] and current['GroupId'] == next['GroupId'] and current['DialogCategory'] == next['DialogCategory'] and next['VoiceClipsJp'] == []:
        next = merge_followup(index + 1, dialog_data)
        if 'LocalizeEN' not in current or current['LocalizeEN'] == None: current['LocalizeEN'] = ''
        if 'LocalizeEN' not in next or next['LocalizeEN'] == None: next['LocalizeEN'] = ''
        current['LocalizeJP'] += '\n\n' + next['LocalizeJP']
        current['LocalizeEN'] += ( len(current['LocalizeEN'])>0 and '\n\n' or '' ) + next['LocalizeEN']
        #print(f'Merged followup at index {index}')
   
    return current
    


def process_file(character, line, page_list):
    if (line['VoiceClipsJp'] and not exists(f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/{line['VoiceClipsJp'][0]}.ogg")) or line['DialogCategory'] == 'UILobbySpecial':
        #print (f"WARNING - Local file {line['VoiceClipsJp'][0]}.ogg not found")
        partial_file_path = f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/"
        partial_file_name = line['VoiceClipsJp'] and f"{line['VoiceClipsJp'][0]}" or f"{character.dev_name.replace('_default','').replace('_','')}_MemorialLobby_{line['GroupId']}"
        
        line['VoiceClipsJp'] = []
        line['WikiVoiceClip'] = []

        if exists(f"{partial_file_path}{partial_file_name}.ogg"): 
            line['VoiceClipsJp'].append(f"{partial_file_name}")
            line['WikiVoiceClip'].append(character.name_translated.replace(' ', '_') + '_' + f"{partial_file_name.split('_', 1)[1]}")

        i=0
        while exists(f"{partial_file_path}{partial_file_name}_{i+1}.ogg"):
            line['VoiceClipsJp'].append(f"{partial_file_name}_{i+1}")
            line['WikiVoiceClip'].append(character.name_translated.replace(' ', '_') + '_' + f"{partial_file_name.split('_', 1)[1]}_{i+1}")
            #print(f"Added {partial_file_path}{partial_file_name}_{i+1}.ogg partial voiceline to the list")
            i += 1

        if 'Title' not in line and line['VoiceClipsJp']: line['Title'] = line['VoiceClipsJp'][0].split('_', 1)[1]
        elif 'Title' not in line: line['Title'] = ''
        line['Title'] = re.sub(r"(_\d{1})_\d{1}", "\\g<1>", line['Title'], 0, re.MULTILINE)
        #if line['Title'] == 'MemorialLobby_0': line['Title'] = 'MemorialLobbyUnlock'

    if site != None:
        for index, wiki_voice_clip in enumerate(line['WikiVoiceClip']):
            #if not wiki_page_exists(f"File:{wiki_voice_clip}.ogg"):
            if f"File:{wiki_voice_clip}.ogg" not in page_list: 
                print (f"Uploading {wiki_voice_clip}.ogg")
                wiki_upload(f"{args['data_audio']}/JP_{character.dev_name.replace('_default','').replace('_','')}/{line['VoiceClipsJp'][index]}.ogg", f"{wiki_voice_clip}.ogg")

    return line




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
        for r in site.query(list='search', srwhat='title', srsearch=match, srlimit=200, srprop='isfilematch'):
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
    lines = []

    for line in data:
        lines.append({'CharacterId': line['CharacterId'], 'DialogCategory': line['DialogCategory'], 'DialogCondition': line['DialogCondition'], 'GroupId': line['GroupId'], 'LocalizeKR': line['LocalizeKR'], 'LocalizeJP': line['LocalizeJP'], 'LocalizeEN': '', 'VoiceClipsJp': line['VoiceClipsJp']})

    f = open(args['translation'] + '/missing/' + name + '.json', "w", encoding='utf8' )
    f.write(json.dumps({'DataList':lines}, sort_keys=False, indent=4, ensure_ascii=False))
    f.close()


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
