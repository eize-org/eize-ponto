from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from django.contrib.messages import get_messages
from .models import Bolsista, SessaoTrabalho, MINUTOS_ESPERADOS, HORAS_LIMITE_ABANDONO


class SessaoAbandonadaTests(TestCase):
    def setUp(self):
        self.client = Client(REMOTE_ADDR='127.0.0.1')
        self.bolsista = Bolsista.objects.create(nome='Guilherme', pendencia_min=300)

    def test_sessao_normal_menos_12h_fecha_normalmente(self):
        entrada = timezone.now() - timedelta(hours=3)
        sessao = SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=entrada
        )

        response = self.client.post(reverse('core:pagina_ponto'), {
            'id_bolsista': self.bolsista.id,
            'tipo': SessaoTrabalho.NORMAL
        })

        self.assertRedirects(response, reverse('core:pagina_ponto'))

        sessao.refresh_from_db()
        self.assertIsNotNone(sessao.saida)
        self.assertFalse(sessao.abandonada)
        self.assertEqual(sessao.min_trabalhados, 180)
        self.assertEqual(sessao.diferenca_min, -60)
        self.assertEqual(sessao.pendencia_abatida_min, 0)

        # Não deve ter criado uma nova sessão
        self.assertEqual(self.bolsista.sessaotrabalho_set.count(), 1)

    def test_sessao_normal_mais_12h_auto_encerra_e_abre_nova_entrada(self):
        entrada_antiga = timezone.now() - timedelta(hours=16)
        sessao_antiga = SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=entrada_antiga
        )

        response = self.client.post(reverse('core:pagina_ponto'), {
            'id_bolsista': self.bolsista.id,
            'tipo': SessaoTrabalho.NORMAL
        })

        self.assertRedirects(response, reverse('core:pagina_ponto'))

        # Verifica a sessão anterior encerrada como abandonada
        sessao_antiga.refresh_from_db()
        self.assertIsNotNone(sessao_antiga.saida)
        self.assertTrue(sessao_antiga.abandonada)
        self.assertEqual(sessao_antiga.min_trabalhados, MINUTOS_ESPERADOS)
        self.assertEqual(sessao_antiga.diferenca_min, 0)
        self.assertEqual(sessao_antiga.pendencia_abatida_min, 0)

        # Pendência não deve ter sido abatida por horas excedentes fantasmas
        self.bolsista.refresh_from_db()
        self.assertEqual(self.bolsista.pendencia_min, 300)

        # Uma nova sessão de entrada deve estar aberta para o bolsista
        sessoes = self.bolsista.sessaotrabalho_set.all().order_by('entrada')
        self.assertEqual(sessoes.count(), 2)

        nova_sessao = sessoes.last()
        self.assertIsNone(nova_sessao.saida)
        self.assertEqual(nova_sessao.tipo, SessaoTrabalho.NORMAL)
        self.assertFalse(nova_sessao.abandonada)

        # Notificação ao bolsista
        mensagens = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('automaticamente' in m.lower() and 'nova entrada' in m.lower() for m in mensagens))

    def test_sessao_pendencia_mais_12h_auto_encerra_com_teto_e_abre_nova_entrada(self):
        entrada_antiga = timezone.now() - timedelta(hours=14)
        sessao_antiga = SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.PENDENCIA,
            entrada=entrada_antiga
        )

        response = self.client.post(reverse('core:pagina_ponto'), {
            'id_bolsista': self.bolsista.id,
            'tipo': SessaoTrabalho.NORMAL
        })

        self.assertRedirects(response, reverse('core:pagina_ponto'))

        sessao_antiga.refresh_from_db()
        self.assertIsNotNone(sessao_antiga.saida)
        self.assertTrue(sessao_antiga.abandonada)
        # Trava no teto da jornada esperada (240 min)
        self.assertEqual(sessao_antiga.min_trabalhados, MINUTOS_ESPERADOS)
        # Abate no máximo 240 minutos da pendência, não as 14 horas
        self.assertEqual(sessao_antiga.pendencia_abatida_min, 240)

        self.bolsista.refresh_from_db()
        self.assertEqual(self.bolsista.pendencia_min, 60)  # 300 - 240

        # Nova sessão de ponto normal aberta
        sessoes = self.bolsista.sessaotrabalho_set.all().order_by('entrada')
        self.assertEqual(sessoes.count(), 2)
        nova_sessao = sessoes.last()
        self.assertIsNone(nova_sessao.saida)
        self.assertEqual(nova_sessao.tipo, SessaoTrabalho.NORMAL)

    def test_sessao_normal_mais_12h_abre_pendencia_se_solicitado(self):
        entrada_antiga = timezone.now() - timedelta(hours=18)
        sessao_antiga = SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=entrada_antiga
        )

        response = self.client.post(reverse('core:pagina_ponto'), {
            'id_bolsista': self.bolsista.id,
            'tipo': SessaoTrabalho.PENDENCIA
        })

        self.assertRedirects(response, reverse('core:pagina_ponto'))

        sessao_antiga.refresh_from_db()
        self.assertTrue(sessao_antiga.abandonada)
        self.assertIsNotNone(sessao_antiga.saida)
        self.assertEqual(sessao_antiga.min_trabalhados, MINUTOS_ESPERADOS)
        self.assertEqual(sessao_antiga.diferenca_min, 0)
        self.assertEqual(sessao_antiga.pendencia_abatida_min, 0)

        # Nova sessão de pagamento de pendência aberta
        sessoes = self.bolsista.sessaotrabalho_set.all().order_by('entrada')
        self.assertEqual(sessoes.count(), 2)
        nova_sessao = sessoes.last()
        self.assertIsNone(nova_sessao.saida)
        self.assertEqual(nova_sessao.tipo, SessaoTrabalho.PENDENCIA)

    def test_bloqueio_duplo_clique_apos_recuperacao(self):
        entrada_antiga = timezone.now() - timedelta(hours=15)
        SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=entrada_antiga
        )

        # Primeiro clique: recupera sessão abandonada e abre nova
        self.client.post(reverse('core:pagina_ponto'), {
            'id_bolsista': self.bolsista.id,
            'tipo': SessaoTrabalho.NORMAL
        })

        # Segundo clique imediato (< 5s)
        response2 = self.client.post(reverse('core:pagina_ponto'), {
            'id_bolsista': self.bolsista.id,
            'tipo': SessaoTrabalho.NORMAL
        })

        self.assertRedirects(response2, reverse('core:pagina_ponto'))
        mensagens = [m.message for m in get_messages(response2.wsgi_request)]
        self.assertTrue(any('aguarde alguns segundos' in m.lower() for m in mensagens))
        self.assertEqual(self.bolsista.sessaotrabalho_set.count(), 2)


class SessaoAbandonadaAdminSyncTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.client = Client(REMOTE_ADDR='127.0.0.1')
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@biblioteca.ufsc.br',
            password='senha_segura_admin'
        )
        self.client.force_login(self.admin_user)
        self.bolsista = Bolsista.objects.create(nome='Ana', pendencia_min=0)

    def test_admin_listagem_mostra_badge_e_filtra_abandonada(self):
        sessao_normal = SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=timezone.now() - timedelta(hours=4),
            saida=timezone.now()
        )
        sessao_abandonada = SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=timezone.now() - timedelta(hours=16),
            saida=timezone.now(),
            abandonada=True
        )

        url_changelist = reverse('admin:core_sessaotrabalho_changelist')
        response = self.client.get(url_changelist)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Abandonada')

        # Filtro: apenas abandonadas
        response_filtrado = self.client.get(url_changelist, {'abandonada__exact': '1'})
        self.assertEqual(response_filtrado.status_code, 200)
        self.assertContains(response_filtrado, 'Abandonada')
        self.assertEqual(len(response_filtrado.context['cl'].result_list), 1)
        self.assertEqual(response_filtrado.context['cl'].result_list[0].id, sessao_abandonada.id)

        # Filtro: apenas não-abandonadas
        response_normais = self.client.get(url_changelist, {'abandonada__exact': '0'})
        self.assertEqual(response_normais.status_code, 200)
        self.assertEqual(len(response_normais.context['cl'].result_list), 1)
        self.assertEqual(response_normais.context['cl'].result_list[0].id, sessao_normal.id)

    def test_admin_inline_bolsista_exibe_sinalizacao_abandonada(self):
        SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=timezone.now() - timedelta(hours=14),
            saida=timezone.now(),
            abandonada=True
        )

        url_bolsista = reverse('admin:core_bolsista_change', args=[self.bolsista.id])
        response = self.client.get(url_bolsista)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Abandonada')

    def test_sincronizacao_exporta_status_abandonada(self):
        from core.sync import montar_dados_bolsista
        sessao = SessaoTrabalho.objects.create(
            bolsista=self.bolsista,
            tipo=SessaoTrabalho.NORMAL,
            entrada=timezone.now() - timedelta(hours=14),
            saida=timezone.now(),
            abandonada=True
        )

        dados = montar_dados_bolsista(self.bolsista)
        self.assertEqual(len(dados['sessoes']), 1)
        self.assertIn('abandonada', dados['sessoes'][0])
        self.assertTrue(dados['sessoes'][0]['abandonada'])

