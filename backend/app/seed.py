"""Наполнение базы демо-данными.

20 вымышленных организаций с валидными по контрольной сумме ИНН/ОГРН.
Сид идемпотентный: если компании уже есть, ничего не делает.
Дочерние строки генерируются детерминированно от ИНН — данные не «плывут»
между пересборками контейнера.
"""

import logging
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
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

logger = logging.getLogger(__name__)

OKVED: dict[str, str] = {
    "62.01": "Разработка компьютерного программного обеспечения",
    "62.02": "Консультативная деятельность в области компьютерных технологий",
    "51.10": "Деятельность пассажирского воздушного транспорта",
    "25.11": "Производство строительных металлических конструкций",
    "01.13": "Выращивание овощей, бахчевых и корнеплодов",
    "46.72": "Торговля оптовая металлами и металлическими рудами",
    "49.41": "Деятельность автомобильного грузового транспорта",
    "01.11": "Выращивание зерновых и зернобобовых культур",
    "41.20": "Строительство жилых и нежилых зданий",
    "20.14": "Производство прочих основных органических химических веществ",
    "42.11": "Строительство автомобильных дорог и автомагистралей",
    "02.20": "Лесозаготовки",
    "24.20": "Производство стальных труб и профилей",
    "10.71": "Производство хлеба и мучных кондитерских изделий",
    "26.51": "Производство приборов для измерения и навигации",
    "09.10": "Услуги в области добычи нефти и природного газа",
    "43.99": "Работы строительные специализированные прочие",
    "10.20": "Переработка и консервирование рыбы и морепродуктов",
    "49.42": "Предоставление услуг по перевозкам",
    "46.77": "Торговля оптовая отходами и ломом",
}

ACTIVE = "Действующее"
LIQUIDATING = "В процессе ликвидации"
LIQUIDATED = "Ликвидировано"


@dataclass(frozen=True, slots=True)
class CompanySeed:
    inn: str
    ogrn: str
    name: str
    full_name: str
    status: str
    registration_date: date
    city: str
    region: str
    address: str
    okved: str
    capital: int
    ceo: str
    revenue: int
    profit: int
    headcount: int
    # court-cases, enforcement, contracts, licenses, inspections, relations, changes
    counts: tuple[int, int, int, int, int, int, int]


