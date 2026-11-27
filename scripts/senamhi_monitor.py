"""Consulta automática de capas SENAMHI publicadas por INDECI.
Las capas de 24h no equivalen al inventario nacional de avisos meteorológicos.
"""
import datetime
import json
import pathlib
import time
import urllib.parse
import urllib.request

BASE = "https://geosinpad.indeci.gob.pe/indeci/rest/services/Ent_Tecnico_Cientificas/SENAMHI/MapServer"
OUT = pathlib.Path("data/senamhi-status.json")
POINTS = {
    "Piura": [(-80.63, -5.19)],
    "Chiclayo": [(-79.84, -6.77)],
    "Trujillo": [(-79.03, -8.11)],
    "Norte Chico": [(-77.61, -11.11), (-77.76, -10.75)],
    "Sur Chico": [(-76.38, -13.08), (-74.94, -14.83)],
    "Lima Norte y Sur": [(-77.06, -11.92), (-76.93, -12.18)],
    "Cusco": [(-71.97, -13.53)],
    "Arequipa": [(-71.54, -16.40)],
    "Huancayo": [(-75.21, -12.07)],
    "Oriente": [(-74.55, -8.38), (-73.25, -3.75), (-76.37, -6.49)]
}
LAYERS = {2: "quebradas_24h", 5: "precipitacion_24h"}

def query(layer, lon, lat):
    params = urllib.parse.urlencode({
        "f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
        "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*", "returnGeometry": "false"
    })
    req = urllib.request.Request(f"{BASE}/{layer}/query?{params}",
        headers={"User-Agent": "Mozilla/5.0 (compatible; HSE-Semaforo/1.0)"})
    with urllib.request.urlopen(req, timeout=18) as response:
        payload = json.load(response)
    if "error" in payload or "features" not in payload:
        raise ValueError("Respuesta ArcGIS inválida")
    return [f.get("attributes", {}) for f in payload["features"]]

def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {"source": BASE, "checked_at_utc": stamp, "status": "unverified",
              "message": "Capas SENAMHI/INDECI sin verificar.",
              "scope": "Capas geográficas 24h; NO inventario nacional de avisos.",
              "zones": {}, "layers": {}, "national_advisories_verified": False}
    ok = 0
    for layer, name in LAYERS.items():
        successful, failures = 0, 0
        for zone, coords in POINTS.items():
            result["zones"].setdefault(zone, {})
            hits = []
            zone_success = 0
            zone_failures = 0
            for lon, lat in coords:
                try:
                    hits.extend(query(layer, lon, lat))
                    successful += 1
                    zone_success += 1
                except Exception:
                    failures += 1
                    zone_failures += 1
            # No interpretar vacío como ausencia de peligro si hubo errores.
            result["zones"][zone][name] = {
                "features": hits[:15], "points_ok": zone_success,
                "coverage": "partial" if zone_failures else "queried"
            } if zone_success else {"features": [], "coverage": "unavailable"}
        result["layers"][name] = {"successful_queries": successful, "failed_queries": failures}
        ok += successful
    result["status"] = "source_reachable" if ok else "unverified"
    result["message"] = ("Capas oficiales consultadas; avisos nacionales todavía no verificados."
                         if ok else "No fue posible consultar las capas oficiales.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["status"], result["layers"])


def weather_snapshot():
    from concurrent.futures import ThreadPoolExecutor
    def fetch_zone(item):
        name, coords = item
        lon, lat = coords[0]
        params = urllib.parse.urlencode({"latitude":lat,"longitude":lon,"current":"temperature_2m,precipitation,wind_gusts_10m,weather_code","timezone":"America/Lima"})
        try:
            with urllib.request.urlopen("https://api.open-meteo.com/v1/forecast?"+params, timeout=15) as response:
                x = json.load(response)["current"]
            if not all(isinstance(x.get(k),(int,float)) for k in ("temperature_2m","precipitation","wind_gusts_10m","weather_code")):
                raise ValueError("Incomplete weather")
            return name, x
        except Exception:
            return name, None
    with ThreadPoolExecutor(max_workers=4) as pool:
        zones = dict(pool.map(fetch_zone, POINTS.items()))
    path = pathlib.Path("data/weather.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"zones":zones},ensure_ascii=False),encoding="utf-8")

if __name__ == "__main__":
    weather_snapshot()
    main()
