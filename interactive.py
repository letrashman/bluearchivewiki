import os
import re
import sys
import traceback

from jinja2 import Environment, FileSystemLoader

from data import load_data
from generate import colorize
from model import Character
from wiki import Wiki

URL = 'https://bluearchive.miraheze.org/w/api.php'

SKILL_VALUES_PATTERN = re.compile(r'\[c]\[([0-9A-Fa-f]{6})](?P<value>\d+(\.\d+)?)(?P<unit>[^\[]*)\[-]\[/c]')


def input_multiline(prompt='> '):
    lines = []
    while True:
        line = input(prompt)
        if line.strip() == '/end':
            break

        lines.append(line)

    return '\n'.join(lines)


def get_characters(data):
    for character in data.characters.values():
        if not character['CollectionVisible']:
            continue

        try:
            character = Character.from_data(character['Id'], data)
        except Exception as err:
            print(f'Failed to parse for DevName {character["DevName"]}: {err}')
            traceback.print_exc()
            continue

        yield character.name, character


def translate_character(character):
    if name := input(f'Enter name ({character.name}): '):
        character.name = name

    if filename := input('Enter image filename: '):
        character.filename = filename

    if reading := input(f'Enter reading ({character.profile.reading}): '):
        character.profile.reading = reading

    print(f'Hobbies: {character.profile.hobbies}')
    if hobbies := input(f'Enter hobbies: '):
        character.profile.hobbies = hobbies

    if illustrator := input(f'Enter illustrator ({character.profile.illustrator}): '):
        character.profile.illustrator = illustrator

    if voice := input(f'Enter voice ({character.profile.voice}): '):
        character.profile.voice = voice

    print(f'Introduction:\n{character.profile.introduction}')
    print('Enter introduction (/end when done): ')
    if introduction := input_multiline():
        character.profile.introduction = introduction

    print('Enter how to obtain (/end when done): ')
    if how_to_obtain := input_multiline():
        character.how_to_obtain = how_to_obtain


def translate_skill(skill):
    if name_translated := input(f'Enter skill name ({skill.name}): '):
        skill.name_translated = name_translated

    # Sample values from the first level
    sample, _ = skill.levels[0]
    sample_clean = SKILL_VALUES_PATTERN.sub(r'\g<value>\g<unit>', sample)
    print(f'Skill description sample:\n{sample_clean}\n')
    for i, value in enumerate(get_skill_values(sample), start=1):
        print(f'Sample value on /{i}: {value}')

    template = input('Enter template: ')
    for i, (description, cost) in enumerate(skill.levels):
        skill.levels[i] = (translate_skill_description(description, template), cost)


def translate_skill_description(description, template):
    values = list(get_skill_values(description))

    def sub_value(m):
        return values[int(m.group('value')) - 1]

    def sub_skillvalue(m):
        return f'{{{{SkillValue|{m.group("text")}}}}}'

    description = re.sub(r'/(?P<value>\d)', sub_value, template)
    description = re.sub(r'{(?P<text>[^}]*)}', sub_skillvalue, description)
    return description


def get_skill_values(description):
    for m in SKILL_VALUES_PATTERN.finditer(description):
        yield m.group('value')


def interactive(datadir, username, password):
    data = load_data(datadir)
    characters = dict(get_characters(data))

    # Get character to work on
    character = characters[input('Enter character name: ')]

    # Translate character's profile in place
    translate_character(character)

    # Translate character's skills
    translate_skill(character.ex_skill)
    translate_skill(character.normal_skill)
    translate_skill(character.passive_skill)
    translate_skill(character.sub_skill)

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    env.filters['colorize'] = colorize
    template = env.get_template('template.txt')
    text = template.render(character=character)

    print(f'Rendered text:\n{text}')
    title = input('Enter title for wiki: ')
    if not title:
        print('Not uploading to wiki.')
        return

    w = Wiki(URL)
    w.login(username, password),
    w.create(title, text, f'Create page for {title}')


def main():
    try:
        interactive(sys.argv[1], sys.argv[2], sys.argv[3])
    except IndexError:
        print('usage: interactive.py <datadir> <username> <password>')


if __name__ == '__main__':
    main()
