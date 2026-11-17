"""Monitor de disponibilidad SENAMHI. No infiere niveles ni localidades."""
import datetime
import json
import pathlib
import re
import urllib.request

URL = "https://www.senamhi.gob.pe/?p=avisos-meteorologicos"
OUT = pathlib.Path("data/senamhi-status.json")
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
record = {"source": URL, "checked_at_utc": now, "status": "unverified",
          "message": "Avisos no verificados: no asignar colores oficiales."}
try:
    request = urllib.request.Request(URL, headers={"User-Agent": "HSE-Semaforo/1.0 (public weather safety monitor)", "Accept": "text/html"})
    with urllib.request.urlopen(request, timeout=20) as response:
        html = response.read(3_000_000).decode("utf-8", errors="replace")
    if re.search(r"avisos meteorol[oó]gicos", html, re.IGNORECASE):
        record["status"] = "source_reachable"
        record["message"] = "Portal accesible. Extracción y cobertura geográfica de avisos pendientes de validar."
    else:
        record["message"] = "Respuesta inesperada del portal SENAMHI."
except Exception as exc:
    record["message"] = "No se pudo consultar el portal SENAMHI."
    record["error_type"] = type(exc).__name__
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(record["status"], record["message"])
