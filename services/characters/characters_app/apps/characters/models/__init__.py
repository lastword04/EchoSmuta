"""
Пакет ORM-моделей приложения ``characters``.

Модели разбиты по доменным модулям, но все они реэкспортируются здесь,
чтобы сохранить обратную совместимость со старыми импортами вида::

    from .models import Character, Location, Referral
    from characters_app.apps.characters.models import *

Импорт всех подмодулей также гарантирует регистрацию всех таблиц
в ``Base.metadata`` (важно для Alembic).
"""

from .character import Character
from .info import CharacterInfo
from .skills import (
    CharacterAbilitySkills,
    AppliedCharacterHistory,
    CharacterDistributions,
)
from .economy import CurrencyType, CharacterCurrencyOperation
from .attachment import CharacterAttachmentSettings
from .settings import (
    RaceSettings,
    GlobalCharacterSettings,
    GlobalCharacterExperienceSettings,
    UserCharacterSettings,
    TransferValueCharactersSettings,
)
from .locations import City, Location
from .activity import CharacterActivity
from .trade_privileges import CharacterTradePrivilege
from .referrals import ReferralLink, Referral


__all__ = [
    'RaceSettings',
    'GlobalCharacterSettings',
    'GlobalCharacterExperienceSettings',
    'Character',
    'CharacterInfo',
    'CharacterAbilitySkills',
    'AppliedCharacterHistory',
    'CharacterDistributions',
    'CurrencyType',
    'CharacterCurrencyOperation',
    'CharacterAttachmentSettings',
    'UserCharacterSettings',
    'TransferValueCharactersSettings',
    'City',
    'Location',
    'CharacterActivity',
    'CharacterTradePrivilege',
    'ReferralLink',
    'Referral',
]
