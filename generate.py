import os
import re
import sys
import traceback
#import json

from jinja2 import Environment, FileSystemLoader

from data import load_data
from model import Character



def colorize(value):
    return re.sub(
        r'\[c]\[([0-9A-Fa-f]{6})]([^\[]*)\[-]\[/c]',
        r'{{SkillValue|\2}}',
        value
    )




def generate(datadir, localedir, outdir):
    data = load_data(datadir, localedir)

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
        
        with open(os.path.join(outdir, f'{character.name_translated}.txt'), 'w', encoding="utf8") as f:
            f.write(template.render(character=character))

        
        #weapon_data['DataList'].append({'Id':character.id, 'NameJP': character.profile.weapon_name, 'NameEN': character.profile.weapon_name_translated, 'DescriptionJP': character.profile.weapon_desc, 'DescriptionEN': character.profile.weapon_desc_translated})

    #save_weapons_translation(weapon_data)




def main():
    try:
        generate(sys.argv[1], sys.argv[2], sys.argv[3])
    except IndexError:
        print('usage: generate.py <datadir> <localedir> <outdir>')


if __name__ == '__main__':
    main()
