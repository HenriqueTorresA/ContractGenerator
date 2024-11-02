# app_cg/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/editar/<int:codusuario>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/excluir/<int:codusuario>/', views.excluir_usuario, name='excluir_usuario'),
    path('inicio/', views.inicio, name='inicio'),
    path('tela-de-negociacao/', views.trading_screen, name='trading_screen'),
    path('tela-de-negociacao-decoracao/', views.trading_screen_decoration, name='trading_screen_decoration'),
    path('resumo-do-contrato/', views.summary_contract, name='summary_contract'),
    path('resumo-do-contrato-decoracao/', views.summary_contract_decoration, name='summary_contract_decoration'),
    path('dados-da-negociacao/', views.trading_data, name='trading_data'),
    path('dados-da-negociacao-decoracao/', views.trading_data_decoration, name='trading_data_decoration'),
    path('generate-pdf/', views.generate_pdf, name="generate_pdf"),
    path('generate-pdf-decoration/', views.generate_pdf_decoration, name="generate_pdf_decoration"),
    path('contratos-ativos/', views.preview_contract,name='preview_contract'),
    path('contratos-vencidos/', views.preview_contract_defeated,name='preview_contract_defeated'),
    path('deletar_contrato/<int:codcontrato>/', views.deletar_contrato, name='deletar_contrato'),
]
