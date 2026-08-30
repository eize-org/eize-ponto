from django.urls import path
from . import views

urlpatterns = [
    path('bolsistas/', views.lista_bolsistas, name='lista_bolsistas'),
    path('bolsistas/<int:pk>/', views.busca_bolsista, name='busca_bolsista'),
    path('bolsistas/<int:pk>/ponto/', views.ponto_bolsista, name='ponto_bolsista'),
    path('bolsistas/<int:pk>/sessoes/', views.sessoes_bolsista, name='sessoes_bolsista'),
    path('historico/<str:token>/', views.historico_bolsista, name='historico_bolsista'),
]
