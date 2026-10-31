# Práctica: monitor de sismos

## 1. Preparar el repositorio
1. Crea en GitHub un repositorio PUBLICO llamado monitor-sismos-actions, con README y rama main.
2. Clónalo con GitHub Desktop y abre su carpeta en VS Code.
3. Copia TODO el contenido de este proyecto dentro de la carpeta clonada, incluida .github y .gitignore. Los .py deben quedar en la raíz, sin otra carpeta intermedia.
4. Edita config.json: reemplaza ESCRIBE TU NOMBRE por tu nombre y TU_USUARIO por tu usuario de GitHub. Guarda. Conserva comillas y comas.

## 2. Verificar localmente
Abre Terminal > Nueva terminal en VS Code, dentro del repositorio:

```powershell
python -m unittest discover -v
python descargar.py
python analizar.py
```

Si python no funciona, usa py en los tres comandos. Se requiere Python 3.9 o superior. No hay bibliotecas adicionales que instalar y no necesitas requirements.txt.
Las siete pruebas deben terminar en OK. Abre public/index.html con tu navegador. Verifica cantidad, máxima y primeros eventos comparando con datos.csv (solo earthquake).
No uses una cifra fija de sismos: cambia con la fuente.
El CSV que descargaste manualmente sirve para inspeccionar columnas; el programa obtiene una copia nueva y registra su hora real. No inventa la hora usando la fecha del archivo.

## 3. Publicar
1. En GitHub: repositorio > Settings > Pages > Build and deployment > Source: GitHub Actions.
2. En GitHub Desktop revisa los archivos, escribe el resumen `Agregar monitor de sismos con CI y CD`, pulsa Commit to main y Push origin.
3. En GitHub abre Actions y entra en la ejecución. CI y CD deben terminar en verde.
4. En Settings > Pages abre Visit site. Normalmente: https://TU_USUARIO.github.io/monitor-sismos-actions/ . Copia el enlace real.
Si Actions no aparece, verifica que enviaste .github/workflows/sismos.yml a main. Si falla, abre el primer paso rojo.
datos.csv, descarga.json y public/ no se suben: están en .gitignore. Actions vuelve a descargarlos y generar el informe.

## 4. Demostraciones OBLIGATORIAS
Hazlas después de la primera publicación y conserva las ejecuciones reales.

### A. Actualizar sin cambiar código
Espera unos minutos y abre Actions > Sismos - CI y CD > Run workflow > main > Run workflow.
Espera a CI y CD en verde y recarga la página: debe cambiar la hora UTC de descarga aunque no cambie la cantidad.
También hay programación 00:17, 06:17, 12:17 y 18:17 UTC (20:17 del día anterior, 02:17, 08:17 y 14:17 en Bolivia). GitHub puede retrasarla.

### B. Cambiar código
En analizar.py cambia TITULO a `Monitor de sismos recientes - Informe actualizado`.
Guarda, ejecuta las pruebas y el análisis local, haz commit `Actualizar título del informe` y Push origin.
Espera a CI/CD verde y comprueba el título nuevo en el sitio.

### C. Fallo controlado y recuperación
En test_analizar.py cambia SOLO esta línea:
`self.assertEqual(resultado["cantidad"], 3)`
por:
`self.assertEqual(resultado["cantidad"], 999)`
Haz commit `Demostrar bloqueo por prueba fallida` y Push origin.
En Actions comprueba CI rojo, CD omitido y el sitio conservando el informe anterior. Esto es intencional para esta demostración.
Después RESTAURA 999 a 3, ejecuta las pruebas, haz commit `Restaurar prueba y recuperar publicación` y Push origin.
Comprueba CI y CD verdes. No termines con el error.

## 5. Entregar
- Enlace real de la página pública, que abra sin iniciar sesión.
- Enlace real del repositorio público.
- Comprueba en Actions: primera publicación, actualización manual, cambio de código, fallo controlado y recuperación.
No se requiere un PDF adicional. No presentes capturas o ejecuciones que no hayas realizado.

## Cómo explicar el proyecto
- descargar.py: urllib solicita el feed 2.5_week.csv; registra hora UTC real y una huella SHA-256 para comprobar que el CSV corresponde a esa descarga. Si falla, termina con error y bloquea la publicación.
- analizar.py: csv.DictReader lee por nombres; comprueba columnas, fechas con zona horaria, magnitudes finitas, ubicación e identificador. Filtra earthquake, ordena por fecha, cuenta por día UTC y genera HTML con barras CSS. No suma magnitudes ni convierte faltantes a cero. Un CSV válido sin eventos muestra cero y Sin datos.
- test_analizar.py: usa archivos temporales pequeños y no consulta internet. Comprueba cálculos, errores, columnas, fechas, agrupación UTC, ausencia de eventos y HTML.
- CI: máquina temporal de GitHub prepara Python, ejecuta pruebas, descarga y genera el informe.
- CD: needs: verificar exige que CI termine correctamente. Publica el artefacto public con permisos de Pages. Si CI falla, el sitio anterior permanece.
- Guardar modifica tu archivo; commit registra la versión local; push envía a GitHub.
- schedule actualiza datos sin commits. Push comprueba cambios de código. workflow_dispatch permite iniciar manualmente.
- El runner de Actions no es un clúster de Big Data; aquí se utiliza un CSV pequeño.

Fuentes: https://earthquake.usgs.gov/earthquakes/feed/v1.0/csv.php
https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
