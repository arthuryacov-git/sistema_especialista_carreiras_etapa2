import json
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PASTA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA))


class Estado(dict):
    def __getattr__(self, chave):
        try:
            return self[chave]
        except KeyError as erro:
            raise AttributeError(chave) from erro

    def __setattr__(self, chave, valor):
        self[chave] = valor


class NovaExecucao(Exception):
    pass


class StreamlitSimulado:
    def __init__(self):
        self.session_state = Estado()
        self.controles_anteriores = set()
        self.controles_atuais = set()
        self.botao_formulario = ''
        self.documento_exportado = None
        self.mensagens = []

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, rastreamento):
        return False

    def set_page_config(self, **kwargs):
        pass

    def columns(self, quantidade):
        return [self for _ in range(quantidade)]

    def form(self, *args, **kwargs):
        return self

    def expander(self, *args, **kwargs):
        return self

    def container(self, *args, **kwargs):
        return self

    def _controle(self, chave, padrao):
        self.controles_atuais.add(chave)
        if chave not in self.session_state:
            self.session_state[chave] = padrao
        return self.session_state[chave]

    def text_input(self, *args, key, value='', **kwargs):
        return self._controle(key, value)

    def slider(self, *args, key, value, **kwargs):
        return self._controle(key, value)

    def selectbox(self, *args, options=None, key=None, index=0, **kwargs):
        if options is None:
            options = args[1]
        return self._controle(key, options[index])

    def multiselect(self, *args, options, key, default=None, **kwargs):
        return self._controle(key, list(default or [options[0]]))

    def form_submit_button(self, texto, **kwargs):
        return texto == self.botao_formulario

    def button(self, *args, **kwargs):
        return False

    def rerun(self):
        raise NovaExecucao()

    def download_button(self, *args, data, **kwargs):
        self.documento_exportado = json.loads(data)

    def warning(self, mensagem, **kwargs):
        self.mensagens.append(('warning', mensagem))

    def info(self, mensagem, **kwargs):
        self.mensagens.append(('info', mensagem))

    def __getattr__(self, nome):
        if nome in {'title', 'caption', 'subheader', 'write', 'metric', 'markdown',
                    'bar_chart', 'dataframe', 'divider', 'progress', 'success'}:
            return lambda *args, **kwargs: None
        raise AttributeError(nome)

    def executar(self):
        self.controles_atuais = set()
        try:
            with patch.dict(sys.modules, {'streamlit': self}):
                runpy.run_path(str(PASTA / 'app.py'), run_name='__main__')
        except NovaExecucao:
            pass
        for chave in self.controles_anteriores - self.controles_atuais:
            self.session_state.pop(chave, None)
        self.controles_anteriores = set(self.controles_atuais)


class TestInterfaceFluxo(unittest.TestCase):
    def test_respostas_continuam_disponiveis_apos_quatro_etapas(self):
        app = StreamlitSimulado()
        app.botao_formulario = 'Próximo: afinidades'
        app.executar()
        self.assertEqual(app.session_state.etapa, 1)

        app.botao_formulario = 'Próximo: objetivos profissionais'
        app.executar()
        self.assertEqual(app.session_state.etapa, 2)
        self.assertEqual(len(app.session_state.respostas_afinidades), 16)

        app.botao_formulario = 'Calcular ranking e abrir roadmap'
        app.executar()
        self.assertEqual(app.session_state.etapa, 3)
        self.assertTrue(app.session_state.respostas_objetivos)
        self.assertFalse(any(k.startswith('afinidade_') for k in app.session_state))

        app.botao_formulario = 'Gerar / atualizar roadmap'
        app.executar()
        self.assertFalse(any(tipo == 'warning' for tipo, _ in app.mensagens))
        self.assertIsNotNone(app.documento_exportado)
        self.assertEqual(len(app.documento_exportado['ranking']), 10)
        self.assertIn('plano', app.documento_exportado)
        self.assertEqual(len(app.documento_exportado['perfil']['afinidades']), 16)
        self.assertTrue(app.documento_exportado['perfil']['objetivos'])


if __name__ == '__main__':
    unittest.main()
