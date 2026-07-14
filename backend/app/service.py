"""Бизнес-логика карточки компании."""

import hashlib
import logging
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_description import generate_description_with_review
from app.cache import (
    ai_description_key,
    ai_description_pattern,
    ai_feedback_key,
    cache_delete_pattern,
    cache_get,
    cache_incr,
    cache_set,
)
from app.config import settings
from app.db import Base
from app.models import SECTIONS, section_counts_key
from app.repository import CompanyRepository
from app.schemas import (
    AiDescriptionResponse,
    AiFeedbackResponse,
    AiVote,
    CompanyFacts,
    CompanySummary,
    SectionCounts,
)

logger = logging.getLogger(__name__)


class CompanyNotFound(Exception):
    def __init__(self, inn: str) -> None:
        super().__init__(inn)
        self.inn = inn


def facts_fingerprint(facts: CompanyFacts) -> str:
    """Отпечаток фактов карточки.

    Пока факты не изменились, описание переиспользуется; как только
    в карточке появилось новое дело или отчётность — ключ станет другим.
    """
    payload = facts.model_dump_json()
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


class CompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CompanyRepository(session)

    async def get_company_summary(self, inn: str) -> CompanySummary | None:
        company = await self.repo.get_company(inn)
        if company is None:
            return None

        okved = await self.repo.get_okved(company.main_okved_code)
        financials = await self.repo.get_latest_financials(inn)
        headcount = await self.repo.get_latest_headcount(inn)

        # Счётчики разделов считаем по одному запросу на раздел: у каждой
        # дочерней таблицы свой индекс по inn, запросы дешёвые, а список
        # разделов читается сверху вниз и легко расширяется.
        counts: dict[str, int] = {}
        for section in SECTIONS:
            counts[section_counts_key(section)] = await self.repo.count_section(inn, section)

        return CompanySummary(
            inn=company.inn,
            name=company.name,
            status=company.status,
            registration_date=company.registration_date,
            city=company.city,
            main_okved_code=company.main_okved_code,
            main_okved_name=okved.name if okved else "",
            revenue=financials.revenue if financials else None,
            profit=financials.profit if financials else None,
            headcount=headcount.headcount if headcount else None,
            section_counts=SectionCounts(**counts),
        )

    async def collect_facts(self, inn: str) -> CompanyFacts | None:
        """Собирает всё, на чём строится ИИ-описание."""
        company = await self.repo.get_company(inn)
        if company is None:
            return None

        okved = await self.repo.get_okved(company.main_okved_code)
        financials = await self.repo.get_latest_financials(inn)
        headcount = await self.repo.get_latest_headcount(inn)
        summary = await self.get_company_summary(inn)
        if summary is None:
            return None

        court_amount = await self.repo.sum_court_amount(inn)
        court_categories = await self.repo.top_court_categories(inn)
        enforcement_amount = await self.repo.sum_enforcement_amount(inn)
        contracts_amount = await self.repo.sum_contract_amount(inn)
        active_licenses = await self.repo.count_active_licenses(inn)
        violations = await self.repo.sum_inspection_violations(inn)
        key_relations = await self.repo.list_key_relations(inn)
        last_change_at = await self.repo.last_change_date(inn)

        return CompanyFacts(
            inn=company.inn,
            name=company.name,
            full_name=company.full_name,
            status=company.status,
            registration_date=company.registration_date,
            city=company.city,
            region=company.region,
            ceo_name=company.ceo_name,
            charter_capital=company.charter_capital,
            main_okved_code=company.main_okved_code,
            main_okved_name=okved.name if okved else "",
            revenue=financials.revenue if financials else None,
            profit=financials.profit if financials else None,
            revenue_year=financials.year if financials else None,
            headcount=headcount.headcount if headcount else None,
            section_counts=summary.section_counts,
            court_amount_total=court_amount,
            court_top_categories=court_categories,
            enforcement_amount_total=enforcement_amount,
            contracts_amount_total=contracts_amount,
            active_licenses=active_licenses,
            inspection_violations=violations,
            key_relations=key_relations,
            last_change_at=last_change_at,
        )

    async def get_ai_description(self, inn: str) -> AiDescriptionResponse:
        facts = await self.collect_facts(inn)
        if facts is None:
            raise CompanyNotFound(inn)

        # Ключ кэша содержит отпечаток фактов: описание, написанное по устаревшим
        # данным, просто перестаёт находиться — инвалидировать руками не нужно.
        fingerprint = facts_fingerprint(facts)
        cache_key = ai_description_key(inn, fingerprint)

        cached = await cache_get(cache_key)
        if cached is not None:
            return AiDescriptionResponse.model_validate({**cached, "cached": True})

        # Redis может быть холодным после рестарта — тогда берём описание из базы.
        stored = await self.repo.get_ai_description(inn)
        if stored is not None and stored.facts_hash == fingerprint:
            restored = AiDescriptionResponse(
                inn=inn,
                description=stored.description,
                generated_at=stored.generated_at,
                cached=True,
                score=stored.score,
                is_llm=stored.is_llm,
                history=list(stored.history or []),
            )
            await cache_set(
                cache_key,
                restored.model_dump(mode="json", exclude={"cached"}),
                settings.ai_cache_ttl_seconds,
            )
            return restored

        generated = await generate_description_with_review(facts)
        response = AiDescriptionResponse(
            inn=inn,
            description=generated.text,
            generated_at=datetime.now(timezone.utc),
            cached=False,
            score=generated.score,
            is_llm=generated.is_llm,
            history=generated.history,
        )

        # Шаблонную заглушку не сохраняем: как только модель снова начнёт отвечать,
        # пользователь должен увидеть нормальное описание, а не подсунутый текст.
        if generated.is_llm:
            await cache_set(
                cache_key,
                response.model_dump(mode="json", exclude={"cached"}),
                settings.ai_cache_ttl_seconds,
            )
            await self.repo.upsert_ai_description(
                inn=inn,
                description=response.description,
                facts_hash=fingerprint,
                score=response.score,
                is_llm=response.is_llm,
                model=generated.model,
                history=response.history,
                generated_at=response.generated_at,
            )
            await self.session.commit()

        return response

    async def register_ai_feedback(self, inn: str, vote: AiVote) -> AiFeedbackResponse:
        company = await self.repo.get_company(inn)
        if company is None:
            raise CompanyNotFound(inn)

        votes = await cache_incr(ai_feedback_key(inn, vote), settings.ai_feedback_ttl_seconds)

        if vote == "down" and votes >= settings.ai_dislikes_before_regeneration:
            # Несколько дизлайков подряд — текст неудачный. Сносим его из кэша,
            # чтобы следующий читатель получил свежую генерацию.
            removed = await cache_delete_pattern(ai_description_pattern(inn))
            logger.info("описание %s снято с кэша по дизлайкам, ключей: %s", inn, removed)
            return AiFeedbackResponse(
                inn=inn, vote=vote, votes=votes, triggered_regeneration=True
            )

        return AiFeedbackResponse(inn=inn, vote=vote, votes=votes, triggered_regeneration=False)

    async def get_section(
        self, inn: str, section: str, limit: int, offset: int
    ) -> tuple[int, Sequence[Base]]:
        company = await self.repo.get_company(inn)
        if company is None:
            raise CompanyNotFound(inn)

        total = await self.repo.count_section(inn, section)
        items = await self.repo.list_section(inn, section, limit=limit, offset=offset)
        return total, items
