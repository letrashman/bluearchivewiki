import operator
import re


class Character(object):
    def __init__(self, name, dev_name, name_en, rarity, school, role, position, damage_type, armor_type, combat_class, weapon_type,
                 uses_cover, profile, normal_skill, ex_skill, passive_skill, sub_skill, stats):
        self.name = name
        self.rarity = rarity
        self.school = school
        self._role = role
        self.position = position
        self._damage_type = damage_type
        self._armor_type = armor_type
        self._combat_class = combat_class
        self.weapon_type = weapon_type
        self._uses_cover = uses_cover
        self.profile = profile
        self.normal_skill = normal_skill
        self.ex_skill = ex_skill
        self.passive_skill = passive_skill
        self.sub_skill = sub_skill
        self.stats = stats

        self.dev_name = dev_name
        self.name_translated = name_en

        # Extra information
        self.filename = None
        self.how_to_obtain = None

    @property
    def role(self):
        return {
            'DamageDealer': 'Attacker',
            'Tanker': 'Tank',
            'Supporter': 'Support',
            'Healer': 'Healer'
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
            'Support': 'Support'
        }[self._combat_class]

    @property
    def uses_cover(self):
        return 'Yes' if self._uses_cover else 'No'

    @classmethod
    def from_data(cls, character_id, data):
        character = data.characters[character_id]
        character_ai = data.characters_ai[character['CharacterAIId']]
        return cls(
            data.characters_localization[character_id]['PersonalNameJp'],
            character['DevName'],
            data.translated_characters[character_id]['PersonalNameEn'],
            character['DefaultStarGrade'],
            character['School'],
            character['TacticRole'],
            character['TacticRange'],
            character['BulletType'],
            character['ArmorType'],
            character['SquadType'],
            character['WeaponType'],
            character_ai['CanUseObstacleOfKneelMotion'] or character_ai['CanUseObstacleOfStandMotion'],
            Profile.from_data(character_id, data),
            Skill.from_data(data.characters_skills[(character_id, False)]['PublicSkillGroupId'][0], data),
            Skill.from_data(data.characters_skills[(character_id, False)]['ExSkillGroupId'][0], data, 5),
            Skill.from_data(data.characters_skills[(character_id, False)]['PassiveSkillGroupId'][0], data),
            Skill.from_data(data.characters_skills[(character_id, False)]['ExtraPassiveSkillGroupId'][0], data),
            Stats.from_data(character_id, data)
        )


class Profile(object):
    def __init__(self, full_name, age, birthday, height, hobbies, illustrator, voice, introduction, reading):
        self.full_name = full_name
        self._age = age
        self._birthday = birthday
        self.height = height
        self.hobbies = hobbies
        self.illustrator = illustrator
        self.voice = voice
        self.introduction = introduction
        self.reading = reading

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
        return cls(
            f'{profile["FamilyNameJp"]} {profile["PersonalNameJp"]}',
            profile['CharacterAgeJp'],
            profile['BirthDay'],
            profile['CharHeightJp'],
            profile['HobbyJp'],
            profile['ArtistNameJp'],
            profile['CharacterVoiceJp'],
            profile['ProfileIntroductionJp'],
            f'{profile["FamilyNameRubyJp"]} {profile["PersonalNameJp"]}'
        )


class Skill(object):
    def __init__(self, name, name_translated, icon, levels, description_general, damage_type):
        self.name = name
        self.icon = icon
        self.levels = levels
        self._damage_type = damage_type

        # Extra information
        self.name_translated = name_translated
        self.description_general = description_general
        #self.max_level = 10

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


        def replace_units(text):
            text = re.sub('回', '', text)
            text = re.sub('つ', '', text)
            text = re.sub('秒', ' seconds', text)
            return text


        def translate_skill(text_jp, skill_level, group_id):
            try: skill_desc = data.translated_skills[group_id]['DescriptionEn']
            except KeyError: 
                skill_desc = text_jp
                #print(f'{group_id} translation is missing')
            else:
                for i in range(skill_level+1):
                    try: skill_desc = skill_desc.removesuffix('.') + data.translated_skills[group_id][f'AddOnLevel{i}']
                    except KeyError: False

            variables = re.findall(r'\[c]\[[0-9A-Fa-f]{6}]([^\[]*)\[-]\[/c]', replace_units(text_jp))
            for i in range(len(variables)):
                skill_desc = re.sub(f'\${i+1}', '{{SkillValue|' + variables[i] + '}}', skill_desc)
            return skill_desc


        def format_description(levels, text_en):
            start_variables = re.findall(r'\{\{SkillValue\|([^\}\[]+)\}\}',  levels[0][0])
            end_variables = re.findall(r'\{\{SkillValue\|([^\}\[]+)\}\}',  levels[max_level-1][0])

            for i in range(len(end_variables)):
                try: stripped_start = re.findall(r'([0-9.]+).*', start_variables[i])
                except IndexError: 
                    start_variables.append(0)
                    stripped_start = [0]

                range_text = start_variables[i] != end_variables[i] and f'{stripped_start[0]}~{end_variables[i]}' or f'{end_variables[i]}'
                text_en = re.sub(f'\${i+1}', '{{SkillValue|' + range_text + '}}', text_en)
            return text_en


        levels = [
            (translate_skill(data.skills_localization[level['LocalizeSkillId']]['DescriptionJp'], level['Level'], group_id), level['SkillCost'])
            for level
            in sorted(group, key=operator.itemgetter('Level'))
        ]
        

        text_general = translate_skill(levels[9][0], max_level, group_id)
        description_general = format_description(levels, text_general)


        try: data.translated_skills[group[0]['GroupId']]['NameEn']
        except KeyError: 
            skill_name_en = None
        else:  
            skill_name_en = data.translated_skills[group[0]['GroupId']]['NameEn']


        return cls(
            data.skills_localization[group[0]['LocalizeSkillId']]['NameJp'],
            skill_name_en,
            group[0]['IconName'].rsplit('/', 1)[-1],
            levels,
            description_general,
            group[0]['BulletType']
        )

        



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
