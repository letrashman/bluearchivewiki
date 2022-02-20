import itertools
import operator
import re
#from googletrans import Translator


class Character(object):
    def __init__(self, id, name, dev_name, portrait, name_en, family_name_en, rarity, school, role, position, damage_type, armor_type, combat_class, equipment, weapon_type,
                 uses_cover, profile, normal_skill, ex_skill, passive_skill, passive_weapon_skill, sub_skill, stats, weapon, favor, memory_lobby, momotalk, liked_gift_tags):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.school = school
        self._role = role
        self.position = position
        self._damage_type = damage_type
        self._armor_type = armor_type
        self._combat_class = combat_class
        self.equipment = equipment
        self.weapon_type = weapon_type
        self._uses_cover = uses_cover
        self.profile = profile
        self.normal_skill = normal_skill
        self.ex_skill = ex_skill
        self.passive_skill = passive_skill
        self.passive_weapon_skill = passive_weapon_skill
        self.sub_skill = sub_skill
        self.stats = stats
        self.weapon = weapon
        self.favor = favor
        self.memory_lobby = memory_lobby
        self.momotalk = momotalk
        self.liked_gift_tags = liked_gift_tags

        self.dev_name = dev_name
        self.portrait = portrait
        self.name_translated = name_en
        self.family_name_translated = family_name_en

    @property
    def role(self):
        return {
            'DamageDealer': 'Attacker',
            'Tanker': 'Tank',
            'Supporter': 'Support',
            'Healer': 'Healer',
            'Vehicle': 'Tactical Support'
        }[self._role]

    @property
    def damage_type(self):
        return {
            'Explosion': 'Explosive',
            'Pierce': 'Penetration',
            'Mystic': 'Mystic'
        }[self._damage_type]

    @property
    def armor_type(self):
        return {
            'LightArmor': 'Light',
            'HeavyArmor': 'Heavy',
            'Unarmed': 'Special'
        }[self._armor_type]

    @property
    def combat_class(self):
        return {
            'Main': 'Striker',
            'Support': 'Special'
        }[self._combat_class]

    @property
    def uses_cover(self):
        return 'Yes' if self._uses_cover else 'No'

    @property
    def name_normalized(self):
        return re.split("[ _(]", self.name_translated)[0]

    @classmethod
    def from_data(cls, character_id, data):
        character = data.characters[character_id]
        character_ai = data.characters_ai[character['CharacterAIId']]
        liked_gift_tags = data.characters_cafe_tags[character_id]['FavorItemTags']
        portrait = character['TextureDir'][character['TextureDir'].rfind('/')+1:]

        return cls(
            character['Id'],
            data.characters_localization[character_id]['PersonalNameJp'],
            character['DevName'],
            portrait,
            data.translated_characters[character_id]['PersonalNameEn'],
            data.translated_characters[character_id]['FamilyNameEn'],
            character['DefaultStarGrade'],
            character['School'] != 'RedWinter' and character['School'] or 'Red Winter',
            character['TacticRole'],
            character['TacticRange'],
            character['BulletType'],
            character['ArmorType'],
            character['SquadType'],
            character['EquipmentSlot'],
            character['WeaponType'],
            character_ai['CanUseObstacleOfKneelMotion'] or character_ai['CanUseObstacleOfStandMotion'],
            Profile.from_data(character_id, data),
            Skill.from_data(data.characters_skills[(character_id, 0, False)]['PublicSkillGroupId'][0], data),
            Skill.from_data(data.characters_skills[(character_id, 0, False)]['ExSkillGroupId'][0], data, 5),
            Skill.from_data(data.characters_skills[(character_id, 0, False)]['PassiveSkillGroupId'][0], data),
            Skill.from_data(data.characters_skills[(character_id, 2, False)]['PassiveSkillGroupId'][0], data),
            Skill.from_data(data.characters_skills[(character_id, 0, False)]['ExtraPassiveSkillGroupId'][0], data),
            Stats.from_data(character_id, data),
            Weapon.from_data(character_id, data),
            Favor.from_data(character_id, data),
            MemoryLobby.from_data(character_id, data),
            Momotalk.from_data(character_id, data),
            liked_gift_tags
        )


