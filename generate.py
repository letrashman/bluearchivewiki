import os
import re
import sys
import traceback
#import json
import argparse

from jinja2 import Environment, FileSystemLoader

from data import load_data
from model import Character


args = None

def colorize(value):
    return re.sub(
        r'\[c]\[([0-9A-Fa-f]{6})]([^\[]*)\[-]\[/c]',
        r'{{SkillValue|\2}}',
        value
    )


def generate():
    global args
    data = load_data(args['data_primary'], args['data_secondary'], args['translation'])

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    env.filters['colorize'] = colorize
    template = env.get_template('template.txt')

    #weapon_data = {}
    #weapon_data['DataList'] = []
    #
    #def save_weapons_translation(weapon_data):
    #    f = open('Weapons.json', "w", encoding='utf8' )
    #    f.write(json.dumps(weapon_data, sort_keys=False, indent=4, ensure_ascii=False))
    #    f.close()
    #    return True

    for character in data.characters.values():
        if not character['IsPlayableCharacter'] or character['ProductionStep'] != 'Release':
            continue

        try:
            character = Character.from_data(character['Id'], data)
        except Exception as err:
            print(f'Failed to parse for DevName {character["DevName"]}: {err}')
            traceback.print_exc()
            continue
        
        with open(os.path.join(args['outdir'], f'{character.name_translated}.txt'), 'w', encoding="utf8") as f:
            f.write(template.render(character=character))

        
        #weapon_data['DataList'].append({'Id':character.id, 'NameJP': character.profile.weapon_name, 'NameEN': character.profile.weapon_name_translated, 'DescriptionJP': character.profile.weapon_desc, 'DescriptionEN': character.profile.weapon_desc_translated})

    #save_weapons_translation(weapon_data)




def main():
    global args

    parser = argparse.ArgumentParser()

    parser.add_argument('-data_primary', metavar='DIR', help='Fullest (JP) game version data')
    parser.add_argument('-data_secondary', metavar='DIR', help='Secondary (Global) version data to include localisation from')
    parser.add_argument('-translation', metavar='DIR', help='Additional translations directory')
    parser.add_argument('-outdir', metavar='DIR', help='Output directory')
    # parser.add_argument('-wiki', nargs=2, metavar=('LOGIN', 'PASSWORD'), help='Publish data to wiki')

    args = vars(parser.parse_args())
    args['data_primary'] = args['data_primary'] == None and '../ba-data/jp' or args['data_primary']
    args['data_secondary'] = args['data_secondary'] == None and '../ba-data/global' or args['data_secondary']
    args['translation'] = args['translation'] == None and 'translation' or args['translation']
    args['outdir'] = args['outdir'] == None and 'out' or args['outdir']
    print(args)

    try:
        generate()
    except:
        parser.print_help()
        traceback.print_exc()


if __name__ == '__main__':
    main()