COMPANIES: tuple[CompanySeed, ...] = (
    CompanySeed(
        inn="7707410283",
        ogrn="1117737759457",
        name="ООО «Ромашка»",
        full_name="Общество с ограниченной ответственностью «Ромашка»",
        status=ACTIVE,
        registration_date=date(2011, 3, 14),
        city="Москва",
        region="Москва",
        address="127055, г. Москва, ул. Новослободская, д. 24, стр. 1, офис 402",
        okved="62.01",
        capital=1_500_000,
        ceo="Логинов Артём Сергеевич",
        revenue=128_500_000,
        profit=9_400_000,
        headcount=47,
        counts=(12, 3, 8, 1, 4, 6, 21),
    ),
    CompanySeed(
        inn="7701140520",
        ogrn="1097780798697",
        name="АО «Полярный вектор»",
        full_name="Акционерное общество «Полярный вектор»",
        status=ACTIVE,
        registration_date=date(2009, 11, 2),
        city="Москва",
        region="Москва",
        address="115184, г. Москва, ул. Большая Татарская, д. 9",
        okved="51.10",
        capital=90_000_000,
        ceo="Верещагина Ольга Петровна",
        revenue=4_120_000_000,
        profit=-85_000_000,
        headcount=612,
        counts=(23, 9, 14, 3, 7, 11, 25),
    ),
    CompanySeed(
        inn="7808910290",
        ogrn="1147841115102",
        name="ООО «Балтпром»",
        full_name="Общество с ограниченной ответственностью «Балтпром»",
        status=ACTIVE,
        registration_date=date(2014, 5, 21),
        city="Санкт-Петербург",
        region="Санкт-Петербург",
        address="196084, г. Санкт-Петербург, Московский пр-т, д. 107, лит. А",
        okved="25.11",
        capital=10_000_000,
        ceo="Крылов Денис Игоревич",
        revenue=743_000_000,
        profit=31_200_000,
        headcount=184,
        counts=(17, 5, 11, 2, 6, 8, 19),
    ),
    CompanySeed(
        inn="5007893962",
        ogrn="1165095494134",
        name="ООО «Подмосковные теплицы»",
        full_name="Общество с ограниченной ответственностью «Подмосковные теплицы»",
        status=ACTIVE,
        registration_date=date(2016, 2, 8),
        city="Мытищи",
        region="Московская область",
        address="141002, Московская обл., г. Мытищи, ул. Силикатная, д. 19",
        okved="01.13",
        capital=500_000,
        ceo="Наумова Ирина Владимировна",
        revenue=289_400_000,
        profit=17_800_000,
        headcount=96,
        counts=(6, 2, 5, 1, 9, 4, 14),
    ),
    CompanySeed(
        inn="6604417905",
        ogrn="1126648269054",
        name="АО «Уралмет-Сервис»",
        full_name="Акционерное общество «Уралмет-Сервис»",
        status=ACTIVE,
        registration_date=date(2012, 7, 30),
        city="Екатеринбург",
        region="Свердловская область",
        address="620144, г. Екатеринбург, ул. Фрунзе, д. 35а",
        okved="46.72",
        capital=25_000_000,
        ceo="Шаталов Пётр Николаевич",
        revenue=1_870_000_000,
        profit=64_500_000,
        headcount=241,
        counts=(25, 7, 13, 2, 5, 9, 23),
    ),
    CompanySeed(
        inn="5401028186",
        ogrn="1155492981885",
        name="ООО «Сибирь Логистик»",
        full_name="Общество с ограниченной ответственностью «Сибирь Логистик»",
        status=ACTIVE,
        registration_date=date(2015, 9, 17),
        city="Новосибирск",
        region="Новосибирская область",
        address="630001, г. Новосибирск, ул. Каменская, д. 56, офис 12",
        okved="49.41",
        capital=300_000,
        ceo="Ерофеев Максим Валерьевич",
        revenue=412_600_000,
        profit=8_900_000,
        headcount=133,
        counts=(19, 11, 7, 1, 4, 7, 18),
    ),
    CompanySeed(
        inn="2307194840",
        ogrn="1182347187208",
        name="ООО «Кубань-Агро»",
        full_name="Общество с ограниченной ответственностью «Кубань-Агро»",
        status=ACTIVE,
        registration_date=date(2018, 4, 3),
        city="Краснодар",
        region="Краснодарский край",
        address="350000, г. Краснодар, ул. Красная, д. 176, офис 21",
        okved="01.11",
        capital=1_200_000,
        ceo="Гончаренко Сергей Иванович",
        revenue=655_300_000,
        profit=42_100_000,
        headcount=207,
        counts=(8, 3, 9, 2, 6, 5, 12),
    ),
    CompanySeed(
        inn="1603270707",
        ogrn="1101674396163",
        name="ООО «Казань Девелопмент»",
        full_name="Общество с ограниченной ответственностью «Казань Девелопмент»",
        status=ACTIVE,
        registration_date=date(2010, 12, 9),
        city="Казань",
        region="Республика Татарстан",
        address="420015, г. Казань, ул. Большая Красная, д. 44",
        okved="41.20",
        capital=15_000_000,
        ceo="Валиев Рустам Ильдарович",
        revenue=1_240_000_000,
        profit=73_400_000,
        headcount=318,
        counts=(21, 6, 16, 3, 8, 12, 24),
    ),
    CompanySeed(
        inn="5207539670",
        ogrn="1135227186852",
        name="АО «Волга Химпром»",
        full_name="Акционерное общество «Волга Химпром»",
        status=ACTIVE,
        registration_date=date(2013, 6, 25),
        city="Нижний Новгород",
        region="Нижегородская область",
        address="603000, г. Нижний Новгород, ул. Ковалихинская, д. 8",
        okved="20.14",
        capital=48_000_000,
        ceo="Сафронов Кирилл Андреевич",
        revenue=2_310_000_000,
        profit=118_700_000,
        headcount=476,
        counts=(14, 4, 12, 3, 11, 8, 22),
    ),
    CompanySeed(
        inn="6100961337",
        ogrn="1176143121890",
        name="ООО «Донстройинвест»",
        full_name="Общество с ограниченной ответственностью «Донстройинвест»",
        status=LIQUIDATING,
        registration_date=date(2017, 8, 14),
        city="Ростов-на-Дону",
        region="Ростовская область",
        address="344002, г. Ростов-на-Дону, пр-т Ворошиловский, д. 62",
        okved="42.11",
        capital=100_000,
        ceo="Мельник Андрей Олегович",
        revenue=96_800_000,
        profit=-24_300_000,
        headcount=28,
        counts=(24, 14, 4, 0, 5, 9, 20),
    ),
    CompanySeed(
        inn="2403485489",
        ogrn="1082400794409",
        name="ООО «Енисей Лес»",
        full_name="Общество с ограниченной ответственностью «Енисей Лес»",
        status=ACTIVE,
        registration_date=date(2008, 10, 6),
        city="Красноярск",
        region="Красноярский край",
        address="660049, г. Красноярск, ул. Ленина, д. 113",
        okved="02.20",
        capital=800_000,
        ceo="Тарасов Виктор Леонидович",
        revenue=318_900_000,
        profit=12_600_000,
        headcount=142,
        counts=(11, 5, 6, 2, 7, 6, 16),
    ),
    CompanySeed(
        inn="7402085857",
        ogrn="1067421761769",
        name="ООО «Челябинский трубный двор»",
        full_name="Общество с ограниченной ответственностью «Челябинский трубный двор»",
        status=ACTIVE,
        registration_date=date(2006, 3, 28),
        city="Челябинск",
        region="Челябинская область",
        address="454091, г. Челябинск, ул. Труда, д. 156",
        okved="24.20",
        capital=32_000_000,
        ceo="Панкратов Илья Дмитриевич",
        revenue=1_560_000_000,
        profit=57_900_000,
        headcount=389,
        counts=(18, 8, 15, 2, 9, 10, 25),
    ),
    CompanySeed(
        inn="6304529291",
        ogrn="1196366759852",
        name="ООО «Самара Софт»",
        full_name="Общество с ограниченной ответственностью «Самара Софт»",
        status=ACTIVE,
        registration_date=date(2019, 1, 22),
        city="Самара",
        region="Самарская область",
        address="443001, г. Самара, ул. Молодогвардейская, д. 204, офис 7",
        okved="62.02",
        capital=200_000,
        ceo="Дубровина Екатерина Максимовна",
        revenue=54_700_000,
        profit=6_100_000,
        headcount=23,
        counts=(3, 1, 4, 0, 3, 3, 9),
    ),
    CompanySeed(
        inn="3602921445",
        ogrn="1203689809058",
        name="ООО «Черноземье Продукт»",
        full_name="Общество с ограниченной ответственностью «Черноземье Продукт»",
        status=ACTIVE,
        registration_date=date(2020, 5, 12),
        city="Воронеж",
        region="Воронежская область",
        address="394036, г. Воронеж, пр-т Революции, д. 33",
        okved="10.71",
        capital=600_000,
        ceo="Козырева Марина Анатольевна",
        revenue=187_200_000,
        profit=9_800_000,
        headcount=88,
        counts=(7, 2, 6, 1, 12, 4, 11),
    ),
    CompanySeed(
        inn="5905712116",
        ogrn="1075949862471",
        name="АО «Пермский приборостроительный альянс»",
        full_name="Акционерное общество «Пермский приборостроительный альянс»",
        status=ACTIVE,
        registration_date=date(2007, 2, 19),
        city="Пермь",
        region="Пермский край",
        address="614010, г. Пермь, ул. Куйбышева, д. 95б",
        okved="26.51",
        capital=64_000_000,
        ceo="Астафьев Николай Егорович",
        revenue=2_940_000_000,
        profit=203_500_000,
        headcount=734,
        counts=(16, 3, 22, 4, 10, 13, 25),
    ),
    CompanySeed(
        inn="7207017934",
        ogrn="1137260475879",
        name="ООО «Тюмень Нефтесервис»",
        full_name="Общество с ограниченной ответственностью «Тюмень Нефтесервис»",
        status=ACTIVE,
        registration_date=date(2013, 11, 5),
        city="Тюмень",
        region="Тюменская область",
        address="625000, г. Тюмень, ул. Республики, д. 142",
        okved="09.10",
        capital=8_000_000,
        ceo="Сидельников Роман Петрович",
        revenue=1_105_000_000,
        profit=38_400_000,
        headcount=265,
        counts=(13, 6, 18, 3, 6, 7, 17),
    ),
    CompanySeed(
        inn="4703635731",
        ogrn="1154722514440",
        name="ООО «Ленобласть Строй»",
        full_name="Общество с ограниченной ответственностью «Ленобласть Строй»",
        status=ACTIVE,
        registration_date=date(2015, 3, 30),
        city="Всеволожск",
        region="Ленинградская область",
        address="188640, Ленинградская обл., г. Всеволожск, Всеволожский пр-т, д. 72",
        okved="43.99",
        capital=1_000_000,
        ceo="Бурмистров Егор Васильевич",
        revenue=376_500_000,
        profit=4_200_000,
        headcount=119,
        counts=(20, 10, 9, 1, 5, 8, 19),
    ),
    CompanySeed(
        inn="3908711460",
        ogrn="1113962897927",
        name="ООО «Балтийская рыба»",
        full_name="Общество с ограниченной ответственностью «Балтийская рыба»",
        status=ACTIVE,
        registration_date=date(2011, 9, 8),
        city="Калининград",
        region="Калининградская область",
        address="236006, г. Калининград, Московский пр-т, д. 40",
        okved="10.20",
        capital=2_500_000,
        ceo="Житник Алексей Юрьевич",
        revenue=498_100_000,
        profit=26_700_000,
        headcount=157,
        counts=(9, 4, 7, 2, 14, 5, 15),
    ),
    CompanySeed(
        inn="5508588776",
        ogrn="1055517151690",
        name="ООО «Омск Транс»",
        full_name="Общество с ограниченной ответственностью «Омск Транс»",
        status=LIQUIDATED,
        registration_date=date(2005, 6, 15),
        city="Омск",
        region="Омская область",
        address="644024, г. Омск, ул. Маршала Жукова, д. 74/1",
        okved="49.42",
        capital=100_000,
        ceo="Черных Валерий Аркадьевич",
        revenue=31_200_000,
        profit=-11_500_000,
        headcount=12,
        counts=(15, 13, 3, 0, 4, 6, 25),
    ),
    CompanySeed(
        inn="3402445679",
        ogrn="1143439219472",
        name="ООО «Волгоград Металл Групп»",
        full_name="Общество с ограниченной ответственностью «Волгоград Металл Групп»",
        status=ACTIVE,
        registration_date=date(2014, 8, 26),
        city="Волгоград",
        region="Волгоградская область",
        address="400005, г. Волгоград, пр-т Ленина, д. 98",
        okved="46.77",
        capital=4_000_000,
        ceo="Игнатенко Дмитрий Русланович",
        revenue=822_400_000,
        profit=19_300_000,
        headcount=176,
        counts=(22, 12, 10, 1, 8, 11, 21),
    ),
)

