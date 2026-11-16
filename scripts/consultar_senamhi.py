import json,datetime,pathlib,requests
from zoneinfo import ZoneInfo
NOW=datetime.datetime.now(ZoneInfo("America/Lima"))
BASE="https://geosinpad.indeci.gob.pe/indeci/rest/services/Ent_Tecnico_Cientificas/SENAMHI/MapServer"
# Coordenadas aproximadas de centros urbanos; se comprueba únicamente el punto indicado, no toda la ruta.
CITIES={
"Piura":[(-80.6328,-5.1945)],"Chiclayo":[(-79.8409,-6.7714)],"Trujillo":[(-79.0288,-8.1116)],
"Norte Chico":[(-77.6050,-11.1067),(-77.7676,-10.7523)],"Sur Chico":[(-76.3833,-13.0751),(-74.9380,-14.8280)],
"Lima Norte y Sur":[(-77.0650,-11.9580),(-76.9760,-12.1660)],"Cusco":[(-71.9675,-13.5319)],
"Arequipa":[(-71.5375,-16.4090)],"Huancayo":[(-75.2049,-12.0651)],
"Oriente":[(-74.5539,-8.3791),(-73.2516,-3.7437),(-76.3650,-6.4882)]}
out={"checked_at":NOW.isoformat(),"source":BASE+"/5","source_status":"unavailable","advisories":[],"zones":{},"note":"Avisos de precipitación de las próximas 24 h, consultados por coordenadas; otros fenómenos no cubiertos."}
session=requests.Session()
successful=0
for city,pts in CITIES.items():
    results=[]
    for lon,lat in pts:
        try:
            params={"f":"json","geometry":f"{lon},{lat}","geometryType":"esriGeometryPoint","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":"NIVEL,FECHA,DESCRIPCIO,RECOMENDAC","returnGeometry":"false"}
            r=session.get(BASE+"/5/query",params=params,timeout=16)
            r.raise_for_status()
            j=r.json()
            if "error" in j or "features" not in j:raise ValueError(str(j.get("error","sin features"))[:90])
            successful+=1
            for feature in j["features"]:
                a=feature.get("attributes",{})
                ts=a.get("FECHA")
                if ts:
                    date=datetime.datetime.fromtimestamp(ts/1000,datetime.timezone.utc).astimezone(ZoneInfo("America/Lima"))
                    if abs((NOW-date).total_seconds())>60*60*48:continue
                else:continue
                level=str(a.get("NIVEL",""))
                if level not in ("Nivel 2","Nivel 3"):continue
                results.append({"level":"AMARILLO" if level=="Nivel 2" else "NARANJA","date":date.isoformat(),"description":a.get("DESCRIPCIO") or "Aviso de precipitaciones 24 horas","recommendation":a.get("RECOMENDAC") or "Evaluar condiciones de lluvia"})
        except Exception as e:
            out.setdefault("errors",[]).append(f"{city}: {type(e).__name__}: {str(e)[:70]}")
    out["zones"][city]={"rain24h":results,"checked_points":len(pts),"verified_points":successful}
out["source_status"]="parsed" if successful==sum(map(len,CITIES.values())) else ("partial" if successful else "unavailable")
out["note"]=f"Consulta de capa SENAMHI/INDECI de precipitaciones 24h: {successful} de {sum(map(len,CITIES.values()))} puntos respondieron. No certifica ausencia de otros avisos."
pathlib.Path("avisos.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(out["source_status"],out["note"])
