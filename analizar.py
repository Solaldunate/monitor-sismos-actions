"""Valida sismos y genera HTML sin dependencias externas."""
import csv
import hashlib
import html
import json
import math
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

TITULO = "Monitor de sismos recientes"
OBLIGATORIAS = {"time", "mag", "place", "id", "type"}

def fecha_utc(texto):
    try:
        fecha = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if fecha.tzinfo is None:
            raise ValueError("falta zona horaria")
        return fecha.astimezone(timezone.utc)
    except (ValueError, AttributeError):
        raise ValueError(f"Fecha inválida o sin zona horaria: {texto!r}") from None

def resumir(ruta):
    eventos = []
    ids = set()
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        faltantes = OBLIGATORIAS - set(lector.fieldnames or [])
        if faltantes:
            raise ValueError("Faltan columnas obligatorias: " + ", ".join(sorted(faltantes)))
        for numero, fila in enumerate(lector, 2):
            try:
                if None in fila or any(fila[c] is None for c in OBLIGATORIAS):
                    raise ValueError("fila incompleta o con columnas adicionales")
                tipo = fila["type"].strip()
                if not tipo:
                    raise ValueError("falta el tipo de evento")
                if tipo != "earthquake":
                    continue
                identificador = fila["id"].strip()
                lugar = fila["place"].strip()
                if not identificador or not lugar:
                    raise ValueError("faltan identificador o ubicación")
                if identificador in ids:
                    raise ValueError("identificador duplicado")
                fecha = fecha_utc(fila["time"])
                try:
                    magnitud = float(fila["mag"])
                except ValueError:
                    raise ValueError("magnitud no numérica") from None
                if not math.isfinite(magnitud):
                    raise ValueError("magnitud no finita")
                ids.add(identificador)
                eventos.append({"id": identificador, "fecha": fecha,
                                "magnitud": magnitud, "lugar": lugar})
            except ValueError as error:
                raise ValueError(f"Fila {numero}: {error}") from None
    eventos.sort(key=lambda e: e["fecha"], reverse=True)
    return {"cantidad": len(eventos),
            "maxima": max((e["magnitud"] for e in eventos), default=None),
            "reciente": eventos[0]["fecha"] if eventos else None,
            "eventos": eventos,
            "por_fecha": dict(sorted(Counter(e["fecha"].date().isoformat() for e in eventos).items()))}

def mostrar_fecha(fecha):
    return fecha.strftime("%Y-%m-%d %H:%M:%S UTC")

def generar_informe(entrada="datos.csv", salida="public/index.html",
                    metadatos="descarga.json", configuracion="config.json"):
    resumen = resumir(entrada)
    meta = json.loads(Path(metadatos).read_text(encoding="utf-8"))
    if hashlib.sha256(Path(entrada).read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError("El CSV no coincide con la descarga registrada. Ejecuta descargar.py.")
    descarga = fecha_utc(meta["descargado_utc"])
    config = json.loads(Path(configuracion).read_text(encoding="utf-8"))
    estudiante = config["estudiante"].strip()
    repositorio = config["repositorio"].rstrip("/")
    if os.environ.get("GITHUB_REPOSITORY"):
        repositorio = "https://github.com/" + os.environ["GITHUB_REPOSITORY"]
    if not repositorio.startswith("https://github.com/"):
        raise ValueError("El repositorio debe comenzar con https://github.com/")
    if not estudiante or estudiante == "ESCRIBE TU NOMBRE":
        raise ValueError("Escribe tu nombre en config.json antes de generar el informe.")
    esc = lambda valor: html.escape(str(valor), quote=True)
    filas = "".join(f"<tr><td>{mostrar_fecha(e['fecha'])}</td><td>{esc(e['lugar'])}</td><td>{e['magnitud']:.2f}</td></tr>" for e in resumen["eventos"][:10])
    if not filas:
        filas = '<tr><td colspan="3">No hay sismos en esta consulta.</td></tr>'
    mayor = max(resumen["por_fecha"].values(), default=1)
    barras = "".join(f'<div class="dia"><span>{dia}</span><div class="pista"><div class="barra" style="width:{100*cantidad/mayor:.2f}%"></div></div><strong>{cantidad}</strong></div>' for dia, cantidad in resumen["por_fecha"].items())
    maxima = f"{resumen['maxima']:.2f}" if resumen["maxima"] is not None else "Sin datos"
    reciente = mostrar_fecha(resumen["reciente"]) if resumen["reciente"] else "Sin datos"
    pagina = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITULO)}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f0f5fa;color:#142d44;font:16px system-ui,sans-serif}}
main{{max-width:1100px;margin:40px auto;padding:0 22px}}header{{background:#142d44;color:white;padding:30px;border-radius:18px}}
h1{{margin:0 0 12px}}a{{color:#08669a}}header a{{color:#a6e4ff}}.indicadores{{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}}
.tarjeta,section{{background:white;border:1px solid #d5e1ed;border-radius:14px;padding:24px}}.tarjeta{{flex:1;min-width:220px}}
.valor{{display:block;font-size:26px;margin-top:10px}}section{{margin:20px 0}}.tabla{{overflow-x:auto}}table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;padding:12px;border-bottom:1px solid #dbe5ee}}th{{background:#edf4fa}}.dia{{display:flex;align-items:center;gap:12px;margin:14px 0}}
.dia span{{min-width:100px}}.pista{{flex:1;background:#edf4fa;border-radius:6px;overflow:hidden}}.barra{{height:24px;background:#0788a2}}
footer{{padding:15px 0 30px;line-height:1.8}}small{{line-height:1.6}}
</style></head><body><main>
<header><p>USGS / ÚLTIMOS SIETE DÍAS / CONSULTA M2.5+</p><h1>{esc(TITULO)}</h1>
<p>Estudiante: {esc(estudiante)}</p><a href="{esc(meta['fuente'])}">Fuente: CSV público del USGS</a></header>
<p><strong>Descarga realizada:</strong> {mostrar_fecha(descarga)}</p>
<p>Periodo consultado: últimos siete días; referencia aproximada {mostrar_fecha(descarga-timedelta(days=7))} a {mostrar_fecha(descarga)}.</p>
<small>Ventana móvil del proveedor. Se analizan los registros earthquake devueltos por el feed; las revisiones de magnitud pueden cambiar sus valores.</small>
<div class="indicadores"><div class="tarjeta">Cantidad de sismos<strong class="valor">{resumen['cantidad']}</strong></div>
<div class="tarjeta">Magnitud máxima<strong class="valor">{maxima}</strong></div>
<div class="tarjeta">Evento más reciente<strong class="valor">{reciente}</strong></div></div>
<section><h2>Cantidad de sismos por fecha (UTC)</h2>{barras or '<p>Sin eventos.</p>'}</section>
<section><h2>Los diez sismos más recientes</h2><div class="tabla"><table><thead><tr><th>Fecha (UTC)</th><th>Ubicación</th><th>Magnitud</th></tr></thead><tbody>{filas}</tbody></table></div></section>
<footer><a href="{esc(repositorio)}">Repositorio del proyecto</a> · <a href="{esc(repositorio)}/actions">Historial de Actions</a><br>
Las magnitudes no se suman. Cada ejecución descarga una copia nueva; la cantidad de eventos puede permanecer igual.</footer>
</main></body></html>"""
    destino = Path(salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    print(f"Informe generado: {destino}; sismos: {resumen['cantidad']}; máxima: {maxima}")
    return destino

if __name__ == "__main__":
    try:
        generar_informe()
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit(f"ANÁLISIS FALLIDO: {error}")