COURTS: tuple[str, ...] = (
    "Арбитражный суд города Москвы",
    "Арбитражный суд Свердловской области",
    "Арбитражный суд Санкт-Петербурга и Ленинградской области",
    "Арбитражный суд Новосибирской области",
    "Арбитражный суд Краснодарского края",
)
COURT_CATEGORIES: tuple[str, ...] = (
    "Неисполнение обязательств по договору поставки",
    "Взыскание задолженности по договору подряда",
    "Споры о защите деловой репутации",
    "Налоговые споры",
    "Взыскание неустойки",
    "Споры по договору аренды",
)
COURT_ROLES: tuple[str, ...] = ("Истец", "Ответчик", "Третье лицо")
COURT_STATUSES: tuple[str, ...] = ("Рассмотрение", "Решение принято", "Прекращено", "Апелляция")

ENFORCEMENT_SUBJECTS: tuple[str, ...] = (
    "Взыскание налогов и сборов",
    "Задолженность по договору",
    "Исполнительский сбор",
    "Взыскание страховых взносов",
    "Иные взыскания имущественного характера",
)
ENFORCEMENT_STATUSES: tuple[str, ...] = ("Возбуждено", "Окончено", "Прекращено")

CUSTOMERS: tuple[str, ...] = (
    "ГБУЗ «Городская клиническая больница № 4»",
    "Департамент транспорта города Москвы",
    "ФГБОУ ВО «Политехнический университет»",
    "МУП «Водоканал»",
    "Администрация городского округа",
    "ГКУ «Центр организации дорожного движения»",
)
CONTRACT_SUBJECTS: tuple[str, ...] = (
    "Поставка расходных материалов",
    "Выполнение работ по текущему ремонту",
    "Оказание услуг технической поддержки",
    "Поставка оборудования",
    "Услуги по перевозке грузов",
)
CONTRACT_STATUSES: tuple[str, ...] = ("Исполнение", "Исполнен", "Расторгнут")

