import json, re, datetime, pathlib, requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
URL="https://web2.senamhi.gob.pe/?p=avisos"
out=pathlib.Path("avisos.json")
now=datetime.datetime.now(ZoneInfo("America/Lima"))
payload={"checked_at":now.isoformat(),"source":URL,"source_status":"unavailable","advisories":[],"note":"No se ha validado cobertura municipal. Los niveles nacionales no se asignan a ciudades."}
try:
    r=requests.get(URL,timeout=35,headers={"User-Agent":"HSE-Meteorologia/1.0 (+GitHub Actions; public SENAMHI alerts)"})
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    for tr in soup.select("tr"):
        cells=[c.get_text(" ",strip=True) for c in tr.select("td")]
        if len(cells)<6: continue
        number=re.search(r"\b\d{1,4}\b",cells[1])
        if not number: continue
        level=next((x for x in ["ROJO","NARANJA","AMARILLO"] if x in " ".join(cells).upper()),None)
        if not level: continue
        dates=re.findall(r"20\d{2}-\d{2}-\d{2}"," ".join(cells))
        if len(dates)<3: continue
        try:
            start=datetime.date.fromisoformat(dates[1]);end=datetime.date.fromisoformat(dates[2])
        except ValueError: continue
        payload["advisories"].append({"number":number.group(),"title":cells[0],"issued":dates[0],"start":str(start),"end":str(end),"level":level,"current":start<=now.date()<=end})
    if payload["advisories"]:
        payload["source_status"]="parsed"
        payload["note"]="Avisos nacionales recuperados automáticamente. No implican afectación local sin verificar mapas oficiales."
    else:
        payload["note"]="No fue posible interpretar la tabla oficial; no se modifican niveles por ciudad."
except Exception as e:
    payload["note"]="Error consultando SENAMHI: "+str(e)[:140]
out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(payload["source_status"],len(payload["advisories"]))
