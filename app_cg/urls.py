# app_cg/urls.py

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/', views.home, name='home'),
    # path('pwa-logo.png', views.logo_pwa, name='pwa-logo'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login, name='login'),
    path('habilitar_2fa/', views.habilitar_2fa, name='habilitar_2fa'),
    path('confirmar_2fa', views.confirmar_2fa, name='confirmar_otp'),
    path('verificar_otp', views.verificar_otp, name='verificar_otp'),
    path('logout/', views.logout, name='logout'),
    path('erro_sessao/', views.erro_sessao, name='erro_sessao'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    # path('usuarios/editar/<int:codusuario>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/excluir/', views.excluir_usuario, name='excluir_usuario'),
    path('inicio/', views.inicio, name='inicio'),

    # administracao
    path('empresas/', views.empresas, name='empresas'),
    path('empresas/cadastrar/', views.cadastrar_empresa, name='cadastrar_empresa'),
    path('empresas/excluir/', views.excluir_empresa, name='excluir_empresa'),

    # stardokmus
    path('tela-de-negociacao/', views.trading_screen, name='trading_screen'),
    path('tela-de-negociacao-decoracao/', views.trading_screen_decoration, name='trading_screen_decoration'),
    path('resumo-do-contrato/', views.summary_contract, name='summary_contract'),
    path('resumo-do-contrato-decoracao/', views.summary_contract_decoration, name='summary_contract_decoration'),
    path('dados-da-negociacao/', views.trading_data, name='trading_data'),
    path('dados-da-negociacao-decoracao/', views.trading_data_decoration, name='trading_data_decoration'),
    path('generate-pdf/', views.generate_pdf, name="generate_pdf"),
    path('generate-pdf-decoration/', views.generate_pdf_decoration, name="generate_pdf_decoration"),
    path('contratos-ativos/', views.preview_contract, {'operacao': 1}, name='preview_contract'),
    path('contratos-vencidos/', views.preview_contract, {'operacao': 2},name='preview_contract_defeated'),
    path('visualizar_contrato/<int:codcontrato>/', views.visualizar_contrato,name='visualizar_contrato'),
    path('deletar_contrato/<int:codcontrato>/', views.deletar_contrato, name='deletar_contrato'),
    path('editar_contrato/<int:codcontrato>/', views.editar_contrato, name='editar_contrato'),
    path('compartilhar_contrato/<int:codcontrato>/', views.compartilhar_contrato, name='compartilhar_contrato'),

    # DocFlow
    path('templates/', views.templates, name="templates"),
    path('templates/cadastrar/', views.cadastrar_template, name="cadastrar_template"),
    path('templates/deletar/', views.deletar_template, name="deletar_template"),
    path('variaveis/<int:codtemplate>/', views.gerenciar_variaveis, name="gerenciar_variaveis"),
    path('atualizar_variaveis/<int:codtemplate>/', views.atualizar_variaveis, name="atualizar_variaveis"),
    path('form_contrato/<int:codtemplate>/', views.form_contrato, name="form_contrato"),
    path('cadastrar_contrato/', views.cadastrar_contrato, name="cadastrar_contrato"),
    path('baixar_template/', views.baixar_template, name="baixar_template"),
    path('contratos/', views.contratos, name="contratos"),
    path('baixar_contrato/', views.baixar_contrato, name="baixar_contrato"),
]

# Apenas em modo de desenvolvimento (debug = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)