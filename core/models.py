from django.db import models

MINUTOS_ESPERADOS = 240


def minutos_para_horas(minutos):
    sinal = '-' if minutos < 0 else ''
    total = abs(minutos)
    horas = total // 60
    mins = total % 60
    return f'{sinal}{horas:02d}:{mins:02d}h'


def horas_para_minutos(texto):
    """Converte 'HH:MM' em minutos totais."""
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
        return self.sessaotrabalho_set.filter(saida__isnull=True).first()

    def pendencia_display(self):
        return minutos_para_horas(self.pendencia_min)
    pendencia_display.short_description = 'Pendência'


class SessaoTrabalho(models.Model):
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE, verbose_name='Bolsista')
    entrada = models.DateTimeField('Entrada', auto_now_add=True)
    saida = models.DateTimeField('Saída', null=True, blank=True)
    min_trabalhados = models.IntegerField('Minutos Trabalhados', null=True, blank=True)
    diferenca_min = models.IntegerField('Diferença (min)', null=True, blank=True)
    pendencia_abatida_min = models.IntegerField('Pendência abatida (min)', null=True, blank=True)

    def mostra_trabalhados(self):
        if self.min_trabalhados is None:
            return None
        return minutos_para_horas(self.min_trabalhados)
    mostra_trabalhados.short_description = 'Trabalhado'

    def mostra_diferenca(self):
        if self.diferenca_min is None:
            return None
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
        return f'{self.bolsista}'