class Profile(object):
    def __init__(self, full_name, age, birthday, height, hobbies, illustrator, voice, introduction_jp, introduction_en, reading, release_date_jp, weapon_name, weapon_desc, weapon_name_translated, weapon_desc_translated):
        self.full_name = full_name
        self._age = age
        self._birthday = birthday
        self.height = height
        self.hobbies = hobbies
        self.illustrator = illustrator
        self.voice = voice
        self.introduction_jp = introduction_jp
        self.introduction_en = introduction_en
        self.reading = reading
        self.release_date_jp = release_date_jp
        self.weapon_name = weapon_name
        self.weapon_desc = weapon_desc
        self.weapon_name_translated = weapon_name_translated
        self.weapon_desc_translated = weapon_desc_translated

    @property
    def age(self):
        return self._age[:-1]

    @property
    def birthday(self):
        month, day = self._birthday.split('/')
        month = [
            'January',
            'February',
            'March',
            'April',
            'May',
            'June',
            'July',
            'August',
            'September',
            'October',
            'November',
            'December'
        ][int(month) - 1]
        return f'{month} {day}'

    @classmethod
    def from_data(cls, character_id, data):
        profile = data.characters_localization[character_id]
        weapon = data.translated_weapons[character_id]

        hobbies = 'HobbiesEn' in data.translated_characters[character_id] and data.translated_characters[character_id]['HobbiesEn'] or profile['HobbyJp']
        illustrator = 'Illust' in data.translated_characters[character_id] and data.translated_characters[character_id]['Illust'] or profile['ArtistNameJp']
        voice = 'VoiceEn' in data.translated_characters[character_id] and data.translated_characters[character_id]['VoiceEn'] or profile['CharacterVoiceJp']
        age = 'AgeEn' in data.translated_characters[character_id] and data.translated_characters[character_id]['AgeEn'] or profile['CharacterAgeJp']
        height = 'HeightEn' in data.translated_characters[character_id] and data.translated_characters[character_id]['HeightEn'] or profile['CharHeightJp']
        release_date_jp = 'ReleaseDateJp' in data.translated_characters[character_id] and data.translated_characters[character_id]['ReleaseDateJp'] or ''
        introduction_en = 'ProfileIntroductionEn' in data.translated_characters[character_id] and data.translated_characters[character_id]['ProfileIntroductionEn'] or ''
 

        #translator = Translator()
        #
        #weapon_name_translated = translator.translate(profile['WeaponNameJp'], dest='en', src='ja').text
        #weapon_desc_translated = translator.translate(profile['WeaponDescJp'], dest='en', src='ja').text
        #print(weapon_name_translated)
        #weapon_name_translated = None
        #weapon_desc_translated = None

        return cls(
            f'{profile["FamilyNameJp"]} {profile["PersonalNameJp"]}',
            age,
            profile['BirthDay'],
            height,
            hobbies,
            illustrator,
            voice,
            profile['ProfileIntroductionJp'].replace("\n\n",'<br>'),
            introduction_en.replace("\n\n",'<br>'),
            f'{profile["FamilyNameRubyJp"]} {profile["PersonalNameJp"]}',
            release_date_jp,
            profile['WeaponNameJp'],
            profile['WeaponDescJp'].replace("\n\n",'<br>'),
            weapon['NameEN'],
            weapon['DescriptionEN'].replace("\n\n",'<br>')
        )


