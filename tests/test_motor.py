import json
import random
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor_inferencia import avaliar_competencias, calcular_ranking, carregar_base, validar_base


class TestMotorInferencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = carregar_base()

    def afinidades(self, valor):
        return {chave:valor for chave in self.base['atributos']}

    def conhecimentos(self, trilha, valor):
        return {item['id']:valor for item in self.base['trilhas'][trilha]['competencias']}

    def test_base_contem_dez_trilhas_e_sessenta_competencias(self):
        self.assertEqual(len(self.base['trilhas']),10)
        self.assertEqual(len(self.base['atributos']),16)
        self.assertEqual(sum(len(t['competencias']) for t in self.base['trilhas'].values()),60)
        self.assertTrue(validar_base(self.base))

    def test_top_tres_e_ranking_crescente_em_posicao(self):
        ranking = calcular_ranking(self.base,self.afinidades(3),['resolver_problemas','qualidade'])
        self.assertEqual(len(ranking),10)
        self.assertEqual([r['posicao'] for r in ranking],list(range(1,11)))
        self.assertEqual([r['compatibilidade'] for r in ranking],sorted([r['compatibilidade'] for r in ranking],reverse=True))

    def test_perfil_mobile_destaca_area_mobile(self):
        atributos = self.afinidades(1)
        for chave in self.base['trilhas']['mobile']['pesos']:
            atributos[chave] = 5
        ranking = calcular_ranking(self.base,atributos,['criar_produtos','resolver_problemas'])
        self.assertEqual(ranking[0]['id'],'mobile')
        self.assertGreater(ranking[0]['compatibilidade'],85)

    def test_dez_perfis_prototipicos_alinhados(self):
        for slug, trilha in self.base['trilhas'].items():
            with self.subTest(trilha=slug):
                notas = self.afinidades(1)
                for atributo in trilha['pesos']:
                    notas[atributo] = 5
                ranking = calcular_ranking(self.base,notas,trilha['objetivos'][:2])
                self.assertEqual(ranking[0]['id'],slug)

    def test_quinhentos_perfis_aleatorios_sem_falhas(self):
        gerador = random.Random(2026)
        objetivos = list(self.base['objetivos'])
        for _ in range(500):
            notas = {atributo:gerador.randint(1,5) for atributo in self.base['atributos']}
            escolhas = gerador.sample(objetivos,2)
            ranking = calcular_ranking(self.base,notas,escolhas)
            self.assertEqual(len(ranking),10)
            self.assertEqual(len({linha['id'] for linha in ranking}),10)
            self.assertTrue(all(0 <= linha['compatibilidade'] <= 100 for linha in ranking))
            self.assertEqual(ranking, sorted(ranking,key=lambda x:(-x['compatibilidade'],-x['pontos_afinidades'],x['nome'])))

    def test_penalidade_efetivamente_reduz_pontuacao(self):
        perfil = self.afinidades(3)
        perfil['programacao'] = 1
        original = calcular_ranking(self.base,perfil,['resolver_problemas'])
        com_penalidade = next(x for x in original if x['id']=='backend')
        copia = deepcopy(self.base)
        copia['trilhas']['backend']['penalidades'] = []
        sem_penalidade = next(x for x in calcular_ranking(copia,perfil,['resolver_problemas']) if x['id']=='backend')
        self.assertGreater(sem_penalidade['compatibilidade'],com_penalidade['compatibilidade'])
        self.assertTrue(com_penalidade['penalidades'])

    def test_caso_ambiguo_reconhece_empate_tecnico(self):
        ranking = calcular_ranking(self.base,self.afinidades(5),[])
        self.assertEqual(ranking[0]['compatibilidade'],90)
        self.assertTrue(all(item['compatibilidade']==90 for item in ranking))
        self.assertTrue(all(item['empate_tecnico_com_primeiro'] for item in ranking[1:]))
        self.assertEqual(ranking,calcular_ranking(self.base,self.afinidades(5),[]))

    def test_pior_caso_notas_minimas_fica_nos_limites(self):
        ranking = calcular_ranking(self.base,self.afinidades(1),[])
        self.assertTrue(all(0 <= item['compatibilidade'] <= 100 for item in ranking))
        self.assertTrue(all(item['compatibilidade']==0 for item in ranking))

    def test_nota_invalida_rejeitada(self):
        notas = self.afinidades(3)
        notas['programacao'] = 6
        with self.assertRaises(ValueError):
            calcular_ranking(self.base,notas,[])

    def test_atributo_ausente_rejeitado(self):
        notas = self.afinidades(3)
        notas.pop('programacao')
        with self.assertRaises(ValueError):
            calcular_ranking(self.base,notas,[])

    def test_objetivo_desconhecido_rejeitado(self):
        with self.assertRaises(ValueError):
            calcular_ranking(self.base,self.afinidades(3),['objetivo_inexistente'])

    def test_mais_que_dois_objetivos_rejeitado(self):
        with self.assertRaises(ValueError):
            calcular_ranking(self.base,self.afinidades(3),list(self.base['objetivos'])[:3])

    def test_totalmente_iniciante_tem_gaps(self):
        resultado = avaliar_competencias(self.base,'backend',self.conhecimentos('backend',0))
        self.assertEqual(resultado['prontidao'],0)
        self.assertEqual(len(resultado['lacunas']),6)
        self.assertEqual(resultado['nivel_indicativo'],'Em formação para Júnior')
        self.assertEqual([x['ordem'] for x in resultado['lacunas']],sorted(x['ordem'] for x in resultado['lacunas']))

    def test_todos_niveis_cinco_sem_gaps(self):
        resultado = avaliar_competencias(self.base,'qa',self.conhecimentos('qa',5))
        self.assertEqual(resultado['prontidao'],100)
        self.assertFalse(resultado['lacunas'])
        self.assertEqual(resultado['nivel_indicativo'],'Sênior')
        self.assertEqual(resultado['marcos'],{'junior':100.0,'pleno':100.0,'senior':100.0})

    def test_gap_especifico_e_prioridade(self):
        notas = self.conhecimentos('backend',5)
        notas['linguagem'] = 1
        notas['api'] = 2
        resultado = avaliar_competencias(self.base,'backend',notas)
        self.assertEqual([item['id'] for item in resultado['lacunas']],['linguagem','api'])
        self.assertEqual([item['lacuna'] for item in resultado['lacunas']],[2,1])
        self.assertTrue(resultado['tecnologias_prioritarias'])
        self.assertEqual(len(resultado['proximos_passos']),2)

    def test_validacao_conhecimentos_incompletos(self):
        with self.assertRaises(ValueError):
            avaliar_competencias(self.base,'backend',{'linguagem':3})

    def test_calculo_pleno_senior(self):
        notas = self.conhecimentos('backend',3)
        junior = avaliar_competencias(self.base,'backend',notas,'junior')
        pleno = avaliar_competencias(self.base,'backend',notas,'pleno')
        senior = avaliar_competencias(self.base,'backend',notas,'senior')
        self.assertEqual(junior['prontidao'],100)
        self.assertGreater(junior['prontidao'],pleno['prontidao'])
        self.assertGreater(pleno['prontidao'],senior['prontidao'])

    def test_json_externo_lido_dinamicamente(self):
        copia = deepcopy(self.base)
        copia['trilhas']['backend']['nome'] = 'Back-end Customizado'
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)/'base.json'
            caminho.write_text(json.dumps(copia,ensure_ascii=False),encoding='utf-8')
            carregada = carregar_base(caminho)
        self.assertEqual(carregada['trilhas']['backend']['nome'],'Back-end Customizado')
        self.assertNotEqual(self.base['trilhas']['backend']['nome'],carregada['trilhas']['backend']['nome'])

    def test_base_com_limites_invalidos_rejeitada(self):
        copia = deepcopy(self.base)
        copia['trilhas']['backend']['competencias'][0]['niveis']['junior'] = 5
        with self.assertRaises(ValueError):
            validar_base(copia)


if __name__ == '__main__':
    unittest.main(verbosity=2)
