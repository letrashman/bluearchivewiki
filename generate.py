import os
import re
import sys

from jinja2 import Environment, FileSystemLoader

from data import load_data
from model import Character


def colorize(value):
    return re.sub(
        r'\[c]\[([0-9A-Fa-f]{6})]([^\[]*)\[-]\[/c]',
        r'<span style="color: #\1">\2</span>',
        value
    )


def generate(path, character_id):
    data = load_data(path)
    character = Character.from_data(character_id, data)

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    env.filters['colorize'] = colorize
    template = env.get_template('template.txt')
    print(template.render(character=character))


def main():
    try:
        generate(sys.argv[1], int(sys.argv[2]))
    except (IndexError, ValueError):
        print('usage: generate.py <path> <character id>')


if __name__ == '__main__':
    main()
