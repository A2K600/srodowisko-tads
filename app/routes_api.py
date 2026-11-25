from decimal import Decimal

from flask import Blueprint, abort, jsonify, request

from .decorators import wymagany_parametr
from .services import dostepne_regiony, policz_wskazniki, raporty_roku
from .validators import parametr_int

api_bp = Blueprint("api", __name__)


def _jako_liczby(slownik):
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in slownik.items()}


@api_bp.get("/kpi")
def kpi():
    region = request.args.get("region")
    if region is not None and region not in dostepne_regiony():
        abort(404, description=f"Nieznany region: {region}")
    return jsonify(_jako_liczby(policz_wskazniki(region)))


@api_bp.get("/raporty")
@wymagany_parametr("rok")
def raporty():
    rok = parametr_int("rok", 2020, 2030)
    return jsonify(rok=rok, raporty=raporty_roku(rok))