from django import forms
from django.contrib import admin
from .models import Bolsista, SessaoTrabalho, horas_para_minutos, minutos_para_horas


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
    readonly_fields = ['entrada', 'saida', 'mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']
    fields = ['entrada', 'saida', 'mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']
    can_delete = False


@admin.register(Bolsista)
class BolsistaAdmin(admin.ModelAdmin):
    form = BolsistaForm
    list_display = ['nome', 'pendencia_display']
    search_fields = ['nome']
    inlines = [SessaoTrabalhoInline]


@admin.register(SessaoTrabalho)
class SessaoTrabalhoAdmin(admin.ModelAdmin):
    list_display = ['bolsista', 'entrada', 'saida', 'mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']
    list_filter = ['entrada']
    search_fields = ['bolsista__nome']
    readonly_fields = ['entrada', 'saida', 'mostra_trabalhados', 'mostra_diferenca', 'mostra_pendencia_abatida']