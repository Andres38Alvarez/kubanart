"""
Importa artistas, museos y obras desde el CSV semilla del proyecto.

Uso:
    python manage.py import_artist
    python manage.py import_artist --csv "otro_archivo.csv"
    python manage.py import_artist --reset   # borra Artist/Museum/Artwork antes de importar

El CSV se espera con estas columnas (algunas vienen con typos del original,
por eso el mapeo explícito abajo):
    artist_name, birth_year, death_year, birthplace,
    artwork_title, year, medium, dimesions,
    museum_name, city, country, museum_catalogue_url,
    image_righnts, notes, description
"""
import csv
import time
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from zettels.models import Artist, Artwork, Museum

DEFAULT_CSV_NAME = "Artis_Cuban Art Acroos  - Tabellenblatt1.csv"

# Coordenadas conocidas de antemano para museos frecuentes, para no depender
# de una llamada de red exitosa en cada importación. Si el museo no está
# aquí, se intenta geocodificar con Nominatim (OpenStreetMap) y si eso
# también falla, se importa igual mostrando el aviso.
KNOWN_MUSEUMS = {
    ("reina sofia", "madrid", "spain"): (40.4085, -3.6944),
    ("museo reina sofia", "madrid", "spain"): (40.4085, -3.6944),
    ("centre pompidou", "paris", "france"): (48.8606, 2.3522),
    ("tate modern", "london", "united kingdom"): (51.5076, -0.0994),
    ("tate", "london", "united kingdom"): (51.5076, -0.0994),
    ("stedelijk museum", "amsterdam", "netherlands"): (52.3579, 4.8790),
    ("museum ludwig", "cologne", "germany"): (50.9413, 6.9603),
    ("moma", "new york", "united states"): (40.7614, -73.9776),
    ("museum of modern art", "new york", "united states"): (40.7614, -73.9776),
    ("metropolitan museum of art", "new york", "united states"): (40.7794, -73.9632),
    ("whitney museum of american art", "new york", "united states"): (40.7396, -74.0089),
    ("perez art museum miami", "miami", "united states"): (25.7862, -80.1868),
    ("pamm", "miami", "united states"): (25.7862, -80.1868),
}

# País (normalizado con fold()) -> región del proyecto. Se usa para llenar
# Museum.region automáticamente al importar. Países que no aparezcan aquí
# quedan con region=None y se pueden ajustar a mano en el admin.
COUNTRY_TO_REGION = {
    # Fase 1: Europa
    "spain": "europe", "france": "europe", "united kingdom": "europe",
    "netherlands": "europe", "germany": "europe", "italy": "europe",
    "portugal": "europe", "belgium": "europe", "austria": "europe",
    "switzerland": "europe", "sweden": "europe", "denmark": "europe",
    "norway": "europe", "finland": "europe", "poland": "europe",
    "ireland": "europe", "greece": "europe",
    # Fase 2: Norteamérica
    "united states": "north_america", "usa": "north_america",
    "canada": "north_america", "mexico": "north_america",
    # Fase 3: Latinoamérica
    "cuba": "latin_america", "argentina": "latin_america",
    "brazil": "latin_america", "colombia": "latin_america",
    "chile": "latin_america", "peru": "latin_america",
    "venezuela": "latin_america", "puerto rico": "latin_america",
    "dominican republic": "latin_america",
    # Fase 4: Asia y África (a completar cuando toque)
    "japan": "asia", "china": "asia", "south korea": "asia", "india": "asia",
    "south africa": "africa", "egypt": "africa", "nigeria": "africa",
}


def region_for_country(country):
    if not country:
        return None
    return COUNTRY_TO_REGION.get(fold(country))


def fold(text):
    """Minúsculas y sin acentos, para que 'Reina Sofía' == 'reina sofia'."""
    text = unicodedata.normalize('NFKD', text.strip().lower())
    return ''.join(c for c in text if not unicodedata.combining(c))


def normalize(value):
    """Convierte strings vacíos o "none" (tal cual vienen en el CSV) a None."""
    if value is None:
        return None
    value = value.strip()
    if value == "" or value.lower() == "none":
        return None
    return value