LICENSE_ACTIVITIES: tuple[str, ...] = (
    "Деятельность по монтажу средств обеспечения пожарной безопасности",
    "Эксплуатация взрывопожароопасных производственных объектов",
    "Заготовка, хранение и переработка лома чёрных металлов",
    "Медицинская деятельность",
    "Образовательная деятельность",
)
LICENSE_AUTHORITIES: tuple[str, ...] = ("МЧС России", "Ростехнадзор", "Росздравнадзор", "Рособрнадзор")

INSPECTION_AUTHORITIES: tuple[str, ...] = (
    "Роспотребнадзор",
    "ФНС России",
    "Государственная инспекция труда",
    "МЧС России",
    "Ростехнадзор",
)
INSPECTION_KINDS: tuple[str, ...] = (
    "Плановая выездная",
    "Внеплановая документарная",
    "Внеплановая выездная",
    "Профилактический визит",
)
INSPECTION_RESULTS: tuple[str, ...] = (
    "Нарушений не выявлено",
    "Выявлены нарушения, выдано предписание",
    "Составлен протокол об административном правонарушении",
)

RELATION_TYPES: tuple[str, ...] = ("Учредитель", "Руководитель", "Адрес регистрации")

FORMER_CEOS: tuple[str, ...] = (
    "Смирнов Игорь Валентинович",
    "Ковалёва Наталья Борисовна",
    "Терентьев Павел Михайлович",
    "Аксёнова Светлана Юрьевна",
)
FORMER_ADDRESSES: tuple[str, ...] = (
    "офис в прежнем бизнес-центре, помещение 3",
    "адрес до смены юридического лица",
    "адрес массовой регистрации, исключён из ЕГРЮЛ",
)
CHANGE_SOURCES: tuple[str, ...] = ("ЕГРЮЛ", "ФНС", "Росстат")

