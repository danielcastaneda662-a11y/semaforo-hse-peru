"""Comprueba disponibilidad de visores oficiales; NO infiere transitabilidad de HTML."""
import datetime,json,pathlib,requests
from zoneinfo import ZoneInfo
now=datetime.datetime.now(ZoneInfo("America/Lima")).isoformat()
sources={
 "sutran":"https://alertasviales.sutran.gob.pe/",
 "mtc":"https://saecoe.mtc.gob.pe/visor"
}
checks={}
for name,url in sources.items():
 try:
  r=requests.get(url,timeout=18,headers={"User-Agent":"SemaforoHSEPeru/1.0 (consulta de disponibilidad)"})
  checks[name]={"url":url,"reachable":r.ok,"http_status":r.status_code}
 except requests.RequestException as e:
  checks[name]={"url":url,"reachable":False,"error":type(e).__name__}
out={
 "checked_at":now,"data_status":"unverified",
 "explanation":"Se comprueba disponibilidad de visores, NO incidencias vigentes. No hay API oficial validada para alimentar el estado de vías.",
 "sources":checks,
 "reported_incidents":[
  {"zone":"Piura","location":"Sierra de Piura, cerca del límite con Cajamarca","road":"Longitudinal de la Sierra Norte, km 68","reported_status":"RESTRINGIDO","current_status":"POR CONFIRMAR","source_url":"https://andina.pe/agencia/noticia-fenomeno-nino-sutran-reporta-22-alertas-viales-eventos-naturales-1098401.aspx","note":"Reporte periodístico basado en declaraciones de SUTRAN. No demuestra que la restricción continúe activa."},
  {"zone":"Oriente","location":"Padre Abad, Ucayali","road":"Carretera Federico Basadre, km 441","reported_status":"INTERRUMPIDO","current_status":"POR CONFIRMAR","source_url":"https://andina.pe/agencia/noticia-fenomeno-nino-sutran-reporta-22-alertas-viales-eventos-naturales-1098401.aspx","note":"Reporte periodístico basado en declaraciones de SUTRAN. No demuestra que la interrupción continúe activa."}
 ]
}
pathlib.Path("vias.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Vías: fuentes consultadas; incidentes NO verificados en tiempo real")