def _get_skill_upgrade_materials(level, data):
    recipe = data.recipes[level['RequireLevelUpMaterial']]
    if recipe['RecipeType'] != 'SkillLevelUp':
        return

    ingredients = data.recipes_ingredients[recipe['RecipeIngredientId']]
    ingredients = itertools.chain(
        zip(ingredients['IngredientParcelType'], ingredients['IngredientId'], ingredients['IngredientAmount']),
        zip(ingredients['CostParcelType'], ingredients['CostId'], ingredients['CostAmount'])
    )
    for type_, id, amount in ingredients:
        if type_ == 'Item':
            #yield data.translated_items[id]['NameEn'], data.items[id]['Icon'].rsplit('/', 1)[-1], amount
            yield data.etc_localization[data.items[id]['LocalizeEtcId']]['NameEn'], data.items[id]['Icon'].rsplit('/', 1)[-1], amount
        elif type_ == 'Currency':
            yield data.translated_currencies[id]['NameEn'], data.currencies[id]['Icon'].rsplit('/', 1)[-1], amount


class SkillLevel(object):
    def __init__(self, description, cost, materials):
        self.description = description
        self.cost = cost
        self.materials = materials

    @classmethod
    def from_data(cls, level, group_id, data):
        return cls(
            translate_skill(data.skills_localization[level['LocalizeSkillId']]['DescriptionJp'], level['Level'], group_id, data),
            level['SkillCost'],
            list(_get_skill_upgrade_materials(level, data))
        )


class Skill(object):
    def __init__(self, name, name_translated, icon, levels, description_general, damage_type, skill_cost):
        self.name = name
        self.icon = icon
        self.levels = levels
        self._damage_type = damage_type

        # Extra information
        self.name_translated = name_translated
        self.description_general = description_general
        #self.max_level = 10
        self.skill_cost = skill_cost

    @property
    def damage_type(self):
        return {
            'Explosion': 'Explosive',
            'Pierce': 'Penetration',
            'Mystic': 'Mystic'
        }[self._damage_type]

    @classmethod
    def from_data(cls, group_id, data, max_level = 10):
        group = [skill for skill in data.skills.values() if skill['GroupId'] == group_id]
        if not group:
            raise KeyError(group_id)





        def format_description(levels, text_en):
            start_variables = re.findall(r'\{\{SkillValue\|([^\}\[]+)\}\}',  levels[0].description)
            end_variables = re.findall(r'\{\{SkillValue\|([^\}\[]+)\}\}',  levels[max_level-1].description)
            range_text = []

            for i in range(len(end_variables)):
                try: stripped_start = re.findall(r'([0-9a-zA-z.]+).*', start_variables[i])
                except IndexError: 
                    start_variables.append(0)
                    stripped_start = [0]

                range_text.append(start_variables[i] != end_variables[i] and f'{stripped_start[0]}~{end_variables[i]}' or f'{end_variables[i]}')

            for skill_value in range_text:
                text_en = re.sub(r'\$[0-9]{1}', '{{SkillValue|' + skill_value + '}}', text_en, 1) 

            return text_en

        levels = [SkillLevel.from_data(level, group_id, data) for level in sorted(group, key=operator.itemgetter('Level'))]

        skill_cost = []
        for i in range(1, max_level):
            if levels[i].cost != levels[i-1].cost:
                #print (f'Skill level {i+1} cost change from {levels[i-1].cost} to {levels[i].cost}')
                skill_cost.append({'level':i+1, 'cost':levels[i].cost})

        text_general = translate_skill(levels[9].description, max_level, group_id, data)
        description_general = format_description(levels, text_general)


        try: data.translated_skills[group[0]['GroupId']]['NameEn']
        except KeyError: 
            skill_name_en = None
        else:  
            skill_name_en = data.translated_skills[group[0]['GroupId']]['NameEn']

        if skill_name_en == None:
            print (f"No translation found for skill {data.skills_localization[group[0]['LocalizeSkillId']]['NameJp']}, group_id {group_id}")

        return cls(
            data.skills_localization[group[0]['LocalizeSkillId']]['NameJp'],
            skill_name_en,
            group[0]['IconName'].rsplit('/', 1)[-1],
            levels,
            description_general,
            group[0]['BulletType'],
            skill_cost
        )