TODAY = date(2026, 7, 1)


def _random_date(rnd: random.Random, days_back: int) -> date:
    return TODAY - timedelta(days=rnd.randint(30, days_back))


def _money(rnd: random.Random, low: int, high: int) -> Decimal:
    return Decimal(rnd.randint(low, high)) / Decimal(100)


def _build_court_cases(company: CompanySeed, rnd: random.Random) -> list[CourtCase]:
    return [
        CourtCase(
            inn=company.inn,
            case_number=f"А{company.inn[:2]}-{rnd.randint(1000, 99999)}/{rnd.randint(2019, 2026)}",
            court=rnd.choice(COURTS),
            role=rnd.choice(COURT_ROLES),
            category=rnd.choice(COURT_CATEGORIES),
            amount=_money(rnd, 50_000_00, 40_000_000_00),
            started_at=_random_date(rnd, 2200),
            status=rnd.choice(COURT_STATUSES),
        )
        for _ in range(company.counts[0])
    ]


def _build_enforcement(company: CompanySeed, rnd: random.Random) -> list[EnforcementCase]:
    return [
        EnforcementCase(
            inn=company.inn,
            number=f"{rnd.randint(10000, 99999)}/{rnd.randint(19, 26)}/{company.inn[:2]}-ИП",
            subject=rnd.choice(ENFORCEMENT_SUBJECTS),
            amount=_money(rnd, 10_000_00, 8_000_000_00),
            department=f"ОСП по г. {company.city} УФССП России",
            opened_at=_random_date(rnd, 1500),
            status=rnd.choice(ENFORCEMENT_STATUSES),
        )
        for _ in range(company.counts[1])
    ]


