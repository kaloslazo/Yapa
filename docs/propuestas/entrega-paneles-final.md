# Entrega final de paneles y Explorar — 11/11/2026

Base: ZIP Yapa-publicacion recibido; main guardado 826af51ec6a54455883e9aaef3cb9bbd3e709fe6. No se consultó el main remoto actual.

## Incluido
- Armado: fechas completas y filtro de zona para bolsas y entregas.
- Atención: Completados con contador, resultados y mensaje cuando no hay registros.
- Portería: zona asignada, filtro por estado, seguimiento e historial. Avisos mientras la página está abierta, con consulta cada 15 segundos. No permite ver otras zonas ni incorpora un estado manual En pausa.
- Proveedor: edición por producto, unidad, disponibilidad y precios por volumen; envía propuestas para aprobación.
- Explorar: guías plegadas al inicio y cinco preguntas visibles, con opción de ver las diez.
- Compras y Reparto: funcionamiento conservado.

La implementación principal ya estaba guardada en el ZIP. Se revisó y conservó. En esta revisión se añadió la fecha completa al historial de Portería y mensajes específicos para preparación y ausencia de pedidos.

## Verificación
TypeScript, 170 pruebas frontend, 718 pruebas backend y build aprobados en Linux con Node 24.22.1 y Python 3.12.14. CI usa Node 22. Sigue el aviso de un archivo JS mayor de 500 kB. La revisión visual registrada en la iteración 63 pertenece al Codex anterior; no se repitió aquí. No se publicó en GitHub ni AWS.

## Ejecutar en Windows
Requisitos: Node 22 y Python 3.11 o superior. Abre dos terminales PowerShell dentro de la carpeta app extraída.

Terminal 1:
```powershell
python api/tools/servir_demo.py --puerto 8010
```
Si usas el lanzador de Python, sustituye python por py -3. La demo se guarda en memoria y se reinicia al detenerla.

Terminal 2:
```powershell
npm.cmd ci
$env:YAPA_API="http://127.0.0.1:8010"
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```
Abre http://127.0.0.1:5173/. Ctrl+C detiene cada servidor. No se usa 8000 ni se modifica PostgreSQL.

## Publicar en una rama nueva
La carpeta app contiene el proyecto completo. cambios.patch contiene las diferencias respecto al main guardado en el ZIP, incluyendo esta guía. No copies todo app encima del repositorio actualizado.

1. Extrae el ZIP en C:\Users\aaroo\Documents\DesignSoftware-projectU. Debe quedar la carpeta entrega-yapa con app, cambios.patch y LEEME-PRIMERO.md.
2. Abre PowerShell. Yapa-entrega-paneles debe ser una carpeta nueva; si existe, usa otro nombre, sin borrar tu trabajo anterior.
```powershell
cd "C:\Users\aaroo\Documents\DesignSoftware-projectU"
git clone https://github.com/kaloslazo/Yapa.git Yapa-entrega-paneles
cd Yapa-entrega-paneles
git switch -c aaron/paneles-explorar-final origin/main
git apply --3way --index "..\entrega-yapa\cambios.patch"
```
Si aparecen conflictos o errores, detente y conserva la salida para resolverlos. No sigas con commit ni push y no reemplaces main con app. Si ya incorporaron estos cambios, el parche también puede indicar que no aplica.

3. Si se aplicó correctamente:
```powershell
git status --short
git --no-pager diff --cached --stat
npm.cmd ci
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
```
Revisa archivos-cambiados.txt para comparar la lista. Si una comprobación falla, corrígela antes de subir.

4. Con las comprobaciones correctas:
```powershell
git commit -m "Mejorar paneles de operacion y secciones de Explorar"
git push -u origin aaron/paneles-explorar-final
```
5. En GitHub abre Compare & pull request. Base main; compare aaron/paneles-explorar-final. Describe el contenido con el resumen de esta guía. Pide revisión al equipo antes de fusionar.

Si GitHub indica Repository not found, verifica tu invitación y la cuenta autorizada. No crees otro repositorio.

## Subir desde la página de GitHub
Sí se puede: selecciona una rama nueva y conserva las rutas de los archivos. Es normal que tenga también todos los archivos de main. Pero subir una copia completa antigua puede reemplazar avances nuevos; por eso aquí se recomienda el parche con Git.

Git pull descarga e integra cambios; git push sube tus commits. Git reconoce las diferencias aunque los archivos convivan con el resto del proyecto. Subir el ZIP a GitHub no lo extrae ni instala. No subas .git, node_modules, .env ni dist.

El flujo incluido despliega únicamente cambios en main, si están configurados los secretos. Esta rama por sí sola no actualiza holayapa.app.

## Reparto: sugerencias, sin implementar
- Ordenar las paradas según la ruta del día.
- Mostrar contacto y observaciones de acceso al edificio.
- Aclarar el motivo y siguiente paso cuando una entrega no se logra.
