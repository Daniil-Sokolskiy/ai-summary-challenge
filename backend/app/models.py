"""Модели БД: карточка компании, дочерние разделы и кэш ИИ-описания."""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OkvedDict(Base):
    """Справочник ОКВЭД. Заполняется сидом, руками не правится."""

    __tablename__ = "okved_dict"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)


class MasterCompany(Base):
    __tablename__ = "master_company"

    inn: Mapped[str] = mapped_column(String(12), primary_key=True)
    ogrn: Mapped[str] = mapped_column(String(15), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False)
    registration_date: Mapped[date | None] = mapped_column(Date)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(400), nullable=False)
    main_okved_code: Mapped[str] = mapped_column(String(8), ForeignKey("okved_dict.code"))
    charter_capital: Mapped[int | None] = mapped_column(BigInteger)
    ceo_name: Mapped[str | None] = mapped_column(String(200))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CompanyFinancials(Base):
    """Годовая отчётность. На карточке показываем последний доступный год."""

    __tablename__ = "company_financials"
    __table_args__ = (UniqueConstraint("inn", "year", name="uq_financials_inn_year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    revenue: Mapped[int | None] = mapped_column(BigInteger)
    profit: Mapped[int | None] = mapped_column(BigInteger)
    assets: Mapped[int | None] = mapped_column(BigInteger)


class CompanyHeadcount(Base):
    __tablename__ = "company_headcount"
    __table_args__ = (UniqueConstraint("inn", "year", name="uq_headcount_inn_year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    headcount: Mapped[int] = mapped_column(Integer, nullable=False)


class CourtCase(Base):
    __tablename__ = "court_case"
    __table_args__ = (Index("ix_court_case_inn_started", "inn", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    case_number: Mapped[str] = mapped_column(String(60), nullable=False)
    court: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # Истец / Ответчик / Третье лицо
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False)


class EnforcementCase(Base):
    """Исполнительное производство ФССП."""

    __tablename__ = "enforcement_case"
    __table_args__ = (Index("ix_enforcement_inn_opened", "inn", "opened_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    number: Mapped[str] = mapped_column(String(60), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    department: Mapped[str] = mapped_column(String(200), nullable=False)
    opened_at: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False)


class Contract(Base):
    """Госконтракты по 44-ФЗ/223-ФЗ."""

    __tablename__ = "contract"
    __table_args__ = (Index("ix_contract_inn_signed", "inn", "signed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    number: Mapped[str] = mapped_column(String(60), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(300), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    signed_at: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False)


class License(Base):
    __tablename__ = "license"
    __table_args__ = (Index("ix_license_inn_issued", "inn", "issued_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    number: Mapped[str] = mapped_column(String(60), nullable=False)
    activity: Mapped[str] = mapped_column(String(300), nullable=False)
    authority: Mapped[str] = mapped_column(String(200), nullable=False)
    issued_at: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(60), nullable=False)


class Inspection(Base):
    """Проверки надзорных органов."""

    __tablename__ = "inspection"
    __table_args__ = (Index("ix_inspection_inn_started", "inn", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    authority: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(120), nullable=False)
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    result: Mapped[str] = mapped_column(String(200), nullable=False)
    violations_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CompanyRelation(Base):
    """Связи по учредителям, руководителям и адресу."""

    __tablename__ = "company_relation"
    __table_args__ = (Index("ix_relation_inn_type", "inn", "relation_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    related_inn: Mapped[str] = mapped_column(String(12), nullable=False)
    related_name: Mapped[str] = mapped_column(String(300), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(60), nullable=False)
    share_percent: Mapped[float | None] = mapped_column(Numeric(6, 2))
    status: Mapped[str] = mapped_column(String(60), nullable=False)


class CompanyChange(Base):
    """История изменений в реестре."""

    __tablename__ = "company_change"
    __table_args__ = (Index("ix_change_inn_changed", "inn", "changed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), index=True)
    changed_at: Mapped[date] = mapped_column(Date, nullable=False)
    field: Mapped[str] = mapped_column(String(120), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(String(300))
    new_value: Mapped[str | None] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(60), nullable=False)


class CompanyAiDescription(Base):
    """Долговременный кэш ИИ-описания.

    Redis может быть холодным (рестарт, вытеснение), поэтому результат
    генерации дублируется в базу. `facts_hash` — отпечаток фактов, по которым
    текст был написан: если факты изменились, строка считается неактуальной.
    """

    __tablename__ = "company_ai_description"

    inn: Mapped[str] = mapped_column(String(12), ForeignKey("master_company.inn"), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    facts_hash: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_llm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    model: Mapped[str | None] = mapped_column(String(80))
    history: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# Разделы карточки: URL-сегмент -> модель и колонка сортировки.
# Порядок важен: в этом же порядке считаются section_counts.
SECTION_MODELS: dict[str, type[Base]] = {
    "court-cases": CourtCase,
    "enforcement": EnforcementCase,
    "contracts": Contract,
    "licenses": License,
    "inspections": Inspection,
    "relations": CompanyRelation,
    "changes": CompanyChange,
}

# Колонка сортировки раздела и признак «по убыванию».
SECTION_ORDER_COLUMNS: dict[str, tuple[str, bool]] = {
    "court-cases": ("started_at", True),
    "enforcement": ("opened_at", True),
    "contracts": ("signed_at", True),
    "licenses": ("issued_at", True),
    "inspections": ("started_at", True),
    "relations": ("related_name", False),
    "changes": ("changed_at", True),
}

SECTIONS: tuple[str, ...] = tuple(SECTION_MODELS)


def section_counts_key(section: str) -> str:
    """URL-сегмент -> ключ в section_counts: court-cases -> court_cases."""
    return section.replace("-", "_")
