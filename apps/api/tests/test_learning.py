import copy
from typing import Any

import httpx
import pytest
from defusedxml.common import DefusedXmlException  # pyright: ignore[reportMissingTypeStubs]
from fastapi import FastAPI
from pydantic import SecretStr, ValidationError

from lingora.core.config import Settings
from lingora.integrations.content.govuk import canonical_url, parse_feed, plain
from lingora.integrations.openai.lessons import OpenAILessonProvider
from lingora.modules.learning.contracts import GenerateLesson, LessonDraft, SubmitAttempt, grade
from lingora.modules.learning.provider import GenerationFailure
from lingora.modules.learning.worker import cost_estimate
from tests.auth_support import TokenFactory
from tests.learning_support import lesson_data


def test_deterministic_grading_and_no_semantic_guessing() -> None:
    draft = LessonDraft.model_validate(lesson_data())
    answers = [
        ["a garden"],
        ["  PLANT  "],
        ["A person who helps", "A planned piece of work"],
        ["Ｊｕｎｅ"],
        ["meet"],
    ]
    assert all(x.correct for x in grade(draft, SubmitAttempt(answers=answers)))
    answers[3] = ["In June."]
    answers[2].reverse()
    results = grade(draft, SubmitAttempt(answers=answers))
    assert not results[2].correct and not results[3].correct
    assert sum(x.correct for x in results) == 3
    assert not any(x.correct for x in grade(draft, SubmitAttempt(answers=[[]] * 5)))


@pytest.mark.parametrize(
    "case",
    [
        "type",
        "evidence",
        "key",
        "matching",
        "vocabulary",
        "gap",
        "empty",
        "extras",
        "four_underscores",
        "long_answer",
        "duplicate_answer",
    ],
)
def test_invalid_generated_lessons_never_pass_validation(case: str) -> None:
    data = copy.deepcopy(lesson_data())
    match case:
        case "type":
            data["exercises"][0]["kind"] = "short_answer"
        case "evidence":
            data["exercises"][3]["evidence"] = "A fact not in this reading."
        case "key":
            data["exercises"][0]["correct_answers"] = ["A museum"]
        case "matching":
            data["exercises"][2]["correct_answers"] = ["Wrong", "Wrong"]
        case "vocabulary":
            data["vocabulary"][0]["term"] = "absent-word"
        case "gap":
            data["exercises"][1]["prompt"] = "No blank to complete"
        case "empty":
            data["exercises"][0]["explanation"] = ""
        case "extras":
            data["student_id"] = "other"
        case "four_underscores":
            data["exercises"][1]["prompt"] = "Volunteers will ____ trees."
        case "long_answer":
            data["exercises"][3]["correct_answers"] = [
                "An excessively long answer that is unsuitable for exact phrase matching"
            ]
        case "duplicate_answer":
            data["exercises"][3]["correct_answers"] = ["June", "june"]
        case _:
            raise AssertionError("Unknown validation case")
    with pytest.raises(ValidationError):
        LessonDraft.model_validate(data)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.gov.uk/government/news/a",
        "https://www.gov.uk.evil.test/government/news/a",
        "https://127.0.0.1/government/news/a",
        "https://www.gov.uk@evil.test/government/news/a",
        "https://www.gov.uk:443/government/news/a",
        "https://www.gov.uk/other",
    ],
)
def test_source_urls_are_allowlisted(url: str) -> None:
    with pytest.raises(ValueError):
        canonical_url(url)


