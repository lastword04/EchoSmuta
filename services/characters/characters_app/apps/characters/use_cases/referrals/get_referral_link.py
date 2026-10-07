from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...schemas import ReferralLinkResponseSchema, ReferralLinkWithReferralsAndUrlReadSchema
from ...services.referrals.referral_link import ReferralLinkServiceProtocol
from ...services.character.characters import CharacterServiceProtocol


class GetReferralLinkUseCaseProtocol(UseCaseProtocol[ReferralLinkResponseSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> ReferralLinkResponseSchema:
        ...


class GetReferralLinkUseCase(GetReferralLinkUseCaseProtocol):
    def __init__(self: Self, service: ReferralLinkServiceProtocol,
                 character_service: CharacterServiceProtocol):
        self.service = service
        self.character_service = character_service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> ReferralLinkResponseSchema:
        # Получаем реферальную ссылку с рефералами и URL
        referral_link_with_data = await self.service.get_referral_link_by_referrer_id(token.user_id)
        
        # Собираем список user_id из рефералов
        user_ids = [referral.referred_user_id for referral in referral_link_with_data.referrals]
        
        # Получаем имена пользователей
        users = await self.character_service.get_simple_main_by_user_ids(user_ids)
        
        # Создаем словарь user_id -> name для быстрого поиска
        user_names_dict = {user.user_id: user.name for user in users.characters}

        # Преобразуем рефералов в нужный формат
        referrals_with_names = []
        for referral in referral_link_with_data.referrals:
            referral_with_name = {
                **referral.model_dump(),
                'referred_user_name': user_names_dict.get(referral.referred_user_id, 'Unknown')
            }
            referrals_with_names.append(referral_with_name)
        
        # Создаем и возвращаем финальную схему
        response_data = {
            **referral_link_with_data.model_dump(exclude={'referrals'}),
            'referrals': referrals_with_names
        }
        
        return ReferralLinkResponseSchema.model_validate(response_data)