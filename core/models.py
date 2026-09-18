from datetime import timedelta
import secrets
from django.db import models
from django.utils import timezone
from django.utils.html import format_html

MINUTOS_ESPERADOS = 240
HORAS_LIMITE_ABANDONO = 12


def minutos_para_horas(minutos):
    sinal = '-' if minutos < 0 else ''
    total = abs(minutos)
    horas = total // 60
    mins = total % 60
    return f'{sinal}{horas:02d}:{mins:02d}h'


def horas_para_minutos(texto):
    texto = texto.strip()
    sinal = -1 if texto.startswith('-') else 1
    texto = texto.lstrip('-')
    horas, mins = texto.split(':')
    return sinal * (int(horas) * 60 + int(mins))


class Bolsista(models.Model):
    nome = models.CharField("Nome", max_length=100)
    pendencia_min = models.IntegerField('Pendência (min)', default=0)
    token = models.CharField('Token de acesso', max_length=64, unique=True, blank=True)

    class Meta:
        verbose_name = 'Bolsista'
        verbose_name_plural = 'Bolsistas'
        ordering = ['nome']

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(24)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    def sessao_aberta(self):
        return self.sessaotrabalho_set.filter(saida__isnull=True).first()

    def pendencia_display(self):
        return minutos_para_horas(self.pendencia_min)
    pendencia_display.short_description = 'Pendência'


class SessaoTrabalho(models.Model):
    NORMAL = 'normal'
    PENDENCIA = 'pendencia'
    TIPOS = [
        (NORMAL, 'Normal'),
        (PENDENCIA, 'Pagamento de pendência'),
    ]

    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE, verbose_name='Bolsista')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPOS, default=NORMAL)
    entrada = models.DateTimeField('Entrada', default=timezone.now)
    saida = models.DateTimeField('Saída', null=True, blank=True)
    min_trabalhados = models.IntegerField('Minutos Trabalhados', null=True, blank=True)
    diferenca_min = models.IntegerField('Diferença (min)', null=True, blank=True)
    pendencia_abatida_min = models.IntegerField('Pendência abatida (min)', null=True, blank=True)
    abandonada = models.BooleanField('Abandonada', default=False)

    def esta_abandonada(self, agora=None):
        if self.saida is not None:
            return self.abandonada
        agora = agora or timezone.now()
        return (agora - self.entrada) > timedelta(hours=HORAS_LIMITE_ABANDONO)

    def save(self, *args, **kwargs):
        if self.entrada and self.saida:
            duracao_real_min = int((self.saida - self.entrada).total_seconds() / 60)
            if self.abandonada or duracao_real_min > (HORAS_LIMITE_ABANDONO * 60):
                self.abandonada = True
                self.min_trabalhados = MINUTOS_ESPERADOS

                if self.pendencia_abatida_min is None:
                    if self.tipo == self.PENDENCIA:
                        self.diferenca_min = None
                        abatido = min(self.min_trabalhados, self.bolsista.pendencia_min)
                        self.bolsista.pendencia_min -= abatido
                        self.bolsista.save()
                        self.pendencia_abatida_min = abatido
                    else:
                        # Sessão normal abandonada: limitada a 4h e sem saldo excedente
                        self.diferenca_min = 0
                        self.pendencia_abatida_min = 0
            else:
                self.min_trabalhados = duracao_real_min

                if self.pendencia_abatida_min is None:
                    if self.tipo == self.PENDENCIA:
                        # Todo o tempo trabalhado abate diretamente da pendência
                        self.diferenca_min = None
                        abatido = min(self.min_trabalhados, self.bolsista.pendencia_min)
                        self.bolsista.pendencia_min -= abatido
                        self.bolsista.save()
                        self.pendencia_abatida_min = abatido
                    else:
                        # Sessão normal: só abate o excedente acima das 4h
                        self.diferenca_min = self.min_trabalhados - MINUTOS_ESPERADOS
                        excedente = max(self.diferenca_min, 0)
                        abatido = 0
                        if excedente > 0 and self.bolsista.pendencia_min > 0:
                            abatido = min(excedente, self.bolsista.pendencia_min)
                            self.bolsista.pendencia_min -= abatido
                            self.bolsista.save()
                        self.pendencia_abatida_min = abatido

        super().save(*args, **kwargs)

    def mostra_trabalhados(self):
        if self.min_trabalhados is None:
            return None
        return minutos_para_horas(self.min_trabalhados)
    mostra_trabalhados.short_description = 'Trabalhado'

    def mostra_diferenca(self):
        if self.diferenca_min is None:
            return '—' if self.tipo == self.PENDENCIA else None
        return minutos_para_horas(self.diferenca_min)
    mostra_diferenca.short_description = 'Diferença'

    def mostra_pendencia_abatida(self):
        if self.pendencia_abatida_min is None:
            return None
        return minutos_para_horas(self.pendencia_abatida_min)
    mostra_pendencia_abatida.short_description = 'Pendência abatida'

    def mostra_abandonada(self):
        if self.abandonada:
            return format_html(
                '<span style="color: #842029; background-color: #f8d7da; padding: 2px 8px; '
                'border-radius: 4px; border: 1px solid #f5c2c7; font-weight: 600; font-size: 0.85em;">{}</span>',
                '⚠️ Abandonada'
            )
        return '—'
    mostra_abandonada.short_description = 'Status'

    class Meta:
        verbose_name = 'Sessão'
        verbose_name_plural = 'Sessões'
        ordering = ['-entrada']

    def __str__(self):
        return f'{self.bolsista} ({self.get_tipo_display()})'