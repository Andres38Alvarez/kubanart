from django.views.generic import ListView, DetailView
from .models import Artist, Artwork

class ArtistListView(ListView):
    model = Artist
    template_name = 'zettels/artist_list.html'
    context_object_name = 'artist'

class ArtistDetailView(DetailView):
    model = Artist
    template_name = 'zettels/artist_detail.html'
    context_object_name = 'artist'

class ArtworkListView(ListView):
    model = Artwork
    template_name = 'zettels/artwork_list.html'
    context_object_name = 'artworks'

class ArtworkDetailView(DetailView):
    model = Artwork
    template_name = 'zettels/artwork_detail.html'
    context_object_name = 'artwork'
