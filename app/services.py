import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation
from sqlalchemy import func

from .extensions import db
from .models import Zamowienie

def dostepne_regiony():
    zapytanie = db.select(Zamowienie.region).distinct().order_by(Zamowienie.region)
    return list(db.session.scalars(zapytanie))


def _zawez(zapytanie, region, rok):
    if region:
        zapytanie = zapytanie.where(Zamowienie.region == region)
    if rok:
        zapytanie = zapytanie.where(
            Zamowienie.data >= date(rok, 1, 1),
            Zamowienie.data < date(rok + 1, 1, 1),
        )
    return zapytanie


def _marza(przychod, koszt):
    if przychod == 0:
        return Decimal("0")
    return ((przychod - koszt) / przychod).quantize(Decimal("0.0001"))


def policz_wskazniki(region=None, rok=None):
    zapytanie = _zawez(db.select(
        func.count().label("liczba_zamowien"),
        func.coalesce(func.sum(Zamowienie.przychod), 0).label("przychod"),
        func.coalesce(func.sum(Zamowienie.koszt), 0).label("koszt"),
    ), region, rok)
    wiersz = db.session.execute(zapytanie).one()
    przychod, koszt = Decimal(wiersz.przychod), Decimal(wiersz.koszt)
    return {
        "region": region or "wszystkie",
        "liczba_zamowien": wiersz.liczba_zamowien,
        "przychod": przychod,
        "koszt": koszt,
        "marza": _marza(przychod, koszt),
    }


def zestawienie_regionow():
    zapytanie = (
        db.select(
            Zamowienie.region,
            func.count().label("liczba_zamowien"),
            func.sum(Zamowienie.przychod).label("przychod"),
            func.sum(Zamowienie.koszt).label("koszt"),
        )
        .group_by(Zamowienie.region)
        .order_by(Zamowienie.region)
    )
    wyniki = []
    for w in db.session.execute(zapytanie):
        przychod, koszt = Decimal(w.przychod), Decimal(w.koszt)
        wyniki.append({
            "region": w.region,
            "liczba_zamowien": w.liczba_zamowien,
            "przychod": przychod,
            "koszt": koszt,
            "marza": _marza(przychod, koszt),
        })
    return wyniki


_RAPORTY = []


def zapisz_raport(rok, region, uwagi=""):
    _RAPORTY.append({"rok": rok, "region": region, "uwagi": uwagi})


def wykaz_raportow():
    return list(_RAPORTY)


def raporty_roku(rok):
    return [r for r in _RAPORTY if r["rok"] == rok]



WYMAGANE_KOLUMNY = {"data", "region", "przychod", "koszt"}


def wczytaj_zbior(strumien):
    tekst = strumien.read().decode("utf-8")      # zły plik -> UnicodeDecodeError (to też ValueError)
    odczyt = csv.DictReader(io.StringIO(tekst))
    brak = WYMAGANE_KOLUMNY - set(odczyt.fieldnames or [])
    if brak:
        raise ValueError("brak kolumn: " + ", ".join(sorted(brak)))
    numer = 1
    try:
        for numer, w in enumerate(odczyt, start=2):
            db.session.add(Zamowienie(
                data=date.fromisoformat(w["data"]),
                region=w["region"],
                przychod=Decimal(w["przychod"]),
                koszt=Decimal(w["koszt"]),
            ))
        db.session.commit()
    except (ValueError, InvalidOperation) as blad:
        db.session.rollback()
        raise ValueError(f"wiersz {numer}: niepoprawna data lub liczba") from blad
    return numer - 1