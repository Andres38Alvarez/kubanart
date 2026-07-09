from django.urls import path
from . import views

app_name = 'zettels'
urlpatterns = [
    path('artist/', views.ArtistListView.as_view(), name='artist_list'),
    path('artists/<int:pk>/', views.ArtistDetailView.as_view(), name='artist_detail'),
    path('artworks/', views.ArtworkListView.as_view(), name='artwork_list'),
    path('artworks/<int:pk>/', views.ArtworkDetailView.as_view(), name='artwork_detail'),
]
