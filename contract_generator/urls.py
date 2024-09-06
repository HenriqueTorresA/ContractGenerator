"""
URL configuration for contract_generator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path
from django.views.generic import RedirectView
from app_cg import views
#from contract_generator.app_cg import admin

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('home/',views.home,name='home'),
    #path('',include('djangopwa.urls')),
    path('', RedirectView.as_view(url='/home/', permanent=True)),
    path('',include('pwa.urls')),
    #path('service-worker.js', views.ServiceWorkerView.as_view(), name='service-worker'),
    path('tela-de-negociacao/', views.trading_screen, name='trading_screen'),
    path('tela-de-negociacao-decoracao/', views.trading_screen_decoration, name='trading_screen_decoration'),
    path('resumo-do-contrato/', views.summary_contract, name='summary_contract'),
    path('resumo-do-contrato-decoracao/', views.summary_contract_decoration, name='summary_contract_decoration'),
    path('dados-da-negociacao/',views.trading_data, name='trading_data'),
    path('dados-da-negociacao-decoracao/',views.trading_data_decoration, name='trading_data_decoration'),
    path('generate-pdf/', views.generate_pdf, name="generate_pdf"),
    path('generate-pdf-decoration/', views.generate_pdf_decoration, name="generate_pdf_decoration"),
]
