# Mapa de obras cubanas en colecciones europeas

Sitio estático (sin build): `index.html` + Leaflet + `data/artworks.geojson`.

## Estructura

```
cuban-art-europe-map/
  index.html
  data/
    artworks.geojson
```

## Cómo actualizar los datos

Edita `data/artworks.geojson`. Cada obra es un `Feature` con este esquema:

```json
{
  "type": "Feature",
  "geometry": { "type": "Point", "coordinates": [longitud, latitud] },
  "properties": {
    "artist": "Nombre del artista",
    "title": "Título de la obra",
    "year": "Año",
    "medium": "Técnica/medio",
    "institution": "Museo o colección",
    "city": "Ciudad",
    "country": "País",
    "source": "URL de la ficha o cita (opcional)"
  }
}
```

Los 5 registros actuales son de ejemplo (marcados `"placeholder": true`) — reemplázalos por tus datos reales cuando tengas tu base de datos lista. Puedes generar este archivo directamente desde una hoja de cálculo (Google Sheets/Airtable) exportando a JSON o pidiéndome que lo convierta cuando me pases el archivo.

## Desplegar en Vercel (temporalmente)

No hay conector de Vercel que permita publicar directamente desde aquí (el que existe solo sirve para consultar despliegues ya hechos), así que el paso de publicar lo haces tú, en 2 minutos:

**Opción A — CLI (más rápida):**
1. Instala la CLI: `npm i -g vercel`
2. Desde la carpeta `cuban-art-europe-map`, ejecuta: `vercel`
3. Sigue el enlace para loguearte con tu cuenta (GitHub/email) la primera vez.
4. Confirma los defaults (proyecto estático, sin build command) y listo — te da una URL tipo `https://cuban-art-europe-map-xxxx.vercel.app`.
5. Para producción: `vercel --prod`.

**Opción B — sin CLI:**
1. Ve a vercel.com/new.
2. Arrastra la carpeta `cuban-art-europe-map` (o conecta un repo de GitHub con estos archivos).
3. Vercel detecta que es un sitio estático y lo publica sin configuración adicional.

Artista nacido en Cuba o que desarrolló su práctica artística principal en Cuba, independientemente de su residencia actual o nacionalidad. Incluye a artistas de la diáspora como Félix González-Torres o Carmen Herrera."



Fuentes válidas:
Solo catálogos online públicos y verificables de museos con acceso abierto.
Ejemplos:

Tate
Centre Pompidou
Museo Reina Sofía
MoMA (para referencia, aunque es EE.UU.).


¿Qué NO incluye la Fase 1?

Colecciones privadas (sin acceso público verificable).
Obras sin ficha oficial en los catálogos.
Artistas con mención marginal en exposiciones (sin obra registrada).

h