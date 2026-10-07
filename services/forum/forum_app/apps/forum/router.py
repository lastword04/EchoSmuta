import uuid
from fastapi import APIRouter, Depends, Path, Query
from shared.schemas.auth import UserTokenDataReadSchema
from ...core.depends import get_user_token_payload
from .use_cases.get_all_forums import GetAllForumUseCaseProtocol
from .use_cases.get_paginate_topic import GetTopicsByForumWithStatsUseCaseProtocol
from .use_cases.create_topic import CreateTopicUseCaseProtocol
from .use_cases.update_topic import UpdateTopicUseCaseProtocol
from .use_cases.add_view_for_topic import AddViewForTopicUseCaseProtocol
from .use_cases.delete_topic import DeleteTopicUseCaseProtocol
from .use_cases.create_comment import CreateCommentUseCaseProtocol
from .use_cases.get_comments import GetCommentsByTopicWithCharacterNamesUseCaseProtocol
from .use_cases.auth_forum import AuthForumUseCaseProtocol
from .use_cases.create_topic_and_comment import CreateTopicAndCommentUseCaseProtocol
from .depends import (
    get_all_forum_use_case,
    get_topics_by_forum_with_stats_use_case,
    get_create_topic_use_case,
    get_update_topic_use_case,
    get_delete_topic_use_case,
    get_add_views_use_case,
    get_create_comment_use_case,
    get_comments_by_topic_with_character_names_use_case,
    get_auth_forum_use_case,
    get_create_comment_and_topic_use_case
)
from .schemas import (
    ForumWithStatsAndCharacterNames,
    TopicWithStatsAndCharacterNamesPaginateSchema,
    TopicCreateSchema,
    TopicReadSchema,
    TopicUpdateSchema,
    CommentReadDBSchema,
    CommentCreateSchema,
    CommentReadWithCharacterNameSchema,
    CommentReadWithCharacterNamePaginateSchema,
    TopicCommentCreateSchema,
    TopicCommentReadSchema
)


router = APIRouter(prefix='/api/forum', tags=['Forum'])

@router.head('/auth', status_code=204)
async def auth_forum(
    token_data: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: AuthForumUseCaseProtocol = Depends(get_auth_forum_use_case)
) -> None:
    await use_case(token_data=token_data)

@router.get('/', response_model=list[ForumWithStatsAndCharacterNames], status_code=200)
async def get_all_forums(use_case: GetAllForumUseCaseProtocol = Depends(get_all_forum_use_case)) -> list[ForumWithStatsAndCharacterNames]:
    result = await use_case()
    return result

@router.get('/{forum_id}/topics', response_model=TopicWithStatsAndCharacterNamesPaginateSchema, status_code=200)
async def get_topics_by_forum_with_stats(
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    limit: int = Query(10, ge=1, le=100, description="Количество элементов на страницу"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    use_case: GetTopicsByForumWithStatsUseCaseProtocol = Depends(get_topics_by_forum_with_stats_use_case)
) -> TopicWithStatsAndCharacterNamesPaginateSchema:
    result = await use_case(forum_id=forum_id, limit=limit, offset=offset)
    return result

@router.post('/{forum_id}/topics', response_model=TopicReadSchema, status_code=201)
async def create_topic(
    topic: TopicCreateSchema,
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    token_data: UserTokenDataReadSchema = Depends(get_user_token_payload),
    create_topic_use_case: CreateTopicUseCaseProtocol = Depends(get_create_topic_use_case)
) -> TopicReadSchema:
    return await create_topic_use_case(forum_id, topic, token_data)

@router.post('/{forum_id}/topics-comment', response_model=TopicCommentReadSchema, status_code=201)
async def create_topic_and_comment(
    data: TopicCommentCreateSchema,
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    token_data: UserTokenDataReadSchema = Depends(get_user_token_payload),
    create_topic_and_comment_use_case: CreateTopicAndCommentUseCaseProtocol = Depends(get_create_comment_and_topic_use_case)
) -> TopicCommentReadSchema:
    return await create_topic_and_comment_use_case(forum_id, data, token_data)

@router.put('/{forum_id}/topics/{topic_id}', response_model=TopicReadSchema, status_code=200)
async def update_topic(
    topic: TopicUpdateSchema,
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    topic_id: uuid.UUID = Path(..., description="ID темы"),
    token_data: UserTokenDataReadSchema = Depends(get_user_token_payload),
    update_topic_use_case: UpdateTopicUseCaseProtocol = Depends(get_update_topic_use_case)
) -> TopicReadSchema:
    return await update_topic_use_case(forum_id, topic_id, topic, token_data)

@router.delete('/{forum_id}/topics/{topic_id}', response_model=None, status_code=204)
async def delete_topic(
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    topic_id: uuid.UUID = Path(..., description="ID темы"),
    token_data: UserTokenDataReadSchema = Depends(get_user_token_payload),
    delete_topic_use_case: DeleteTopicUseCaseProtocol = Depends(get_delete_topic_use_case)
) -> None:
    return await delete_topic_use_case(topic_id, token_data)

@router.post('/{forum_id}/topics/{topic_id}/activity', response_model=None, status_code=204)
async def visit_topic(
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    topic_id: uuid.UUID = Path(..., description="ID темы"),
    visit_topic_use_case: AddViewForTopicUseCaseProtocol = Depends(get_add_views_use_case)
) -> None:
    return await visit_topic_use_case(topic_id)


@router.post('/{forum_id}/topics/{topic_id}/comments', response_model=CommentReadWithCharacterNameSchema, status_code=200)
async def create_comment(
    data: CommentCreateSchema,
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    topic_id: uuid.UUID = Path(..., description="ID темы"),
    token_data: UserTokenDataReadSchema = Depends(get_user_token_payload),
    create_comment_use_case: CreateCommentUseCaseProtocol = Depends(get_create_comment_use_case)
) -> CommentReadDBSchema:
    return await create_comment_use_case(forum_id, topic_id, data, token_data)


@router.get('/{forum_id}/topics/{topic_id}/comments', response_model=CommentReadWithCharacterNamePaginateSchema, status_code=200)
async def get_comments_by_topic_with_character_names(
    forum_id: uuid.UUID = Path(..., description="ID форума"),
    topic_id: uuid.UUID = Path(..., description="ID темы"),
    limit: int = Query(10, ge=1, le=100, description="Количество элементов на страницу"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    get_comments_by_topic_with_character_names_use_case: GetCommentsByTopicWithCharacterNamesUseCaseProtocol = Depends(get_comments_by_topic_with_character_names_use_case)
) -> CommentReadWithCharacterNamePaginateSchema:
    return await get_comments_by_topic_with_character_names_use_case(topic_id, limit, offset)