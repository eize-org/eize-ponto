from django.core.management.base import BaseCommand
from core.models import Bolsista
from core.sync import sincronizar_historico_bolsista


class Command(BaseCommand):
    help = "Sincroniza o histórico de todos os bolsistas com o repositório GitHub Pages."

    def handle(self, *args, **options):
        bolsistas = Bolsista.objects.all().order_by('nome')
        total = bolsistas.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("Nenhum bolsista cadastrado."))
            return

        self.stdout.write(f"Iniciando reconciliação em lote de {total} bolsista(s)...")

        sucessos = 0
        erros = 0

        for i, b in enumerate(bolsistas, start=1):
            self.stdout.write(f"[{i}/{total}] Sincronizando {b.nome}...", ending=" ")
            ok, err = sincronizar_historico_bolsista(b)
            if ok:
                self.stdout.write(self.style.SUCCESS("OK"))
                sucessos += 1
            else:
                self.stdout.write(self.style.ERROR(f"FALHOU ({err})"))
                erros += 1

        self.stdout.write("")
        if erros == 0:
            self.stdout.write(self.style.SUCCESS(f"Reconciliação concluída com sucesso! ({sucessos}/{total})"))
        else:
            self.stdout.write(self.style.WARNING(f"Concluído com avisos: {sucessos} com sucesso, {erros} falha(s)."))
