from rest_framework import serializers
from .models import Bolsista, SessaoTrabalho

class SessaoTrabalhoSerializer(serializers.ModelSerializer):

    class Meta:
        model = SessaoTrabalho
        fields = ['id', 'entrada', 'saida', 'min_trabalhados', 'diferenca_min', 'mostra_diferenca', 'abandonada']
        
class BolsistaSerializer(serializers.ModelSerializer):
    sessao_aberta = serializers.SerializerMethodField()
    sessoes_recentes = serializers.SerializerMethodField()

    class Meta:
        model = Bolsista
        fields = ['id', 'nome', 'sessao_aberta', 'sessoes_recentes',]
    
    def get_sessao_aberta(self, obj):
        sessao = obj.sessao_aberta()
        return SessaoTrabalhoSerializer(sessao).data if sessao else None
    
    def get_sessoes_recentes(self, obj):
        sessoes = obj.sessaotrabalho_set.all()[:5]
        return SessaoTrabalhoSerializer(sessoes, many=True).data