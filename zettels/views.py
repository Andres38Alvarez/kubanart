from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView
from .models import Artist, Artwork, Museum, PressMention, Publication


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentions'] = (
            PressMention.objects
            .select_related('publication')
            .prefetch_related('artists')
            .all()
        )
        context['num_mentions'] = context['mentions'].count()
        context['num_publications'] = Publication.objects.count()
        context['num_cuba_diaspora'] = (
            PressMention.objects.filter(publication__origin=Publication.Origin.CUBA_DIASPORA).count()
        )
        context['num_international'] = (
            PressMention.objects.filter(publication__origin=Publication.Origin.INTERNATIONAL).count()
        )
        return context


def artworks_geojson(request):
    """
    Un punto por museo (no por obra): varias obras del mismo museo comparten
    coordenadas, así que agruparlas evita que los marcadores se apilen
    exactamente unos sobre otros y solo el de arriba responda al click. El
    popup de cada museo lista todas sus obras, cada una enlazando a su ficha
    completa (el "mini-portafolio").
    """
    qs = (
        Artwork.objects
        .select_related('artist', 'museum')
        .filter(museum__latitude__isnull=False, museum__longitude__isnull=False)
        .order_by('museum_id', 'artist__name', 'title')
    )

    museums = {}
    for artwork in qs:
        museum = artwork.museum
        if museum.id not in museums:
            museums[museum.id] = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [museum.longitude, museum.latitude],
                },
                'properties': {
                    'institution': museum.name,
                    'city': museum.city,
                    'country': museum.country,
                    'region': museum.region,
                    'artworks': [],
                },
            }
        museums[museum.id]['properties']['artworks'].append({
            'id': artwork.pk,
            'artist': artwork.artist.name,
            'title': artwork.title,
            'year': artwork.year,
            'medium': artwork.medium,
            'detail_url': reverse('zettels:artwork_detail', args=[artwork.pk]),
        })

    return JsonResponse({'type': 'FeatureCollection', 'features': list(museums.values())})
