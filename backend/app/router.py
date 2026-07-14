"""HTTP-эндпоинты карточки компании."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import SECTION_MODELS
from app.schemas import (
    AiDescriptionResponse,
    AiFeedbackRequest,
    AiFeedbackResponse,
    ChangeItem,
    CompanySummary,
    ContractItem,
    CourtCaseItem,
    EnforcementItem,
    InspectionItem,
    LicenseItem,
    RelationItem,
    SectionResponse,
)
from app.service import CompanyNotFound, CompanyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["company"])

Inn = Annotated[str, Path(pattern=r"^\d{10}(\d{2})?$", description="ИНН, 10 или 12 цифр")]

SECTION_ITEM_MODELS: dict[str, type[BaseModel]] = {
    "court-cases": CourtCaseItem,
    "enforcement": EnforcementItem,
    "contracts": ContractItem,
    "licenses": LicenseItem,
    "inspections": InspectionItem,
    "relations": RelationItem,
    "changes": ChangeItem,
}


def get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> CompanyService:
    return CompanyService(session)


ServiceDep = Annotated[CompanyService, Depends(get_service)]


@router.get("/company/{inn}/summary", response_model=CompanySummary)
async def get_company_summary(inn: Inn, service: ServiceDep) -> CompanySummary:
    summary = await service.get_company_summary(inn)
    if summary is None:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return summary


@router.get("/company/{inn}/ai-description", response_model=AiDescriptionResponse)
async def get_ai_description(
    inn: Inn, service: ServiceDep, response: Response
) -> AiDescriptionResponse:
    try:
        description = await service.get_ai_description(inn)
    except CompanyNotFound:
        raise HTTPException(status_code=404, detail="Компания не найдена")

    # Описание меняется редко, а генерация дорогая — пусть его отдаёт CDN,
    # не доходя до приложения.
    response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=3600"
    return description


@router.post("/company/{inn}/ai-feedback", response_model=AiFeedbackResponse)
async def submit_ai_feedback(
    inn: Inn, payload: AiFeedbackRequest, service: ServiceDep
) -> AiFeedbackResponse:
    try:
        return await service.register_ai_feedback(inn, payload.vote)
    except CompanyNotFound:
        raise HTTPException(status_code=404, detail="Компания не найдена")


@router.get("/company/{inn}/section/{section}", response_model=SectionResponse)
async def get_company_section(
    inn: Inn,
    section: Annotated[str, Path(description="Раздел карточки")],
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SectionResponse:
    if section not in SECTION_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестный раздел: {section}. Доступны: {', '.join(SECTION_MODELS)}",
        )

    try:
        total, rows = await service.get_section(inn, section, limit=limit, offset=offset)
    except CompanyNotFound:
        raise HTTPException(status_code=404, detail="Компания не найдена")

    item_model = SECTION_ITEM_MODELS[section]
    items = [item_model.model_validate(row) for row in rows]
    return SectionResponse(section=section, total=total, items=items)
