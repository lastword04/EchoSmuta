from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from .....settings import settings
from ...schemas import GlobalCharacterExperienceSettingsCreateSchema, GlobalCharacterExperienceSettingsReadSchema
from ...services.settings.experience_settings import GlobalCharacterExperienceSettingsServiceProtocol 


class InitializeGlobalCharacterExperienceSettingsUseCaseProtocol(UseCaseProtocol[list[GlobalCharacterExperienceSettingsReadSchema]]):
    async def __call__(self: Self) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        ...


class InitializeGlobalCharacterExperienceSettingsUseCase(InitializeGlobalCharacterExperienceSettingsUseCaseProtocol):
    def __init__(self: Self, service: GlobalCharacterExperienceSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[GlobalCharacterExperienceSettingsReadSchema]:
         
        experience_settings = await self.service.get_all()
        if len(experience_settings) > 0:
            return experience_settings

        default_experience_settings = self._get_default_experience_settings()
        return await self.service.bulk_create(default_experience_settings)


    def _get_default_experience_settings(self: Self) -> list[GlobalCharacterExperienceSettingsCreateSchema]:

        return [

        
        
         
        GlobalCharacterExperienceSettingsCreateSchema(level=1, up=0, experience=100, base=10, weapon_skill=0, race_parameter=2, skills=2, ducats=50, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=1, up=1, experience=200, base=10, weapon_skill=0, race_parameter=0, skills=1, ducats=10, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=1, up=2, experience=300, base=10, weapon_skill=0, race_parameter=0, skills=1, ducats=10, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=1, up=3, experience=400, base=10, weapon_skill=0, race_parameter=0, skills=1, ducats=10, endurance=0, intelligence=0),
            
         
        GlobalCharacterExperienceSettingsCreateSchema(level=2, up=0, experience=500, base=15, weapon_skill=0, race_parameter=2, skills=2, ducats=150, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=2, up=1, experience=700, base=15, weapon_skill=0, race_parameter=0, skills=1, ducats=15, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=2, up=2, experience=900, base=15, weapon_skill=0, race_parameter=0, skills=1, ducats=15, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=2, up=3, experience=1100, base=15, weapon_skill=0, race_parameter=0, skills=1, ducats=15, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=3, up=0, experience=1300, base=20, weapon_skill=1, race_parameter=2, skills=2, ducats=275, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=3, up=1, experience=1600, base=20, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=3, up=2, experience=1900, base=20, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=3, up=3, experience=2200, base=20, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=4, up=0, experience=2500, base=25, weapon_skill=1, race_parameter=2, skills=2, ducats=500, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=4, up=1, experience=3400, base=25, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=4, up=2, experience=4300, base=25, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=4, up=3, experience=5200, base=25, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=4, up=4, experience=6100, base=25, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=4, up=5, experience=7000, base=25, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=0, experience=8100, base=30, weapon_skill=1, race_parameter=2, skills=2, ducats=250, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=1, experience=9000, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=2, experience=9900, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=3, experience=10800, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=4, experience=11700, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=5, experience=12600, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=6, experience=13500, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=7, experience=14400, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=8, experience=15300, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=9, experience=16200, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=10, experience=17100, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=11, experience=18000, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=12, experience=18900, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=5, up=13, experience=19800, base=30, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=0, experience=20700, base=35, weapon_skill=1, race_parameter=2, skills=2, ducats=270, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=1, experience=21750, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=2, experience=22800, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=3, experience=23950, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=4, experience=25000, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=5, experience=26050, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=6, experience=27100, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=7, experience=28050, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=8, experience=29100, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=9, experience=30150, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=10, experience=31200, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=11, experience=32250, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=12, experience=33300, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=13, experience=34350, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=6, up=14, experience=35400, base=35, weapon_skill=0, race_parameter=0, skills=1, ducats=25, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=0, experience=36450, base=40, weapon_skill=1, race_parameter=2, skills=2, ducats=310, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=1, experience=37850, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=2, experience=39250, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=3, experience=40650, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=4, experience=42050, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=5, experience=43450, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=6, experience=44850, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=7, experience=46250, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=8, experience=47650, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=9, experience=49050, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=10, experience=50450, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=11, experience=51850, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=12, experience=53250, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=13, experience=54650, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=7, up=14, experience=56050, base=40, weapon_skill=0, race_parameter=0, skills=1, ducats=40, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=8, up=0, experience=57450, base=45, weapon_skill=1, race_parameter=2, skills=2, ducats=370, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=8, up=1, experience=61950, base=45, weapon_skill=0, race_parameter=0, skills=1, ducats=100, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=8, up=2, experience=70950, base=45, weapon_skill=0, race_parameter=0, skills=1, ducats=200, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=8, up=3, experience=82200, base=45, weapon_skill=0, race_parameter=0, skills=1, ducats=250, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=8, up=4, experience=91200, base=45, weapon_skill=0, race_parameter=0, skills=1, ducats=200, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=8, up=5, experience=95700, base=45, weapon_skill=0, race_parameter=0, skills=1, ducats=100, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=0, experience=102450, base=50, weapon_skill=1, race_parameter=2, skills=2, ducats=400, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=1, experience=112450, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=150, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=2, experience=125000, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=100, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=3, experience=140000, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=50, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=4, experience=155000, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=50, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=5, experience=170000, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=100, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=6, experience=185000, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=100, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=7, experience=200000, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=50, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=9, up=8, experience=215000, base=50, weapon_skill=0, race_parameter=0, skills=1, ducats=50, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=0, experience=230000, base=55, weapon_skill=1, race_parameter=2, skills=2, ducats=400, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=1, experience=240000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=2, experience=250000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=3, experience=260000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=4, experience=285000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=35, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=5, experience=300000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=6, experience=335000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=50, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=7, experience=350000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=8, experience=375000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=35, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=9, experience=385000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=10, up=10, experience=395000, base=55, weapon_skill=0, race_parameter=0, skills=1, ducats=20, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=0, experience=500000, base=60, weapon_skill=1, race_parameter=2, skills=2, ducats=450, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=1, experience=550000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=2, experience=600000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=3, experience=650000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=4, experience=700000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=5, experience=750000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=200, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=6, experience=800000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=7, experience=850000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=11, up=8, experience=900000, base=60, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=0, experience=1000000, base=65, weapon_skill=1, race_parameter=2, skills=2, ducats=500, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=1, experience=1100000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=2, experience=1200000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=3, experience=1300000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=4, experience=1400000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=5, experience=1500000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=6, experience=1600000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=7, experience=1700000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=8, experience=1800000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=12, up=9, experience=1900000, base=65, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=0, experience=2000000, base=70, weapon_skill=1, race_parameter=2, skills=2, ducats=1000, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=1, experience=2200000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=2, experience=2400000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=3, experience=2600000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=4, experience=2800000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=5, experience=3000000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=6, experience=3200000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=7, experience=3400000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=8, experience=3600000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=13, up=9, experience=3800000, base=70, weapon_skill=0, race_parameter=0, skills=1, ducats=0, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=0, experience=4000000, base=75, weapon_skill=1, race_parameter=2, skills=2, ducats=2000, endurance=1, intelligence=1),
        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=1, experience=4500000, base=75, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=2, experience=5000000, base=75, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=3, experience=5500000, base=75, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=4, experience=6000000, base=75, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=5, experience=6500000, base=75, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=6, experience=7000000, base=75, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),
        GlobalCharacterExperienceSettingsCreateSchema(level=14, up=7, experience=7500000, base=75, weapon_skill=0, race_parameter=0, skills=1, ducats=1000, endurance=0, intelligence=0),

        GlobalCharacterExperienceSettingsCreateSchema(level=15, up=0, experience=8000000, base=80, weapon_skill=1, race_parameter=2, skills=2, ducats=2500, endurance=1, intelligence=1),
  

        ]
                

