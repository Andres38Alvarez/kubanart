"""
Importa menciones de prensa desde el CSV semilla del "termómetro" de
circulación (press_mentions.csv).

Uso:
    python manage.py import_press
    python manage.py import_press --csv "otro_archivo.csv"
    python manage.py import_press --reset   # borra PressMention/Publication existentes antes de importar

El CSV se espera con estas columnas:
    publication_name, publication_country, publication_language,
    publication_origin (cuba_diaspora | international), publication_url,
    artist_name, article_title, article_url,
    published_year, published_date (YYYY-MM-DD o "none"), notes

artist_name admite varios artistas separados por ";" (ej. una nota que
cubre una exposición colectiva con obras de varios de los artistas ya
cargados en la base).

Nota editorial: publication_origin no se usa para excluir nada, sino para
poder comparar después la recepción dentro de Cuba/diáspora vs. la
recepción internacional (decisión tomada explícitamente con el usuario).
"""
import csv
import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from zettels.models import Artist, Artwork, Publication, PressMention

DEFAULT_CSV_NAME = "press_mentions.csv"


def normalize(value):
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


def to_date(value):
    value = normalize(value)
    if value is None:
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


class Command(BaseCommand):
    help = "Importa Publication/PressMention desde el CSV semilla de prensa."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            dest="csv_path",
            default=None,
            help="Ruta al CSV (por defecto, press_mentions.csv en la raíz del proyecto).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra todas las PressMention/Publication existentes antes de importar.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"] or (Path(settings.BASE_DIR) / DEFAULT_CSV_NAME)
        csv_path = Path(csv_path)

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"No existe el archivo: {csv_path}"))
            return

        if options["reset"]:
            self.stdout.write("Borrando PressMention y Publication existentes...")
            PressMention.objects.all().delete()
            Publication.objects.all().delete()

        n_publications = n_mentions = n_skipped = 0
        publication_cache = {}

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pub_name = normalize(row.get("publication_name"))
                article_title = normalize(row.get("article_title"))
                article_url = normalize(row.get("article_url"))
                if not (pub_name and article_title and article_url):
                    continue  # fila incompleta, se salta

                pub_country = normalize(row.get("publication_country"))
                cache_key = (pub_name.lower(), (pub_country or "").lower())
                if cache_key in publication_cache:
                    publication = publication_cache[cache_key]
                else:
                    publication, created = Publication.objects.get_or_create(
                        name=pub_name,
                        country=pub_country,
                        defaults={
                            "language": normalize(row.get("publication_language")),
                            "origin": normalize(row.get("publication_origin")) or Publication.Origin.INTERNATIONAL,
                            "homepage_url": normalize(row.get("publication_url")),
                        },
                    )
                    if created:
                        n_publications += 1
                    publication_cache[cache_key] = publication

                mention, created = PressMention.objects.get_or_create(
                    publication=publication,
                    url=article_url,
                    defaults={
                        "title": article_title,
                        "published_year": to_int(row.get("published_year")),
                        "published_date": to_date(row.get("published_date")),
                        "notes": normalize(row.get("notes")),
                    },
                )
                if not created:
                    n_skipped += 1
                    continue
                n_mentions += 1

                artist_field = normalize(row.get("artist_name"))
                if artist_field:
                    for artist_name in [n.strip() for n in artist_field.split(";") if n.strip()]:
                        artist = Artist.objects.filter(name=artist_name).first()
                        if artist:
                            mention.artists.add(artist)
                        else:
                            self.stdout.write(self.style.WARNING(
                                f"  Artista '{artist_name}' no encontrado en la base "
                                f"— la mención '{article_title}' quedó sin vincular a ese artista."
                            ))

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {n_publications} publicaciones nuevas, {n_mentions} menciones nuevas "
            f"({n_skipped} ya existían y se saltaron)."
        ))
