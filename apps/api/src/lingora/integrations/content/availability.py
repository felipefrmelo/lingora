import httpx

from lingora.integrations.content.govuk import canonical_url
from lingora.modules.learning.contracts import ContentView
from lingora.modules.learning.provider import Generated, GenerationFailure, LessonProvider


class AvailableSourceProvider:
    """Check only the known source host before paying for generation; never follow redirects."""

    def __init__(self, provider: LessonProvider) -> None:
        self.provider = provider

    async def generate(self, context: dict[str, object]) -> Generated:
        source = ContentView.model_validate(context["source"])
        url = canonical_url(source.url)
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                response = await client.head(url)
        except httpx.HTTPError:
            raise GenerationFailure("source_check_failed", retryable=True) from None
        if response.status_code != 200:
            raise GenerationFailure(
                "source_unavailable"
                if response.status_code in {404, 410} or 300 <= response.status_code < 400
                else "source_check_failed",
                retryable=response.status_code >= 500 or response.status_code == 429,
            )
        return await self.provider.generate(context)
