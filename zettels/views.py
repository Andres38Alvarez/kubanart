from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView
from .models import Artist, Artwork, Museum


class HomeView(TemplateView):
    template_name = 'zettels/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_artists'] = Artist.objects.count()
        context['num_artworks'] = Artwork.objects.count()
        context['num_museums'] = Museum.objects.count()
        context['num_countries'] = (
            Museum.objects.exclude(country='').values('country').distinct().count()
        )
        context['recent_artworks'] = (
            Artwork.objects.select_related('artist', 'museum').order_by('-id')[:6]
        )
        return context


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


class MapView(TemplateView):
    template_name = 'zettels/map.html'


class MediaView(TemplateView):
    template_name = 'zettels/media.html'


def artworks_geojson(request):
    """
    Un punto por obra, usando las coordenadas de su museo. Varias obras del
    mismo museo caen en el mismo punto -a propósito- y el popup enlaza a la
    ficha completa de cada una (el "mini-portafolio").
    """
    qs = (
        Artwork.objects
        .select_related('artist', 'museum')
        .filter(museum__latitude__isnull=False, museum__longitude__isnull=False)
    )

    features = []
    for artwork in qs:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [artwork.museum.longitude, artwork.museum.latitude],
            },
            'properties': {
                'artist': artwork.artist.name,
                'title': artwork.title,
                'year': artwork.year,
                'medium': artwork.medium,
                'institution': artwork.museum.name,
                'city': artwork.museum.city,
                'country': artwork.museum.country,
                'region': artwork.museum.region,
                'detail_url': reverse('zettels:artwork_detail', args=[artwork.pk]),
            },
        })

    return JsonResponse({'type': 'FeatureCollection', 'features': features})
