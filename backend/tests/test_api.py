"""Счастливый путь API карточки."""

from httpx import AsyncClient

from tests.conftest import DEMO_INN


async def test_summary_returns_card(client: AsyncClient) -> None:
    response = await client.get(f"/v1/company/{DEMO_INN}/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["inn"] == DEMO_INN
    assert payload["name"] == "ООО «Ромашка»"
    assert payload["status"] == "Действующее"
    assert payload["main_okved_code"] == "62.01"
    assert payload["revenue"] == 128_500_000
    assert payload["section_counts"]["court_cases"] == 12
    assert payload["section_counts"]["changes"] == 21


async def test_summary_unknown_inn_returns_404(client: AsyncClient) -> None:
    response = await client.get("/v1/company/9999999999/summary")

    assert response.status_code == 404


async def test_section_returns_items(client: AsyncClient) -> None:
    response = await client.get(f"/v1/company/{DEMO_INN}/section/court-cases")

    assert response.status_code == 200
    payload = response.json()
    assert payload["section"] == "court-cases"
    assert payload["total"] == 12
    assert len(payload["items"]) == 12
    assert payload["items"][0]["case_number"].startswith("А77-")


async def test_unknown_section_returns_400(client: AsyncClient) -> None:
    response = await client.get(f"/v1/company/{DEMO_INN}/section/bankruptcy")

    assert response.status_code == 400


async def test_debug_stats_counts_sql_queries(client: AsyncClient) -> None:
    await client.post("/debug/reset")
    await client.get(f"/v1/company/{DEMO_INN}/summary")

    stats = (await client.get("/debug/stats")).json()

    assert stats["sql_queries_total"] > 0
    assert stats["sql_queries_by_endpoint"]["/v1/company/{inn}/summary"] > 0


async def test_ai_description_is_generated(client: AsyncClient) -> None:
    """Долгий тест: дёргает настоящий llm-mock с его латентностью."""
    response = await client.get(f"/v1/company/{DEMO_INN}/ai-description")

    assert response.status_code == 200
    payload = response.json()
    assert payload["inn"] == DEMO_INN
    assert "## Финансовое состояние" in payload["description"]
    assert payload["is_llm"] is True