def test_feed_license_filtering_and_html_safety() -> None:
    body = (
        b'<feed xmlns="http://www.w3.org/2005/Atom">'
        b"<entry>"
        b"<title>Space project announced</title>"
        b'<link href="https://www.gov.uk/government/news/project?utm_source=tracking"/>'
        b"<updated>2026-01-01T12:00:00Z</updated>"
        b"<summary>&lt;p&gt;A new space project will help scientists "
        b"learn about the world.&lt;/p&gt;</summary>"
        b"</entry>"
        b"</feed>"
    )
    rows = parse_feed(body, "space")
    assert len(rows) == 1
    assert rows[0].url.endswith("/project") and "?" not in rows[0].url
    assert rows[0].license_name == "OGL-3.0"
    assert parse_feed(body.replace(b"A new space", b"Third-party copyright: space"), "space") == []
    assert parse_feed(body.replace(b"www.gov.uk/", b"evil.test/"), "space") == []
    assert plain("<script>alert(1)</script><p>Hello <b>world</b></p>") == "Hello world"
    with pytest.raises(DefusedXmlException):
        parse_feed(b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>', "space")
    with pytest.raises(ValueError):
        parse_feed(b"x" * 1_000_001, "space")


def test_request_bounds_and_estimated_cost() -> None:
    with pytest.raises(ValidationError):
        GenerateLesson.model_validate({"content_id": "bad", "student_id": "other"})
    with pytest.raises(ValidationError):
        SubmitAttempt(answers=[["x" * 301]] * 5)
    assert cost_estimate("gpt-5-mini-2025-08-07", 1000, 100) == 450
    assert cost_estimate("unknown", 1000, 100) is None


@pytest.mark.parametrize("mode", ["valid", "invalid", "refused", "throttled"])
async def test_openai_adapter_uses_structured_private_bounded_requests(
    mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from openai import AsyncOpenAI

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(request.content)
        assert body["store"] is False and body["max_output_tokens"] == 7000
        assert body["text"]["format"]["strict"] is True
        assert "untrusted DATA" in body["instructions"]
        if mode == "throttled":
            return httpx.Response(429, json={"error": {"message": "private provider error"}})
        document = lesson_data() if mode == "valid" else {"bad": "private output"}
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 1,
                "model": "gpt-5-mini-2025-08-07",
                "status": "completed",
                "output": []
                if mode == "refused"
                else [
                    {
                        "type": "message",
                        "id": "msg_test",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {"type": "output_text", "text": json.dumps(document), "annotations": []}
                        ],
                    }
                ],
                "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            },
        )

    def factory(**kwargs: Any) -> AsyncOpenAI:
        return AsyncOpenAI(
            **kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )

    monkeypatch.setattr("lingora.integrations.openai.lessons.AsyncOpenAI", factory)
    provider = OpenAILessonProvider(Settings(openai_api_key=SecretStr("test-only")))
    if mode == "valid":
        result = await provider.generate(
            {
                "cefr": "B1",
                "source": {"title": "A garden", "summary": "A community is planning a garden."},
            }
        )
        assert result.input_tokens == 10 and len(result.document.exercises) == 5
    else:
        with pytest.raises(GenerationFailure) as error:
            await provider.generate(
                {
                    "cefr": "B1",
                    "source": {"title": "A garden", "summary": "A community is planning a garden."},
                }
            )
        assert "private" not in str(error.value)
        assert error.value.retryable is (mode == "throttled")


def test_source_attribution_is_assembled_verbatim_and_only_once() -> None:
    from lingora.modules.learning.contracts import assemble_lesson, reading_prefix

    context = {
        "source": {"title": "Original news title", "summary": "An exact licensed source brief."}
    }
    draft = LessonDraft.model_validate(lesson_data())
    result = assemble_lesson(draft, context)
    assert result.reading == reading_prefix(context) + draft.reading
    assert assemble_lesson(result, context).reading == result.reading


def test_worker_models_resolve_foreign_keys_in_a_fresh_process() -> None:
    import subprocess
    import sys

    # API tests import identity models first; the standalone worker must also work cold.
    script = (
        "from lingora.modules.learning.worker import claim; "
        "from lingora.modules.learning.models import LessonJob; "
        "assert all(key.column.table.name for key in LessonJob.__table__.foreign_keys)"
    )
    subprocess.run(  # noqa: S603 - fixed interpreter and test-authored script, no external input
        [sys.executable, "-c", script], check=True, capture_output=True, timeout=10
    )


def test_matching_presentation_does_not_reveal_model_key_order() -> None:
    from lingora.modules.learning.contracts import assemble_lesson

    data = lesson_data()
    data["exercises"][2]["options"] = data["exercises"][2]["correct_answers"].copy()
    draft = LessonDraft.model_validate(data)
    context = {"source": {"title": "Original news title", "summary": "A licensed brief."}}
    result = assemble_lesson(draft, context)
    assert result.exercises[2].options != result.exercises[2].correct_answers
    assert sorted(result.exercises[2].options) == sorted(result.exercises[2].correct_answers)
    assert result.exercises[2].correct_answers == draft.exercises[2].correct_answers


