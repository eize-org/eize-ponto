from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bolsista, SessaoTrabalho
from .sync import sincronizar_bolsista_bg, sincronizar_sessao_bg

@receiver(post_save, sender=Bolsista)
def sync_bolsista_on_save(sender, instance, **kwargs):
    """Quando o admin edita um bolsista, avisa a nuvem."""
    sincronizar_bolsista_bg(instance)

@receiver(post_save, sender=SessaoTrabalho)
def sync_sessao_on_save(sender, instance, **kwargs):
    """
    Quando bate/fecha o ponto, avisa a nuvem.
    A sessão pode abater a pendência no save(), então mandamos
    a atualização do Bolsista também para o saldo bater.
    """
    sincronizar_bolsista_bg(instance.bolsista)
    sincronizar_sessao_bg(instance)
