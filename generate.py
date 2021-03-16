import os
import sys

from jinja2 import Environment, FileSystemLoader

from data import load_data
from model import Character


def generate(path):
    data = load_data(path)
    character = Character.from_data(10000, data)

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template('template.txt')
    print(template.render(character=character))


def main():
    try:
        generate(sys.argv[1])
    except IndexError:
        print('usage: generate.py <path>')


if __name__ == '__main__':
    main()