def _build_contracts(company: CompanySeed, rnd: random.Random) -> list[Contract]:
    return [
        Contract(
            inn=company.inn,
            number=f"{rnd.randint(10**11, 10**12 - 1)}",
            customer_name=rnd.choice(CUSTOMERS),
            subject=rnd.choice(CONTRACT_SUBJECTS),
            amount=_money(rnd, 300_000_00, 120_000_000_00),
            signed_at=_random_date(rnd, 1800),
            status=rnd.choice(CONTRACT_STATUSES),
        )
        for _ in range(company.counts[2])
    ]


def _build_licenses(company: CompanySeed, rnd: random.Random) -> list[License]:
    licenses: list[License] = []
    for index in range(company.counts[3]):
        issued_at = _random_date(rnd, 2500)
        expired = rnd.random() < 0.25
        licenses.append(
            License(
                inn=company.inn,
                number=f"ЛО-{company.inn[:2]}-01-{rnd.randint(100000, 999999)}",
                activity=LICENSE_ACTIVITIES[index % len(LICENSE_ACTIVITIES)],
                authority=rnd.choice(LICENSE_AUTHORITIES),
                issued_at=issued_at,
                valid_until=issued_at + timedelta(days=rnd.randint(365, 2000)),
                status="Прекращена" if expired else "Действует",
            )
        )
    return licenses


def _build_inspections(company: CompanySeed, rnd: random.Random) -> list[Inspection]:
    inspections: list[Inspection] = []
    for _ in range(company.counts[4]):
        violations = rnd.choice([0, 0, 0, 1, 2, 3])
        result = INSPECTION_RESULTS[0] if violations == 0 else rnd.choice(INSPECTION_RESULTS[1:])
        inspections.append(
            Inspection(
                inn=company.inn,
                authority=rnd.choice(INSPECTION_AUTHORITIES),
                kind=rnd.choice(INSPECTION_KINDS),
                started_at=_random_date(rnd, 1600),
                result=result,
                violations_found=violations,
            )
        )
    return inspections


