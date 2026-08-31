from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.pagina_ponto, name='pagina_ponto'),
    path('historico/<str:token>/', views.historico_bolsista, name='historico_bolsista'),
]