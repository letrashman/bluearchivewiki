import os
import re
import sys
import traceback

from jinja2 import Environment, FileSystemLoader

from data import load_data
from model import Character


def colorize(value):
    return re.sub(
        r'\[c]\[([0-9A-Fa-f]{6})]([^\[]*)\[-]\[/c]',
        r'<span style="color: #\1">\2</span>',
        value
    )


def generate(datadir, outdir):
    data = load_data(datadir)

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    env.filters['colorize'] = colorize
    template = env.get_template('template.txt')

    for character in data.characters.values():
        if not character['CollectionVisible']:
            continue

        try:
            character = Character.from_data(character['Id'], data)
        except Exception as err:
            print(f'Failed to parse for DevName {character["DevName"]}: {err}')
            traceback.print_exc()
            continue

        with open(os.path.join(outdir, f'{character.name}.txt'), 'w') as f:
            f.write(template.render(character=character))


def main():
    try:
        generate(sys.argv[1], sys.argv[2])
    except IndexError:
        print('usage: generate.py <datadir> <outdir>')


if __name__ == '__main__':
    main()