def replace_units(text):
    
    text = re.sub('1回', 'once', text)
    text = re.sub('2回', 'twice', text)
    #text = re.sub('3回', 'three times', text)
    text = re.sub('回', '', text)
    text = re.sub('つ', '', text)
    text = re.sub('秒', ' seconds', text)
    text = re.sub('個', '', text)
    return text

def translate_skill(text_jp, skill_level, group_id, data):
    try: skill_desc = data.translated_skills[group_id]['DescriptionEn']
    except KeyError: 
        skill_desc = text_jp
        #print(f'{group_id} translation is missing')
    else:

        for i in range(skill_level+1):
            try: skill_desc = data.translated_skills[group_id][f'ReplaceOnLevel{i}']
            except KeyError: pass
            
            try: skill_desc = skill_desc.removesuffix('.') + data.translated_skills[group_id][f'AddOnLevel{i}']
            except KeyError: pass

    variables = re.findall(r'\[c]\[[0-9A-Fa-f]{6}]([^\[]*)\[-]\[/c]', replace_units(text_jp))
    #replacement_count = len(re.findall(r'\$[0-9]{1}', skill_desc))
    #if len(variables) > 0 and len(variables) != replacement_count: print(f'Mismatched number of variables ({len(variables)}/{replacement_count}) in {text_jp} / {skill_desc}')

    for i in range(len(variables)):
        skill_desc = re.sub(f'\${i+1}', '{{SkillValue|' + variables[i] + '}}', skill_desc)
    return skill_desc



class Stats(object):
    def __init__(self, attack, defense, hp, healing, accuracy, evasion, critical_rate, critical_damage, stability,
                 firing_range, cc_strength, cc_resistance, city_affinity, outdoor_affinity, indoor_affinity):
        self.attack = attack
        self.defense = defense
        self.hp = hp
        self.healing = healing
        self.accuracy = accuracy
        self.evasion = evasion
        self.critical_rate = critical_rate
        self._critical_damage = critical_damage
        self.stability = stability
        self.firing_range = firing_range
        self.cc_strength = cc_strength
        self.cc_resistance = cc_resistance
        self.city_affinity = city_affinity
        self.outdoor_affinity = outdoor_affinity
        self.indoor_affinity = indoor_affinity

    @property
    def critical_damage(self):
        return self._critical_damage // 100

    @classmethod
    def from_data(cls, character_id, data):
        stats = data.characters_stats[character_id]
        return cls(
            (stats['AttackPower1'], stats['AttackPower100']),
            (stats['DefensePower1'], stats['DefensePower100']),
            (stats['MaxHP1'], stats['MaxHP100']),
            (stats['HealPower1'], stats['HealPower100']),
            stats['AccuracyPoint'],
            stats['DodgePoint'],
            stats['CriticalPoint'],
            stats['CriticalDamageRate'],
            stats['StabilityPoint'],
            stats['Range'],
            stats['OppressionPower'],
            stats['OppressionResist'],
            stats['StreetBattleAdaptation'],
            stats['OutdoorBattleAdaptation'],
            stats['IndoorBattleAdaptation']
        )


