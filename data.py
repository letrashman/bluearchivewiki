import collections
import json
import os

BlueArchiveData = collections.namedtuple(
    'BlueArchiveData',
    ['characters', 'characters_ai', 'characters_localization', 'characters_skills', 'characters_stats', 'skills', 
    'skills_localization','translated_characters','translated_skills',
    'weapons', 'translated_weapons',
    'currencies','translated_currencies',
    'items', 'translated_items',
    'recipes', 'recipes_ingredients']
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
        (character_skill['CharacterId'], character_skill['MinimumGradeCharacterWeapon'], character_skill['IsFormConversion']): character_skill
        for character_skill
        in data['DataList']
    }


def load_characters_stats(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterStatExcelTable.json'), key='CharacterId')


def load_currencies(path):
    return load_file(os.path.join(path, 'Excel', 'CurrencyExcelTable.json'), key='ID')



def load_data(path, locale_path):
    return BlueArchiveData(
        characters=load_characters(path),
        characters_ai=load_characters_ai(path),
        characters_localization=load_characters_localization(path),
        characters_skills=load_characters_skills(path),
        characters_stats=load_characters_stats(path),
        skills=load_skills(path),
        skills_localization=load_skills_localization(path),
        translated_characters = load_characters_translation(locale_path),
        translated_skills =  load_skills_translation(locale_path),
        weapons = load_weapons(path),
        translated_weapons = load_weapons_translation(locale_path),
        currencies=load_currencies(path),
        translated_currencies=load_currencies_translation(locale_path),
        items=load_items(path),
        translated_items=load_items_translation(locale_path),
        recipes=load_recipes(path),
        recipes_ingredients=load_recipes_ingredients(path),
    )


def load_file(file, key='Id'):
    with open(file,encoding="utf8") as f:
        data = json.load(f)

    return {item[key]: item for item in data['DataList']}


def load_items(path):
    return load_file(os.path.join(path, 'Excel', 'ItemExcelTable.json'))

def load_recipes(path):
    return load_file(os.path.join(path, 'Excel', 'RecipeExcelTable.json'))

def load_recipes_ingredients(path):
    return load_file(os.path.join(path, 'Excel', 'RecipeIngredientExcelTable.json'))

def load_skills(path):
    return load_file(os.path.join(path, 'Excel', 'SkillExcelTable.json'))

def load_skills_localization(path):
    return load_file(os.path.join(path, 'Excel', 'LocalizeSkillExcelTable.json'), key='Key')

def load_characters_translation(path):
    return load_file(os.path.join(path, 'CharProfile.json'), key='CharacterId')

def load_weapons(path):
    return load_file(os.path.join(path, 'Excel', 'CharacterWeaponExcelTable.json'), key='Id')

def load_weapons_translation(path):
    return load_file(os.path.join(path, 'Weapons.json'), key='Id')


def load_currencies_translation(path):
    return load_file(os.path.join(path, 'Currencies.json'))

def load_items_translation(path):
    return load_file(os.path.join(path, 'Items.json'))

def load_skills_translation(path):
    return load_file(os.path.join(path, 'Skills.json'), key='GroupId')