# ContractGenerator/urls.py

from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Inclua o arquivo de URLs do app_cg
    path('', RedirectView.as_view(url='/home/', permanent=True)),
    path('', include('app_cg.urls')),

    # Inclua o PWA como uma rota separada, se necessário
    path('', include('pwa.urls')),
]
