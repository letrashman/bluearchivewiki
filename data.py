import collections
import json
import os

BlueArchiveData = collections.namedtuple(
    'BlueArchiveData',
    ['characters', 'characters_localization', 'characters_skills', 'characters_stats', 'skills', 'skills_localization']
)


def load_characters(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterExcelTable.json'))


def load_characters_localization(path):
    return load_file(os.path.join(path, 'Excel', 'LocalizeCharProfileExcelTable.json'), key='CharacterId')


def load_characters_skills(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterSkillListExcelTable.json'), key='CharacterId')


def load_characters_stats(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterStatExcelTable.json'), key='CharacterId')


def load_data(path):
    return BlueArchiveData(
        characters=load_characters(path),
        characters_localization=load_characters_localization(path),
        characters_skills=load_characters_skills(path),
        characters_stats=load_characters_stats(path),
        skills=load_skills(path),
        skills_localization=load_skills_localization(path)
    )


def load_file(file, key='Id'):
    with open(file) as f:
        data = json.load(f)

    return {item[key]: item for item in data['DataList']}


def load_skills(path):
    return load_file(os.path.join(path, 'Excel', 'SkillExcelTable.json'))


def load_skills_localization(path):
    return load_file(os.path.join(path, 'Excel', 'LocalizeSkillExcelTable.json'), key='Key')