@pytest.mark.parametrize(
    "method,path,scope",
    [
        ("GET", "/api/v1/me/content", "profile:write"),
        ("POST", "/api/v1/me/lessons", "profile:read"),
        ("GET", "/api/v1/me/lessons/00000000-0000-0000-0000-000000000001", "profile:write"),
        ("GET", "/api/v1/me/lesson-jobs/00000000-0000-0000-0000-000000000001", "profile:write"),
        (
            "POST",
            "/api/v1/me/lessons/00000000-0000-0000-0000-000000000001/attempts",
            "profile:read",
        ),
        (
            "GET",
            "/api/v1/me/lessons/00000000-0000-0000-0000-000000000001/attempts",
            "profile:write",
        ),
    ],
)
async def test_learning_endpoints_require_their_scopes(
    authenticated_app: FastAPI, token_factory: TokenFactory, method: str, path: str, scope: str
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=authenticated_app), base_url="http://test"
    ) as client:
        response = await client.request(
            method, path, headers={"Authorization": "Bearer " + token_factory({"scope": scope})}
        )
    assert response.status_code == 403


@pytest.mark.parametrize("status", [200, 302, 403, 404, 429, 503])
async def test_source_availability_uses_only_bounded_head(
    status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import UTC, datetime
    from uuid import uuid4

    from lingora.integrations.content.availability import AvailableSourceProvider
    from lingora.modules.learning.contracts import ContentView
    from tests.learning_support import FakeProvider

    real_client = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "HEAD"
        assert str(request.url) == "https://www.gov.uk/government/news/example"
        assert "authorization" not in request.headers
        return httpx.Response(status, headers={"Location": "http://127.0.0.1/private"})

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        assert kwargs["timeout"] == 10 and kwargs["follow_redirects"] is False
        return real_client(**kwargs, transport=httpx.MockTransport(handler))

    monkeypatch.setattr("lingora.integrations.content.availability.httpx.AsyncClient", factory)
    source = ContentView(
        id=uuid4(),
        title="An example",
        url="https://www.gov.uk/government/news/example",
        published_at=datetime.now(UTC),
        source="GOV.UK",
        license_name="OGL-3.0",
        license_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        attribution="Public sector information under OGL v3.0.",
        summary="A public news brief.",
        topics=["space"],
    )
    fake = FakeProvider()
    provider = AvailableSourceProvider(fake)
    if status == 200:
        await provider.generate({"source": source.model_dump(mode="json")})
        assert fake.calls == 1
    else:
        with pytest.raises(GenerationFailure) as error:
            await provider.generate({"source": source.model_dump(mode="json")})
        assert error.value.retryable is (status in {429, 503})
        assert fake.calls == 0


async def test_worker_failures_never_print_private_database_diagnostics(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import sys

    from sqlalchemy.exc import OperationalError

    from lingora import learning_cli

    async def failure(*args: Any, **kwargs: Any) -> None:
        raise OperationalError(
            "private SQL", {"answer": "private student answer"}, Exception("private row contents")
        )

    monkeypatch.setattr(sys, "argv", ["lingora", "worker", "--once"])
    monkeypatch.setattr(
        learning_cli, "Settings", lambda: Settings(openai_api_key=SecretStr("test-only"))
    )
    monkeypatch.setattr(learning_cli, "run_once", failure)
    with pytest.raises(SystemExit) as error:
        await learning_cli.main()
    assert error.value.code == 1
    output = capsys.readouterr()
    assert "worker.operation_failed" in output.out
    assert "private" not in output.out + output.err


@pytest.mark.parametrize("supported", [True, False])
def test_text_questions_use_precise_quoted_evidence(supported: bool) -> None:
    from lingora.modules.learning.contracts import RawLesson, assemble_lesson

    data = lesson_data()
    data["exercises"][3]["prompt"] = "Name any month you can think of."
    data["exercises"][3]["correct_answers"] = ["June" if supported else "November", "January"]
    raw = RawLesson.model_validate(data)
    context = {"source": {"title": "Garden news", "summary": "A licensed brief."}}
    if not supported:
        with pytest.raises(ValueError):
            assemble_lesson(raw, context)
    else:
        result = assemble_lesson(raw, context)
        question = result.exercises[3]
        assert "The garden will open in ___." in question.prompt
        assert question.correct_answers == ["June"]
        assert "The garden will open in June." in question.explanation
        assert "Name any month" not in question.prompt
