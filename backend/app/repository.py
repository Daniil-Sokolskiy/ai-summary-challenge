"""Доступ к данным. Никакой бизнес-логики — только SQL."""

from collections.abc import Sequence
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base
from app.models import (
    SECTION_MODELS,
    SECTION_ORDER_COLUMNS,
    CompanyAiDescription,
    CompanyChange,
    CompanyFinancials,
    CompanyHeadcount,
    CompanyRelation,
    Contract,
    CourtCase,
    EnforcementCase,
    Inspection,
    License,
    MasterCompany,
    OkvedDict,
)


class UnknownSection(ValueError):
    """Запрошен раздел, которого нет в карточке."""


def section_model(section: str) -> type[Base]:
    model = SECTION_MODELS.get(section)
    if model is None:
        raise UnknownSection(section)
    return model


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_company(self, inn: str) -> MasterCompany | None:
        return await self.session.get(MasterCompany, inn)

    async def get_okved(self, code: str) -> OkvedDict | None:
        return await self.session.get(OkvedDict, code)

    async def get_latest_financials(self, inn: str) -> CompanyFinancials | None:
        query = (
            select(CompanyFinancials)
            .where(CompanyFinancials.inn == inn)
            .order_by(CompanyFinancials.year.desc())
            .limit(1)
        )
        return await self.session.scalar(query)

    async def get_latest_headcount(self, inn: str) -> CompanyHeadcount | None:
        query = (
            select(CompanyHeadcount)
            .where(CompanyHeadcount.inn == inn)
            .order_by(CompanyHeadcount.year.desc())
            .limit(1)
        )
        return await self.session.scalar(query)

    async def count_section(self, inn: str, section: str) -> int:
        model = section_model(section)
        query = select(func.count()).select_from(model).where(model.inn == inn)
        return await self.session.scalar(query) or 0

    async def list_section(
        self, inn: str, section: str, limit: int, offset: int
    ) -> Sequence[Base]:
        model = section_model(section)
        column_name, descending = SECTION_ORDER_COLUMNS[section]
        order_column = getattr(model, column_name)
        query = (
            select(model)
            .where(model.inn == inn)
            .order_by(order_column.desc() if descending else order_column.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(query)
        return result.all()

    async def sum_court_amount(self, inn: str) -> float:
        query = select(func.coalesce(func.sum(CourtCase.amount), 0)).where(CourtCase.inn == inn)
        return float(await self.session.scalar(query) or 0)

    async def top_court_categories(self, inn: str, limit: int = 3) -> list[str]:
        query = (
            select(CourtCase.category, func.count().label("cases"))
            .where(CourtCase.inn == inn)
            .group_by(CourtCase.category)
            .order_by(func.count().desc(), CourtCase.category)
            .limit(limit)
        )
        rows = await self.session.execute(query)
        return [category for category, _ in rows.all()]

    async def sum_enforcement_amount(self, inn: str) -> float:
        query = select(func.coalesce(func.sum(EnforcementCase.amount), 0)).where(
            EnforcementCase.inn == inn
        )
        return float(await self.session.scalar(query) or 0)

    async def sum_contract_amount(self, inn: str) -> float:
        query = select(func.coalesce(func.sum(Contract.amount), 0)).where(Contract.inn == inn)
        return float(await self.session.scalar(query) or 0)

    async def count_active_licenses(self, inn: str) -> int:
        query = (
            select(func.count())
            .select_from(License)
            .where(License.inn == inn, License.status == "Действует")
        )
        return await self.session.scalar(query) or 0

    async def sum_inspection_violations(self, inn: str) -> int:
        query = select(func.coalesce(func.sum(Inspection.violations_found), 0)).where(
            Inspection.inn == inn
        )
        return int(await self.session.scalar(query) or 0)

    async def list_key_relations(self, inn: str, limit: int = 5) -> list[str]:
        query = (
            select(CompanyRelation.related_name)
            .where(CompanyRelation.inn == inn)
            .order_by(CompanyRelation.share_percent.desc().nulls_last(), CompanyRelation.id)
            .limit(limit)
        )
        result = await self.session.scalars(query)
        return list(result.all())

    async def last_change_date(self, inn: str) -> date | None:
        query = select(func.max(CompanyChange.changed_at)).where(CompanyChange.inn == inn)
        return await self.session.scalar(query)

    async def get_ai_description(self, inn: str) -> CompanyAiDescription | None:
        return await self.session.get(CompanyAiDescription, inn)

    async def upsert_ai_description(
        self,
        *,
        inn: str,
        description: str,
        facts_hash: str,
        score: int,
        is_llm: bool,
        model: str | None,
        history: list[str],
        generated_at: datetime,
    ) -> None:
        values = {
            "inn": inn,
            "description": description,
            "facts_hash": facts_hash,
            "score": score,
            "is_llm": is_llm,
            "model": model,
            "history": history,
            "generated_at": generated_at.astimezone(timezone.utc),
        }
        statement = pg_insert(CompanyAiDescription).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[CompanyAiDescription.inn],
            set_={key: statement.excluded[key] for key in values if key != "inn"},
        )
        await self.session.execute(statement)
