from django.db import models
from django.utils import timezone

MINUTOS_ESPERADOS = 240


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

    class Meta:
        verbose_name = 'Bolsista'
        verbose_name_plural = 'Bolsistas'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def sessao_aberta(self):
        """Retorna qualquer sessão aberta, de qualquer tipo."""
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

    def save(self, *args, **kwargs):
        if self.entrada and self.saida:
            self.min_trabalhados = int((self.saida - self.entrada).total_seconds() / 60)

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

    class Meta:
        verbose_name = 'Sessão'
        verbose_name_plural = 'Sessões'
        ordering = ['-entrada']

    def __str__(self):
        return f'{self.bolsista} ({self.get_tipo_display()})'