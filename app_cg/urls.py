# app_cg/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login, name='login'),
    path('tela-de-negociacao/', views.trading_screen, name='trading_screen'),
    path('tela-de-negociacao-decoracao/', views.trading_screen_decoration, name='trading_screen_decoration'),
    path('resumo-do-contrato/', views.summary_contract, name='summary_contract'),
    path('resumo-do-contrato-decoracao/', views.summary_contract_decoration, name='summary_contract_decoration'),
    path('dados-da-negociacao/', views.trading_data, name='trading_data'),
    path('dados-da-negociacao-decoracao/', views.trading_data_decoration, name='trading_data_decoration'),
    path('generate-pdf/', views.generate_pdf, name="generate_pdf"),
    path('generate-pdf-decoration/', views.generate_pdf_decoration, name="generate_pdf_decoration"),
    path('visualizacao-de-contratos/', views.preview_contract,name='preview_contract'),
]
