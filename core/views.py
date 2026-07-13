from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from datetime import timedelta
from .models import Bolsista, SessaoTrabalho, MINUTOS_ESPERADOS
from .serializers import BolsistaSerializer, SessaoTrabalhoSerializer

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


@transaction.atomic
def pagina_ponto(request):
    bolsistas = Bolsista.objects.all()

    if request.method == 'POST':
        id_bolsista = request.POST.get('id_bolsista')
        try:
            bolsista = Bolsista.objects.select_for_update().get(pk=id_bolsista)

            sessao_aberta = SessaoTrabalho.objects.select_for_update().filter(
                bolsista=bolsista, saida__isnull=True
            ).first()

            ultima_sessao = SessaoTrabalho.objects.filter(bolsista=bolsista).order_by('-entrada').first()
            if ultima_sessao and (timezone.now() - ultima_sessao.entrada) < timedelta(seconds=5):
                acao = 'saída' if ultima_sessao.saida else 'entrada'
                messages.error(
                    request,
                    f'Aguarde alguns segundos antes de bater o ponto novamente. '
                    f'A {acao} de {bolsista.nome} já foi registrada.'
                )
                return redirect('core:pagina_ponto')

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
                messages.warning(request, f'Saída de {bolsista.nome} registrada!')

        except Bolsista.DoesNotExist:
            messages.error(request, 'Bolsista não encontrado.')

        return redirect('core:pagina_ponto')
    
    return render(request, 'core/ponto.html', {'bolsistas': bolsistas})