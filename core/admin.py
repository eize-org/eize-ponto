from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from django import forms
from django.utils.html import format_html
from .models import Bolsista, SessaoTrabalho, horas_para_minutos, minutos_para_horas


class FiltroSemana(admin.SimpleListFilter):
    title = 'semana'
    parameter_name = 'semana'

    def lookups(self, request, model_admin):
        opcoes = []
        hoje = timezone.now().date()
        inicio_semana_atual = hoje - timedelta(days=hoje.weekday())

        for i in range(4):  # últimas 4 semanas
            inicio = inicio_semana_atual - timedelta(weeks=i)
            fim = inicio + timedelta(days=6)
            label = f'{inicio.strftime("%d/%m")} a {fim.strftime("%d/%m")}'
            opcoes.append((str(i), label))
        return opcoes

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        hoje = timezone.now().date()
        inicio_semana_atual = hoje - timedelta(days=hoje.weekday())
        inicio = inicio_semana_atual - timedelta(weeks=int(self.value()))
        fim = inicio + timedelta(days=7)
        return queryset.filter(entrada__date__gte=inicio, entrada__date__lt=fim)


class BolsistaForm(forms.ModelForm):
    pendencia = forms.CharField(
        label='Pendência (HH:MM)',
        required=False,
        help_text='Ex: 04:00 para 1 turno (4h) de pendência.'
    )

    class Meta:
        model = Bolsista
        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            minutos = self.instance.pendencia_min
            sinal = '-' if minutos < 0 else ''
            total = abs(minutos)
            self.fields['pendencia'].initial = f'{sinal}{total // 60:02d}:{total % 60:02d}'
        else:
            self.fields['pendencia'].initial = '00:00'

    def clean_pendencia(self):
        texto = self.cleaned_data['pendencia'] or '00:00'
        try:
            return horas_para_minutos(texto)
        except (ValueError, IndexError):
            raise forms.ValidationError('Use o formato HH:MM, ex: 04:00')

    def save(self, commit=True):
        bolsista = super().save(commit=False)
        bolsista.pendencia_min = self.cleaned_data['pendencia']
        if commit:
            bolsista.save()
        return bolsista


class SessaoTrabalhoInline(admin.TabularInline):
    model = SessaoTrabalho
    extra = 0
    readonly_fields = ['mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']
    fields = ['tipo', 'entrada', 'saida', 'mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']
    can_delete = False


@admin.register(Bolsista)
class BolsistaAdmin(admin.ModelAdmin):
    form = BolsistaForm
    list_display = ['nome', 'pendencia_display']
    search_fields = ['nome']
    readonly_fields = ['link_historico']
    inlines = [SessaoTrabalhoInline]

    def link_historico(self, obj):
        if not obj.pk:
            return '—'
        url = f'/historico/{obj.token}/'
        return format_html('<a href="{0}" target="_blank">{0}</a>', url)
    link_historico.short_description = 'Link do histórico (pessoal e intransferível)'


@admin.register(SessaoTrabalho)
class SessaoTrabalhoAdmin(admin.ModelAdmin):
    list_display = ['bolsista', 'tipo', 'entrada', 'saida', 'mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']
    list_filter = ['bolsista', FiltroSemana, 'tipo']
    search_fields = ['bolsista__nome']
    readonly_fields = ['mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']