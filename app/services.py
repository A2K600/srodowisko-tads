import csv


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


def policz_wskazniki(sciezka, region=None):
    zamowienia = wczytaj_zamowienia(sciezka)
    if region is not None:
        zamowienia = [z for z in zamowienia if z["region"] == region]

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


def zapisz_raport(rok, region):
    _RAPORTY.append({"rok": rok, "region": region})


def raporty_roku(rok):
    return [r for r in _RAPORTY if r["rok"] == rok]