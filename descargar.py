"""Descarga una copia nueva; nunca continúa con datos anteriores si falla."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.csv"

def descargar():
    try:
        peticion = Request(URL, headers={"User-Agent": "MonitorSismosPractica/1.0"})
        with urlopen(peticion, timeout=60) as respuesta:
            datos = respuesta.read()
        if not datos.strip():
            raise ValueError("La respuesta del USGS está vacía.")
        datos.decode("utf-8-sig")
        instante = datetime.now(timezone.utc).isoformat()
        temporal = Path("datos.csv.tmp")
        temporal.write_bytes(datos)
        temporal.replace("datos.csv")
        metadatos = {"descargado_utc": instante, "fuente": URL,
                     "sha256": hashlib.sha256(datos).hexdigest()}
        Path("descarga.json").write_text(json.dumps(metadatos), encoding="utf-8")
        print(f"Descarga correcta: {len(datos)} bytes; UTC: {instante}")
    except Exception as error:
        raise SystemExit(f"DESCARGA FALLIDA: {error}. No se genera ni publica el informe.")

if __name__ == "__main__":
    descargar()
