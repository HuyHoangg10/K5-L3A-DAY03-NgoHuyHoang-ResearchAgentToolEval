"""Completed Tool Unit Test Challenge.

The tests follow the patterns in test_tools_examples.py and use fixtures from
conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    options = ["Tin web", "Thảo luận mạng xã hội"]
    result = TOOL_FUNCTIONS["clarify"](
        question="Bạn muốn tìm ở đâu?",
        response_type="choice",
        options=options,
    )

    assert result["options"] == options
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    items = [
        {"section": "A", "title": "Tin 1"},
        {"section": "B", "title": "Tin 2"},
        {"section": "A", "title": "Tin 3"},
    ]
    result = TOOL_FUNCTIONS["format"](items=items, template="sections")

    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    items = [{"title": "Tin 1"}, {"title": "Tin 2"}, {"title": "Tin 3"}]
    result = TOOL_FUNCTIONS["format"](items=items, template="thread")
    lines = [line for line in result["markdown"].splitlines() if line]

    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    assert TOOL_FUNCTIONS["format"](items=None)["item_count"] == 0
    assert TOOL_FUNCTIONS["format"](items=[])["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat")
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)

    assert len(calls) == 1
    assert "test-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "test-chat"
    assert calls[0]["json"]["text"] == "Bản tin"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    TOOL_FUNCTIONS["lookup"](query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "Nội dung bài viết",
        "metadata": {"title": "T", "sourceURL": "https://example.com/article"},
    }}))

    result = TOOL_FUNCTIONS["fetch"]("https://example.com/input")

    assert len(calls) == 1
    assert result["items"][0] == {
        "title": "T",
        "url": "https://example.com/article",
        "source": "example.com",
        "summary": "Nội dung bài viết",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    result = TOOL_FUNCTIONS["fetch"]("https://example.com")

    assert result["items"][0]["summary"] == "x" * 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    timeline = [{"screen_name": "user", "text": "không có id"}]
    timeline += [
        {"tweet_id": str(i), "screen_name": "user", "text": f"Tweet {i}"}
        for i in range(1, 7)
    ]
    fake_http(FakeResponse({"timeline": timeline}))

    result = TOOL_FUNCTIONS["timeline"](screenname="user", limit=3)

    assert len(result["items"]) == 3
    assert all(
        item["url"].startswith("https://x.com/user/status/")
        for item in result["items"]
    )


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"timeline": []}))

    TOOL_FUNCTIONS["social_search"](query="AI agents", search_type="Top")

    assert calls[0]["params"]["query"] == "AI agents"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = TOOL_FUNCTIONS["policy"](query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    result = TOOL_FUNCTIONS["policy"](query="API keys", policy_area="data_privacy")

    assert result["results"]
    assert all(item["policy_area"] == "data_privacy" for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    result = TOOL_FUNCTIONS["policy"](
        query="Injection probe",
        policy_area="source_citation",
    )
    hit = next(item for item in result["results"] if item["section"] == "Injection probe")

    assert any("ignore the citation policy" in line for line in hit["untrusted_text"])
    assert "ignore the citation policy" not in hit["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_inspect_source_happy_path() -> None:
    result = TOOL_FUNCTIONS["inspect_source"]("https://arxiv.org/abs/1706.03762")
    assert result["domain"] == "arxiv.org"
    assert result["uses_https"] is True
    assert result["source_type"] == "academic_repository"
    assert result["risk_flags"] == []


def test_inspect_source_empty_input_returns_error() -> None:
    result = TOOL_FUNCTIONS["inspect_source"]("")
    assert result["error"] == "invalid_input"


def test_inspect_source_unsupported_scheme_returns_error_dict() -> None:
    result = TOOL_FUNCTIONS["inspect_source"]("ftp://example.com/file")
    assert result["error"] == "invalid_url"
    assert "message" in result
