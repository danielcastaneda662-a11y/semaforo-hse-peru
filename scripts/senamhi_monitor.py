"""Monitor de disponibilidad SENAMHI. No infiere niveles ni localidades."""
import datetime
import json
import pathlib
import re
import urllib.request
import time

URL = "https://www.senamhi.gob.pe/?p=avisos-meteorologicos"
OUT = pathlib.Path("data/senamhi-status.json")
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
record = {"source": URL, "checked_at_utc": now, "status": "unverified",
          "message": "Avisos no verificados: no asignar colores oficiales."}
errors = []
for attempt in range(3):
    try:
        request = urllib.request.Request(URL, headers={
            "User-Agent": "Mozilla/5.0 (compatible; HSE-Semaforo/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "es-PE,es;q=0.9"
        })
        with urllib.request.urlopen(request, timeout=25) as response:
            html = response.read(3_000_000).decode("utf-8", errors="replace")
        if re.search(r"avisos meteorol[oó]gicos", html, re.IGNORECASE):
            record["status"] = "source_reachable"
            record["message"] = "Portal accesible. Extracción y cobertura geográfica de avisos pendientes de validar."
        else:
            record["message"] = "Respuesta inesperada del portal SENAMHI; avisos no verificados."
        break
    except Exception as exc:
        errors.append(type(exc).__name__)
        if attempt < 2:
            time.sleep(2 * (attempt + 1))
else:
    record["message"] = "SENAMHI no respondió después de tres intentos. No implica ausencia de avisos."
    record["error_type"] = ", ".join(errors)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(record["status"], record["message"])
