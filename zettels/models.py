from django.db import models

class Artist(models.Model):
    name = models.CharField(max_length=100)
    birth_year = models.IntegerField(null=True,blank=True)
    death_year = models.IntegerField(null=True,blank=True)
    birthplace = models.CharField(max_length=100, null=True,blank=True)

    def __str__(self):
        return self.name

class Artwork(models.Model):
    # Delete the artist . on_delete=models.CASCADE deletes the pieces if the artist is deleted.
    
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='artworks')
    #fields of csv
    title = models.CharField(max_length=255)
    year = models.IntegerField(null=True, blank=True)
    medium = models.CharField(max_length=255, null=True, blank=True)
    dimensions = models.CharField(max_length=255, null=True, blank=True)
    museum_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    museum_catalogue_url = models.URLField(max_length=255, null=True, blank=True)
    image_rights = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    

    def __str__(self):
        return self.title
