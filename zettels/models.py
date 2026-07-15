from django.db import models

class Artist(models.Model):
    name = models.CharField(max_length=100)
    birth_year = models.IntegerField(null=True,blank=True)
    death_year = models.IntegerField(null=True,blank=True)
    birthplace = models.CharField(max_length=100, null=True,blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Museum(models.Model):
    # Un registro por institución física. Las coordenadas se geocodifican
    # una sola vez aquí, en vez de repetirse en cada Artwork.

    class Region(models.TextChoices):
        EUROPE = 'europe', 'Europe'
        NORTH_AMERICA = 'north_america', 'North America'
        LATIN_AMERICA = 'latin_america', 'Latin America'
        ASIA = 'asia', 'Asia'
        AFRICA = 'africa', 'Africa'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    # Se infiere automáticamente del país al importar (ver import_artist.py),
    # pero queda editable a mano para casos ambiguos o países nuevos.
    region = models.CharField(
        max_length=20, choices=Region.choices, null=True, blank=True,
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['country', 'city', 'name']
        unique_together = ('name', 'city', 'country')

    def __str__(self):
        return f"{self.name} ({self.city}, {self.country})"


class Publication(models.Model):
    # Una fila por medio/publicación (no por artículo): esto evita repetir
    # país/idioma/origen en cada mención y permite ver de un vistazo cuántas
    # veces aparece un medio en el "termómetro" de prensa.

    class Origin(models.TextChoices):
        CUBA_DIASPORA = 'cuba_diaspora', 'Cuba / Diaspora'
        INTERNATIONAL = 'international', 'International'

    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(max_length=100, null=True, blank=True)
    # Ver nota de la pregunta al usuario: se guardan ambos orígenes para
    # poder comparar recepción dentro y fuera de Cuba, no para excluir uno.
    origin = models.CharField(max_length=20, choices=Origin.choices)
    homepage_url = models.URLField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'country')

    def __str__(self):
        return self.name


class PressMention(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='mentions')
    artists = models.ManyToManyField(Artist, related_name='press_mentions', blank=True)
    artwork = models.ForeignKey(
        'Artwork', on_delete=models.SET_NULL, null=True, blank=True, related_name='press_mentions',
    )
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=500)
    # Fecha parcial a propósito: para menciones antiguas a veces solo se
    # puede confirmar el año (o ni eso), y no queremos bloquear la carga
    # de datos por no tener el día exacto.
    published_year = models.IntegerField(null=True, blank=True)
    published_date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-published_year', '-published_date']

    def __str__(self):
        return f"{self.title} ({self.publication.name})"


class Artwork(models.Model):
    # Delete the artist . on_delete=models.CASCADE deletes the pieces if the artist is deleted.
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='artworks')
    # PROTECT: no se puede borrar un museo si todavía tiene obras registradas
    # (evita perder obras por accidente al limpiar la tabla de museos).
    museum = models.ForeignKey(Museum, on_delete=models.PROTECT, related_name='artworks', null=True, blank=True)

    #fields of csv
    title = models.CharField(max_length=255)
    year = models.IntegerField(null=True, blank=True)
    medium = models.CharField(max_length=255, null=True, blank=True)
    dimensions = models.CharField(max_length=255, null=True, blank=True)
    museum_catalogue_url = models.URLField(max_length=255, null=True, blank=True)
    image_rights = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['artist__name', 'title']

    def __str__(self):
        return self.title
