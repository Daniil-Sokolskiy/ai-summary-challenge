"""Pydantic-схемы: контракт API и внутренние структуры фактов."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SectionCounts(BaseModel):
    court_cases: int = 0
    enforcement: int = 0
    contracts: int = 0
    licenses: int = 0
    inspections: int = 0
    relations: int = 0
    changes: int = 0


class CompanySummary(BaseModel):
    inn: str
    name: str
    status: str
    registration_date: date | None
    city: str
    main_okved_code: str
    main_okved_name: str
    revenue: int | None
    profit: int | None
    headcount: int | None
    section_counts: SectionCounts


class AiDescriptionResponse(BaseModel):
    inn: str
    description: str
    generated_at: datetime
    cached: bool
    score: int
    is_llm: bool
    history: list[str] = Field(default_factory=list)


AiVote = Literal["up", "down"]


class AiFeedbackRequest(BaseModel):
    vote: AiVote


class AiFeedbackResponse(BaseModel):
    inn: str
    vote: AiVote
    votes: int
    triggered_regeneration: bool


class CourtCaseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    court: str
    role: str
    category: str
    amount: float | None
    started_at: date
    status: str


class EnforcementItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    subject: str
    amount: float | None
    department: str
    opened_at: date
    status: str


class ContractItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    customer_name: str
    subject: str
    amount: float | None
    signed_at: date
    status: str


class LicenseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    activity: str
    authority: str
    issued_at: date
    valid_until: date | None
    status: str


class InspectionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    authority: str
    kind: str
    started_at: date
    result: str
    violations_found: int


class RelationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    related_inn: str
    related_name: str
    relation_type: str
    share_percent: float | None
    status: str


class ChangeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    changed_at: date
    field: str
    previous_value: str | None
    new_value: str | None
    source: str


SectionItem = (
    CourtCaseItem
    | EnforcementItem
    | ContractItem
    | LicenseItem
    | InspectionItem
    | RelationItem
    | ChangeItem
)


class SectionResponse(BaseModel):
    section: str
    total: int
    items: list[SectionItem]


class CompanyFacts(BaseModel):
    """Всё, на чём основано ИИ-описание.

    Модель сериализуется в JSON и хэшируется — отпечаток фактов входит
    в ключ кэша, поэтому порядок и состав полей менять осознанно.
    """

    inn: str
    name: str
    full_name: str
    status: str
    registration_date: date | None
    city: str
    region: str
    ceo_name: str | None
    charter_capital: int | None
    main_okved_code: str
    main_okved_name: str
    revenue: int | None
    profit: int | None
    revenue_year: int | None
    headcount: int | None
    section_counts: SectionCounts
    court_amount_total: float
    court_top_categories: list[str]
    enforcement_amount_total: float
    contracts_amount_total: float
    active_licenses: int
    inspection_violations: int
    key_relations: list[str]
    last_change_at: date | None


class DebugStats(BaseModel):
    sql_queries_total: int
    sql_queries_by_endpoint: dict[str, int]
