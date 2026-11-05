"""Operator-only commands; no unauthenticated administrative HTTP surface."""

import argparse
import asyncio
import json
import time
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import update

from lingora.core.config import Settings
from lingora.infrastructure.database import Database
from lingora.integrations.content.availability import AvailableSourceProvider
from lingora.integrations.content.govuk import ingest
from lingora.integrations.openai.lessons import OpenAILessonProvider
from lingora.modules.learning.contracts import ContentView
from lingora.modules.learning.models import Content
from lingora.modules.learning.provider import GenerationFailure
from lingora.modules.learning.worker import run_once


async def main() -> None:
    parser = argparse.ArgumentParser(description="Lingora content ingestion and lesson worker")
    parser.add_argument("command", choices=["ingest", "worker", "hide", "evaluate"])
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--content-id", type=UUID)
    parser.add_argument("--level", choices=["A1", "A2", "B1", "B2", "C1", "C2"], default="A2")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    settings = Settings()
    database = Database(settings)
    provider = AvailableSourceProvider(OpenAILessonProvider(settings))
    last_ingestion = 0.0
    try:
        if args.command == "evaluate":
            if not args.content_id or not settings.openai_api_key.get_secret_value():
                parser.error("evaluate requires --content-id and OPENAI_API_KEY")
            async with database.sessions() as session:
                source = await session.get(Content, args.content_id)
                if source is None or not source.available:
                    parser.error("Content is unavailable")
                context: dict[str, object] = {
                    "source": ContentView.model_validate(source).model_dump(mode="json"),
                    "cefr": args.level,
                    "goals": [],
                    "interests": [],
                }
            try:
                result = await provider.generate(context)
            except GenerationFailure as error:
                print(
                    json.dumps(
                        {
                            "validated": False,
                            "failure_code": error.code,
                            "validation_checks": error.validation_checks,
                        }
                    )
                )
                raise SystemExit(1) from None
            if args.output:
                args.output.write_text(
                    json.dumps(
                        {
                            "context": context,
                            "document": result.document.model_dump(),
                            "model": result.model,
                            "input_tokens": result.input_tokens,
                            "output_tokens": result.output_tokens,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n"
                )
            print(
                json.dumps(
                    {
                        "validated": True,
                        "model": result.model,
                        "input_tokens": result.input_tokens,
                        "output_tokens": result.output_tokens,
                    }
                )
            )
            return
        if args.command == "hide":
            if not args.content_id:
                parser.error("hide requires --content-id")
            async with database.sessions() as session, session.begin():
                await session.execute(
                    update(Content).where(Content.id == args.content_id).values(available=False)
                )
            print("Content hidden from new lessons and catalog.")
            return
        if args.command == "worker" and not settings.openai_api_key.get_secret_value():
            parser.error("OPENAI_API_KEY is required for the worker")
        while True:
            if args.command == "ingest" or (
                not args.once and time.monotonic() - last_ingestion > 21600
            ):
                try:
                    async with database.sessions() as session, httpx.AsyncClient() as client:
                        count = await ingest(session, client)
                    print(json.dumps({"event": "content.ingested", "inserted": count}), flush=True)
                except Exception:
                    print(json.dumps({"event": "content.ingestion_failed"}), flush=True)
                    if args.command == "ingest":
                        raise SystemExit(1) from None
                last_ingestion = time.monotonic()
            if args.command == "ingest":
                return
            processed = await run_once(database.sessions, provider, settings.lesson_model)
            if args.once:
                return
            if not processed:
                await asyncio.sleep(2)
    finally:
        await database.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
