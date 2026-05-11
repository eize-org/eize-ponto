from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Bolsista, SessaoTrabalho, MINUTOS_ESPERADOS
from .serializers import BolsistaSerializer, SessaoTrabalhoSerializer
from django.conf import settings

@api_view(['GET'])
def lista_bolsistas(request):
    bolsistas = Bolsista.objects.all()
    serializer = BolsistaSerializer(bolsistas, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def busca_bolsista(request, pk):
    try:
        bolsista = Bolsista.objects.get(pk=pk)
    except Bolsista.DoesNotExist:
        return Response({'error': 'Bolsista não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = BolsistaSerializer(bolsista)
    return Response(serializer.data)

@api_view(['POST'])
def ponto_bolsista(request, pk):
    try:
        bolsista = Bolsista.objects.get(pk=pk)
    except Bolsista.DoesNotExist:
        return Response({'error': 'Bolsista não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    sessao_aberta = bolsista.sessao_aberta()

    if sessao_aberta is None:
        sessao = SessaoTrabalho.objects.create(bolsista=bolsista)
        return Response({
            'acao': 'entrada',
            'mensagem': 'Entrada registrada com sucesso!',
            'sessao': SessaoTrabalhoSerializer(sessao).data,
        }, status=status.HTTP_201_CREATED)
    else:
        agora = timezone.now()
        trabalhou = int((agora - sessao_aberta.entrada).total_seconds() / 60)
        sessao_aberta.saida = agora
        sessao_aberta.min_trabalhados = trabalhou
        sessao_aberta.diferenca_min = trabalhou - MINUTOS_ESPERADOS
        sessao_aberta.save()
        return Response({
            'acao': 'saida',
            'mensagem': 'Saída registrada com sucesso!',
            'sessao': SessaoTrabalhoSerializer(sessao_aberta).data,
        })
    
@api_view(['GET'])
def sessoes_bolsista(request, pk):
    try:
        bolsista = Bolsista.objects.get(pk=pk)
    except Bolsista.DoesNotExist:
        return Response({'error': 'Bolsista não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    sessoes = bolsista.sessaotrabalho_set.all()
    serializer = SessaoTrabalhoSerializer(sessoes, many=True)
    return Response(serializer.data)

def pagina_ponto(request):
    bolsistas = Bolsista.objects.all()

    if request.method == 'POST':
        # senha = request.POST.get('senha')

        # if senha != settings.SENHA_PONTO:
        #    messages.error(request, 'Senha incorreta.')
        #    return redirect('core:pagina_ponto')

        id_bolsista = request.POST.get('id_bolsista')
        try:
            bolsista = Bolsista.objects.get(pk=id_bolsista)
            sessao_aberta = bolsista.sessao_aberta()

            if sessao_aberta is None:
                SessaoTrabalho.objects.create(bolsista=bolsista)
                messages.success(request, f'Entrada de {bolsista.nome} registrada!')
            else:
                agora = timezone.now()
                trabalhou = int((agora - sessao_aberta.entrada).total_seconds() / 60)
                sessao_aberta.saida = agora
                sessao_aberta.min_trabalhados = trabalhou
                sessao_aberta.diferenca_min = trabalhou - MINUTOS_ESPERADOS
                sessao_aberta.save()
                messages.success(request, f'Saída de {bolsista.nome} registrada!', extra_tags='saida')

        except Bolsista.DoesNotExist:
            messages.error(request, 'Bolsista não encontrado.')

        return redirect('core:pagina_ponto')
    
    return render(request, 'core/ponto.html', {'bolsistas': bolsistas})