def to_int(value):
    value = normalize(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


class Command(BaseCommand):
    help = "Importa Artist/Museum/Artwork desde el CSV semilla del proyecto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            dest="csv_path",
            default=None,
            help="Ruta al CSV (por defecto, el CSV semilla en la raíz del proyecto).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra todas las Artwork/Museum/Artist existentes antes de importar.",
        )
        parser.add_argument(
            "--no-geocode",
            action="store_true",
            help="No intentar geocodificar por red; solo usa KNOWN_MUSEUMS.",
        )

    def geocode(self, name, city, country, use_network=True):
        key = (fold(name), fold(city), fold(country))
        if key in KNOWN_MUSEUMS:
            return KNOWN_MUSEUMS[key]

        if not use_network:
            return (None, None)

        try:
            from geopy.geocoders import Nominatim

            geolocator = Nominatim(user_agent="cuban_art_across_kubanart")
            query = f"{name}, {city}, {country}"
            location = geolocator.geocode(query, timeout=10)
            # Nominatim pide no golpear su servidor más de ~1 req/seg.
            time.sleep(1)
            if location:
                return (location.latitude, location.longitude)
        except Exception as exc:  # sin geopy, sin red, timeout, lo que sea
            self.stdout.write(self.style.WARNING(
                f"  No se pudo geocodificar '{name}, {city}, {country}': {exc}"
            ))
        return (None, None)

    def handle(self, *args, **options):
        csv_path = options["csv_path"] or (Path(settings.BASE_DIR) / DEFAULT_CSV_NAME)
        csv_path = Path(csv_path)

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"No existe el archivo: {csv_path}"))
            return

        if options["reset"]:
            self.stdout.write("Borrando Artwork, Museum y Artist existentes...")
            Artwork.objects.all().delete()
            Museum.objects.all().delete()
            Artist.objects.all().delete()

        use_network = not options["no_geocode"]

        museum_cache = {}
        n_artists = n_museums = n_artworks = 0

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                artist_name = normalize(row.get("artist_name"))
                if not artist_name:
                    continue  # fila vacía o corrupta, se salta

                artist, created = Artist.objects.get_or_create(
                    name=artist_name,
                    defaults={
                        "birth_year": to_int(row.get("birth_year")),
                        "death_year": to_int(row.get("death_year")),
                        "birthplace": normalize(row.get("birthplace")),
                    },
                )
                if created:
                    n_artists += 1

                museum_name = normalize(row.get("museum_name"))
                city = normalize(row.get("city"))
                country = normalize(row.get("country"))
                museum = None
                if museum_name and city and country:
                    cache_key = (museum_name.lower(), city.lower(), country.lower())
                    if cache_key in museum_cache:
                        museum = museum_cache[cache_key]
                    else:
                        museum, created = Museum.objects.get_or_create(
                            name=museum_name, city=city, country=country,
                            defaults={"region": region_for_country(country)},
                        )
                        if created:
                            n_museums += 1
                        elif museum.region is None:
                            # Museo ya existía de antes de que existiera el campo region.
                            inferred = region_for_country(country)
                            if inferred:
                                museum.region = inferred
                                museum.save(update_fields=["region"])
                        if museum.latitude is None or museum.longitude is None:
                            lat, lon = self.geocode(museum_name, city, country, use_network)
                            if lat is not None:
                                museum.latitude = lat
                                museum.longitude = lon
                                museum.save(update_fields=["latitude", "longitude"])
                            else:
                                self.stdout.write(self.style.WARNING(
                                    f"  Sin coordenadas para {museum_name} ({city}, {country}) "
                                    "— no aparecerá en el mapa hasta que se completen a mano."
                                ))
                        museum_cache[cache_key] = museum

                Artwork.objects.create(
                    artist=artist,
                    museum=museum,
                    title=normalize(row.get("artwork_title")),
                    year=to_int(row.get("year")),
                    medium=normalize(row.get("medium")),
                    dimensions=normalize(row.get("dimesions")),  # typo real del CSV
                    museum_catalogue_url=normalize(row.get("museum_catalogue_url")),
                    image_rights=normalize(row.get("image_righnts")),  # typo real del CSV
                    notes=normalize(row.get("notes")),
                    description=normalize(row.get("description")),
                )
                n_artworks += 1

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {n_artists} artistas nuevos, {n_museums} museos nuevos, "
            f"{n_artworks} obras importadas."
        ))
