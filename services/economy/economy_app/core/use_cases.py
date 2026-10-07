from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T", covariant=True)


@runtime_checkable
class UseCaseProtocol(Protocol[T]):
    async def __call__(self) -> T:
        ...