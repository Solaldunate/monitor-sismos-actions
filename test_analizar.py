import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from analizar import resumir, generar_informe

CABECERA = "time,mag,place,id,type\n"
EJEMPLO = CABECERA + (
    "2026-01-01T12:00:00Z,3.2,La Paz,a,earthquake\n"
    "2026-01-02T10:00:00Z,4.5,Cochabamba,b,earthquake\n"
    "2026-01-02T11:00:00Z,2.8,Santa Cruz,c,earthquake\n"
    "2026-01-02T12:00:00Z,5.0,Otro,d,quarry blast\n"
)

class TestSismos(unittest.TestCase):
    def procesar(self, contenido):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "datos.csv"
            ruta.write_text(contenido, encoding="utf-8")
            return resumir(ruta)

    def test_calculo_conocido(self):
        resultado = self.procesar(EJEMPLO)
        self.assertEqual(resultado["cantidad"],3)
        self.assertEqual(resultado["maxima"], 4.5)
        self.assertEqual(resultado["eventos"][0]["id"], "c")
        self.assertEqual(resultado["por_fecha"], {"2026-01-01": 1, "2026-01-02": 2})

    def test_rechaza_valor_invalido(self):
        for valor in ["hola", "", "NaN", "inf"]:
            with self.subTest(valor=valor), self.assertRaisesRegex(ValueError, "Fila 2"):
                self.procesar(CABECERA + f"2026-01-01T12:00:00Z,{valor},La Paz,a,earthquake\n")

    def test_columna_ausente(self):
        with self.assertRaisesRegex(ValueError, "columnas obligatorias"):
            self.procesar("time,place,id,type\n")

    def test_fecha_invalida(self):
        for fecha in ["ayer", "2026-01-01T12:00:00"]:
            with self.subTest(fecha=fecha), self.assertRaises(ValueError):
                self.procesar(CABECERA + f"{fecha},3,La Paz,a,earthquake\n")

    def test_agrupa_en_utc(self):
        resultado = self.procesar(CABECERA + "2026-01-01T23:30:00-04:00,3,La Paz,a,earthquake\n")
        self.assertEqual(resultado["por_fecha"], {"2026-01-02": 1})

    def test_sin_eventos(self):
        resultado = self.procesar(CABECERA)
        self.assertEqual(resultado["cantidad"], 0)
        self.assertIsNone(resultado["maxima"])

    def test_genera_informe(self):
        with tempfile.TemporaryDirectory() as carpeta:
            base = Path(carpeta)
            datos, meta, config, salida = [base / nombre for nombre in ["datos.csv", "descarga.json", "config.json", "public/index.html"]]
            datos.write_text(EJEMPLO.replace("La Paz", "<La Paz>"), encoding="utf-8")
            meta.write_text(json.dumps({"sha256": hashlib.sha256(datos.read_bytes()).hexdigest(), "descargado_utc": "2026-01-03T12:00:00Z", "fuente": "https://earthquake.usgs.gov/"}), encoding="utf-8")
            config.write_text(json.dumps({"estudiante": "Estudiante de prueba", "repositorio": "https://github.com/ejemplo/monitor-sismos-actions"}), encoding="utf-8")
            generar_informe(datos, salida, meta, config)
            pagina = salida.read_text(encoding="utf-8")
            for texto in ["Estudiante de prueba", "4.50", "&lt;La Paz&gt;", "2026-01-03 12:00:00 UTC", "Cantidad de sismos por fecha", "/actions"]:
                self.assertIn(texto, pagina)
            self.assertNotIn("<La Paz>", pagina)
            datos.write_text(CABECERA, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no coincide"):
                generar_informe(datos, salida, meta, config)

if __name__ == "__main__":
    unittest.main()