class Weapon(object):
    def __init__(self, id, image_path, attack_power, attack_power_100, max_hp, max_hp_100, heal_power, heal_power_100, stat_type, stat_value, rank2_desc, rank3_desc):
        self.id = id
        self.image_path = image_path
        self.attack_power = attack_power
        self.attack_power_100 = attack_power_100
        self.max_hp = max_hp
        self.max_hp_100 = max_hp_100
        self.heal_power = heal_power
        self.heal_power_100 = heal_power_100
        self.stat_type = stat_type
        self.stat_value = stat_value
        self.rank2_desc = rank2_desc
        self.rank3_desc = rank3_desc



    @classmethod
    def from_data(cls, character_id, data):
        weapon = data.weapons[character_id]
        stats = data.characters_stats[character_id]



        weapon_passive_skill = Skill.from_data(data.characters_skills[(character_id, 2, False)]['PassiveSkillGroupId'][0], data)

        #print (passive_skill.name_translated)
        #try: data.translated_skills[group[0]['GroupId']]['NameEn']
        #except KeyError: 
        #    skill_name_en = None
        #else:  
        #    skill_name_en = data.characters_skills[(character_id, False)]['PassiveSkillGroupId'][0] #data.translated_skills[group[0]['GroupId']]['NameEn']

        rank2_desc = f'Passive Skill changes to "{weapon_passive_skill.name_translated}"'

                
        def affinity_type(affinity_change_type):
            return {
                'Street': 'Urban',
                'Outdoor': 'Outdoor',
                'Indoor': 'Indoor'
            }[affinity_change_type]

        def offset_affinity(start_letter, offset_int):
            affinity_values = ['D','C','B','A','S','SS']
            index = affinity_values.index(start_letter)

            return affinity_values[index+offset_int]

        affinity_change_type =  weapon['StatType'][2].replace("BattleAdaptation_Base", "")
        old_affinity_letter =  stats[affinity_change_type+'BattleAdaptation']

        rank3_desc = f"{{{{Icon|{affinity_type(affinity_change_type)}|size=20}}}} {affinity_type(affinity_change_type)} area affinity {{{{Affinity|{offset_affinity(old_affinity_letter,weapon['StatValue'][2])}}}}} {offset_affinity(old_affinity_letter,weapon['StatValue'][2])}"
        #{{Icon|Urban|size=20}} Urban area affinity {{Affinity|SS}} SS


        return cls(
            weapon['Id'],
            weapon['ImagePath'],
            weapon['AttackPower'],
            weapon['AttackPower100'],
            weapon['MaxHP'],
            weapon['MaxHP100'],
            weapon['HealPower'],
            weapon['HealPower100'],
            weapon['StatType'],
            weapon['StatValue'],
            rank2_desc,
            rank3_desc
        )
        

class Favor(object):
    def __init__(self, levels):
        self.levels = levels

    @classmethod
    def from_data(cls, character_id, data):
        levels = {}

        def replace_statnames(stat_list):
            list_out = []
            
            for item in stat_list:
                item = re.sub('_Base', '', item)
                item = re.sub('Power', '', item)
                item = re.sub('Max', '', item)
                item = re.sub('Heal', 'Healing', item)

                list_out.append(item)     
            #return([re.sub('_Base', '', item) for item in stat_list])
            return (list_out)


        for favor_level in data.favor_levels:
            if favor_level[0] == character_id:
                #print(replace_statnames(data.favor_levels[(character_id , favor_level[1])]['StatType']))
                levels[favor_level[1]] = {'stat_type':replace_statnames(data.favor_levels[(character_id , favor_level[1])]['StatType']), 'stat_value':data.favor_levels[(character_id , favor_level[1])]['StatValue']}  

        return cls(
            levels
        )


class MemoryLobby(object):
    def __init__(self, image, unlock_level):
        self.image = image
        self.unlock_level = unlock_level


    @classmethod
    def from_data(cls, character_id, data):
        try: lobby_data = data.memory_lobby[character_id]
        except KeyError: return cls( None, None )

        unlock_level = None
        for favor_reward in data.favor_rewards:
            if favor_reward[0] == character_id:
                if 'MemoryLobby' in data.favor_rewards[(character_id , favor_reward[1])]['RewardParcelType']: unlock_level = data.favor_rewards[(character_id , favor_reward[1])]['FavorRank']
        
        return cls(
            lobby_data['RewardTextureName'][lobby_data['RewardTextureName'].rfind('/')+1:],
            unlock_level
        )


class Momotalk(object):
    def __init__(self, levels):
        self.levels = levels

    @classmethod
    def from_data(cls, character_id, data):
        levels = []


        for favor_reward in data.favor_rewards:
            if favor_reward[0] == character_id:
                #print(data.favor_rewards[(character_id , favor_reward[1])]['FavorRank'])
                levels.append(favor_reward[1])  

        return cls(
            levels
        )