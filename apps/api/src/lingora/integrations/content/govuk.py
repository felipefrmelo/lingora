"""Bounded ingestion of selected GOV.UK Atom briefs, not linked pages or media."""

import hashlib
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit

import httpx
from defusedxml.ElementTree import fromstring  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.learning.models import Content

LICENSE_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
FEEDS = {
    "space": "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=uk-space-agency",
    "environment": "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=environment-agency",
}
NS = {"a": "http://www.w3.org/2005/Atom"}


class PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "br", "div"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def plain(value: str) -> str:
    parser = PlainText()
    parser.feed(value)
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()


def canonical_url(value: str) -> str:
    url = urlsplit(value)
    if (
        url.scheme != "https"
        or url.netloc != "www.gov.uk"
        or not url.path.startswith("/government/news/")
    ):
        raise ValueError("Only selected GOV.UK news links are accepted")
    return urlunsplit(("https", "www.gov.uk", url.path.rstrip("/"), "", ""))


def parse_feed(body: bytes, topic: str) -> list[Content]:
    if len(body) > 1_000_000 or topic not in FEEDS:
        raise ValueError("Unsupported or oversized feed")
    root = fromstring(body)
    records: list[Content] = []
    for entry in root.findall("a:entry", NS)[:30]:
        try:
            title = plain(entry.findtext("a:title", "", NS))
            text = plain(entry.findtext("a:summary", "", NS) or entry.findtext("a:content", "", NS))
            link = entry.find("a:link[@rel='alternate']", NS)
            if link is None:
                link = entry.find("a:link", NS)
            if link is None:
                continue
            url = canonical_url(link.attrib.get("href", ""))
            published = datetime.fromisoformat(
                entry.findtext("a:published", "", NS) or entry.findtext("a:updated", "", NS)
            )
            if published.tzinfo is None or published > datetime.now(UTC):
                continue
            # Exclude briefs that explicitly declare incompatible/third-party rights.
            if (
                not 5 <= len(title) <= 300
                or not 40 <= len(text) <= 8000
                or re.search(r"all rights reserved|third.party copyright|©", text, re.I)
            ):
                continue
            fingerprint = hashlib.sha256(
                re.sub(r"\W+", "", (title + text).casefold()).encode()
            ).hexdigest()
            records.append(
                Content(
                    url=url,
                    title=title,
                    summary=text,
                    published_at=published,
                    source="GOV.UK",
                    topics=[topic, "science"],
                    license_name="OGL-3.0",
                    license_url=LICENSE_URL,
                    attribution=(
                        "Contains public sector information licensed under "
                        "the Open Government Licence v3.0."
                    ),
                    fingerprint=fingerprint,
                    available=True,
                )
            )
        except (ValueError, OverflowError):
            continue
    return records


async def ingest(session: AsyncSession, client: httpx.AsyncClient) -> int:
    count = 0
    for topic, url in FEEDS.items():
        async with client.stream(
            "GET",
            url,
            follow_redirects=False,
            timeout=15,
            headers={"User-Agent": "Lingora/0.1 (+https://github.com/felipefrmelo/lingora)"},
        ) as response:
            response.raise_for_status()
            data = bytearray()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > 1_000_000:
                    raise ValueError("Feed exceeds size limit")
        records = parse_feed(bytes(data), topic)
        async with session.begin():
            for record in records:
                # Immutable brief snapshots. Edits are deliberately not silently propagated.
                values = {
                    column.name: getattr(record, column.name)
                    for column in Content.__table__.columns
                    if column.name not in {"id", "fetched_at"}
                }
                result = await session.execute(
                    insert(Content).values(**values).on_conflict_do_nothing().returning(Content.id)
                )
                count += len(list(result.scalars()))
    return count
