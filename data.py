import collections
import json
import os

BlueArchiveData = collections.namedtuple(
    'BlueArchiveData',
    ['characters', 'characters_ai', 'characters_localization', 'characters_skills', 'characters_stats', 'currencies',
     'items', 'recipes', 'recipes_ingredients', 'skills', 'skills_localization']
)
BlueArchiveTranslations = collections.namedtuple(
    'BlueArchiveTranslations',
    ['currencies', 'items', 'skills']
)


def load_characters(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterExcelTable.json'))


def load_characters_ai(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterAIExcelTable.json'))


def load_characters_localization(path):
    return load_file(os.path.join(path, 'Excel', 'LocalizeCharProfileExcelTable.json'), key='CharacterId')


def load_characters_skills(path):
    with open(os.path.join(path, 'Excel', 'CharacterSkillListExcelTable.json')) as f:
        data = json.load(f)

    return {
        (character_skill['CharacterId'], character_skill['IsFormConversion']): character_skill
        for character_skill
        in data['DataList']
    }


def load_characters_stats(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterStatExcelTable.json'), key='CharacterId')


def load_currencies(path):
    return load_file(os.path.join(path, 'Excel', 'CurrencyExcelTable.json'), key='ID')


def load_currencies_translations(path):
    return load_file(os.path.join(path, 'Currencies.json'))


def load_data(path):
    return BlueArchiveData(
        characters=load_characters(path),
        characters_ai=load_characters_ai(path),
        characters_localization=load_characters_localization(path),
        characters_skills=load_characters_skills(path),
        characters_stats=load_characters_stats(path),
        currencies=load_currencies(path),
        items=load_items(path),
        recipes=load_recipes(path),
        recipes_ingredients=load_recipes_ingredients(path),
        skills=load_skills(path),
        skills_localization=load_skills_localization(path)
    )


def load_file(file, key='Id'):
    with open(file) as f:
        data = json.load(f)

    return {item[key]: item for item in data['DataList']}


def load_items(path):
    return load_file(os.path.join(path, 'Excel', 'ItemExcelTable.json'))


def load_items_translations(path):
    return load_file(os.path.join(path, 'Items.json'))


def load_recipes(path):
    return load_file(os.path.join(path, 'Excel', 'RecipeExcelTable.json'))


def load_recipes_ingredients(path):
    return load_file(os.path.join(path, 'Excel', 'RecipeIngredientExcelTable.json'))


def load_skills(path):
    return load_file(os.path.join(path, 'Excel', 'SkillExcelTable.json'))


def load_skills_localization(path):
    return load_file(os.path.join(path, 'Excel', 'LocalizeSkillExcelTable.json'), key='Key')


def load_skills_translations(path):
    return load_file(os.path.join(path, 'Skills.json'), key='GroupId')


def load_translations(path):
    return BlueArchiveTranslations(
        currencies=load_currencies_translations(path),
        items=load_items_translations(path),
        skills=load_skills_translations(path)
    )
