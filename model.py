import itertools
import operator


class Character(object):
    def __init__(self, name, rarity, school, role, position, damage_type, armor_type, combat_class, weapon_type,
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
    def from_data(cls, character_id, data, tls):
        character = data.characters[character_id]
        character_ai = data.characters_ai[character['CharacterAIId']]
        return cls(
            data.characters_localization[character_id]['PersonalNameJp'],
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
            Skill.from_data(data.characters_skills[(character_id, False)]['PublicSkillGroupId'][0], data, tls),
            Skill.from_data(data.characters_skills[(character_id, False)]['ExSkillGroupId'][0], data, tls),
            Skill.from_data(data.characters_skills[(character_id, False)]['PassiveSkillGroupId'][0], data, tls),
            Skill.from_data(data.characters_skills[(character_id, False)]['ExtraPassiveSkillGroupId'][0], data, tls),
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


def _get_skill_upgrade_materials(level, data, tls):
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
            yield tls.items[id]['NameEn'], data.items[id]['Icon'].rsplit('/', 1)[-1], amount
        elif type_ == 'Currency':
            yield tls.currencies[id]['NameEn'], data.currencies[id]['Icon'].rsplit('/', 1)[-1], amount


class SkillLevel(object):
    def __init__(self, description, cost, materials):
        self.description = description
        self.cost = cost
        self.materials = materials

    @classmethod
    def from_data(cls, level, data, tls):
        return cls(
            data.skills_localization[level['LocalizeSkillId']]['DescriptionJp'],
            level['SkillCost'],
            list(_get_skill_upgrade_materials(level, data, tls))
        )


class Skill(object):
    def __init__(self, name, name_tl, icon, levels, damage_type):
        self.name = name
        self.name_tl = name_tl
        self.icon = icon
        self.levels = levels
        self._damage_type = damage_type

    @property
    def damage_type(self):
        return {
            'Explosion': 'Explosive',
            'Pierce': 'Penetration',
            'Mystic': 'Mystic'
        }[self._damage_type]

    @classmethod
    def from_data(cls, group_id, data, tls):
        group = [skill for skill in data.skills.values() if skill['GroupId'] == group_id]
        if not group:
            raise KeyError(group_id)

        return cls(
            data.skills_localization[group[0]['LocalizeSkillId']]['NameJp'],
            tls.skills[group[0]['GroupId']]['NameEn'],
            group[0]['IconName'].rsplit('/', 1)[-1],
            [SkillLevel.from_data(level, data, tls) for level in sorted(group, key=operator.itemgetter('Level'))],
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
