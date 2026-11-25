import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from .extensions import db
from .models import Zamowienie

def wczytaj_zamowienia(sciezka):
    with open(sciezka, encoding="utf-8", newline="") as plik:
        zamowienia = []
        for wiersz in csv.DictReader(plik):
            zamowienia.append({
                "data": wiersz["data"],
                "region": wiersz["region"],
                "przychod": float(wiersz["przychod"]),
                "koszt": float(wiersz["koszt"]),
            })
        return zamowienia


def dostepne_regiony(sciezka):
    regiony = {z["region"] for z in wczytaj_zamowienia(sciezka)}
    return sorted(regiony)


def policz_wskazniki(sciezka, region=None, rok=None):
    zamowienia = wczytaj_zamowienia(sciezka)
    if region is not None:
        zamowienia = [z for z in zamowienia if z["region"] == region]
    if rok is not None:
        zamowienia = [z for z in zamowienia if z["data"].startswith(str(rok))]

    przychod = round(sum(z["przychod"] for z in zamowienia), 2)
    koszt = round(sum(z["koszt"] for z in zamowienia), 2)
    if przychod == 0:
        marza = 0.0
    else:
        marza = round((przychod - koszt) / przychod, 4)

    return {
        "region": region or "wszystkie",
        "liczba_zamowien": len(zamowienia),
        "przychod": przychod,
        "koszt": koszt,
        "marza": marza,
    }


_RAPORTY = []


def zapisz_raport(rok, region, uwagi=""):
    _RAPORTY.append({"rok": rok, "region": region, "uwagi": uwagi})


def wykaz_raportow():
    return list(_RAPORTY)


def raporty_roku(rok):
    return [r for r in _RAPORTY if r["rok"] == rok]

def zestawienie_regionow(sciezka):
    wyniki = []
    for kod in dostepne_regiony(sciezka):
        wyniki.append(policz_wskazniki(sciezka, kod))
    return wyniki


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