def _build_relations(company: CompanySeed, rnd: random.Random) -> list[CompanyRelation]:
    others = [other for other in COMPANIES if other.inn != company.inn]
    partners = rnd.sample(others, k=min(company.counts[5], len(others)))
    relations: list[CompanyRelation] = []
    for partner in partners:
        relation_type = rnd.choice(RELATION_TYPES)
        share = _money(rnd, 100, 100_00) if relation_type == "Учредитель" else None
        relations.append(
            CompanyRelation(
                inn=company.inn,
                related_inn=partner.inn,
                related_name=partner.name,
                relation_type=relation_type,
                share_percent=share,
                status=partner.status,
            )
        )
    return relations


def _build_changes(company: CompanySeed, rnd: random.Random) -> list[CompanyChange]:
    capital = f"{company.capital:,} ₽".replace(",", " ")
    variants: tuple[tuple[str, str, str], ...] = (
        ("Руководитель", rnd.choice(FORMER_CEOS), company.ceo),
        ("Юридический адрес", rnd.choice(FORMER_ADDRESSES), company.address),
        ("Уставный капитал", "10 000 ₽", capital),
        ("Основной ОКВЭД", "70.22", company.okved),
        ("Наименование", f"{company.name[:-1]}-Плюс»", company.name),
        ("Состав учредителей", "2 участника", "3 участника"),
        ("Дополнительный ОКВЭД", "—", rnd.choice(tuple(OKVED))),
    )
    changes: list[CompanyChange] = []
    for index in range(company.counts[6]):
        field, previous_value, new_value = variants[index % len(variants)]
        changes.append(
            CompanyChange(
                inn=company.inn,
                changed_at=_random_date(rnd, 2600),
                field=field,
                previous_value=previous_value,
                new_value=new_value,
                source=rnd.choice(CHANGE_SOURCES),
            )
        )
    return changes


def _build_financials(company: CompanySeed, rnd: random.Random) -> list[CompanyFinancials]:
    rows: list[CompanyFinancials] = []
    revenue = company.revenue
    profit = company.profit
    for offset, year in enumerate((2025, 2024, 2023)):
        decay = 1 - offset * rnd.uniform(0.08, 0.22)
        rows.append(
            CompanyFinancials(
                inn=company.inn,
                year=year,
                revenue=int(revenue * decay),
                profit=int(profit * decay),
                assets=int(revenue * decay * rnd.uniform(0.4, 0.9)),
            )
        )
    return rows


def _build_headcount(company: CompanySeed, rnd: random.Random) -> list[CompanyHeadcount]:
    return [
        CompanyHeadcount(
            inn=company.inn,
            year=year,
            headcount=max(1, int(company.headcount * (1 - offset * rnd.uniform(0.05, 0.2)))),
        )
        for offset, year in enumerate((2025, 2024, 2023))
    ]


async def seed_if_empty(session: AsyncSession) -> None:
    existing = await session.scalar(select(func.count()).select_from(MasterCompany))
    if existing:
        logger.info("сид пропущен: в базе уже %s компаний", existing)
        return

    session.add_all([OkvedDict(code=code, name=name) for code, name in OKVED.items()])
    await session.flush()

    for company in COMPANIES:
        session.add(
            MasterCompany(
                inn=company.inn,
                ogrn=company.ogrn,
                name=company.name,
                full_name=company.full_name,
                status=company.status,
                registration_date=company.registration_date,
                city=company.city,
                region=company.region,
                address=company.address,
                main_okved_code=company.okved,
                charter_capital=company.capital,
                ceo_name=company.ceo,
            )
        )
    await session.flush()

    for company in COMPANIES:
        rnd = random.Random(int(company.inn))
        session.add_all(_build_financials(company, rnd))
        session.add_all(_build_headcount(company, rnd))
        session.add_all(_build_court_cases(company, rnd))
        session.add_all(_build_enforcement(company, rnd))
        session.add_all(_build_contracts(company, rnd))
        session.add_all(_build_licenses(company, rnd))
        session.add_all(_build_inspections(company, rnd))
        session.add_all(_build_relations(company, rnd))
        session.add_all(_build_changes(company, rnd))

    await session.commit()
    logger.info("сид выполнен: %s компаний", len(COMPANIES))
