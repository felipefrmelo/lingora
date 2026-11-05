from dataclasses import dataclass
from typing import Any, Protocol

from lingora.modules.learning.contracts import LessonDraft


@dataclass(frozen=True)
class Generated:
    document: LessonDraft
    model: str
    input_tokens: int
    output_tokens: int


class LessonProvider(Protocol):
    async def generate(self, context: dict[str, Any]) -> Generated: ...


class GenerationFailure(Exception):
    def __init__(
        self,
        code: str,
        retryable: bool = False,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        validation_checks: tuple[str, ...] = (),
    ) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.validation_checks = validation_checks
