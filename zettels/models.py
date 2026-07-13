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
