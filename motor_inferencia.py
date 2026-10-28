import json
from copy import deepcopy
from pathlib import Path

NIVEIS = ('junior', 'pleno', 'senior')


def carregar_base(caminho=None):
    arquivo = Path(caminho) if caminho is not None else Path(__file__).with_name('regras_carreiras.json')
    with arquivo.open('r', encoding='utf-8') as entrada:
        base = json.load(entrada)
    validar_base(base)
    return base


def validar_base(base):
    if not isinstance(base, dict):
        raise ValueError('A base de conhecimento deve ser um objeto JSON.')
    for campo in ('parametros', 'atributos', 'objetivos', 'trilhas'):
        if campo not in base or not isinstance(base[campo], dict):
            raise ValueError(f'Campo obrigatório ausente ou inválido: {campo}.')
    parametros = base['parametros']
    for campo in ('peso_afinidades', 'peso_objetivos', 'maximo_objetivos', 'faixa_afinidade', 'faixa_competencia', 'empate_tecnico_pontos'):
        if campo not in parametros:
            raise ValueError(f'Parâmetro ausente: {campo}.')
    if parametros['peso_afinidades'] < 0 or parametros['peso_objetivos'] < 0 or parametros['peso_afinidades'] + parametros['peso_objetivos'] != 100:
        raise ValueError('Os pesos gerais devem ser positivos e somar 100.')
    if not base['atributos'] or not base['objetivos'] or len(base['trilhas']) != 10:
        raise ValueError('A base precisa ter atributos, objetivos e exatamente 10 trilhas.')
    if parametros['maximo_objetivos'] < 1:
        raise ValueError('O número máximo de objetivos deve ser positivo.')
    for slug, trilha in base['trilhas'].items():
        if not trilha.get('nome') or not isinstance(trilha.get('pesos'), dict) or not trilha['pesos']:
            raise ValueError(f'Trilha inválida: {slug}.')
        if not trilha.get('competencias') or not isinstance(trilha['competencias'], list):
            raise ValueError(f'Competências ausentes em {slug}.')
        for atributo, peso in trilha['pesos'].items():
            if atributo not in base['atributos'] or isinstance(peso, bool) or not isinstance(peso, (int, float)) or peso <= 0:
                raise ValueError(f'Peso ou atributo inválido: {slug}/{atributo}.')
        if set(trilha.get('objetivos', [])) - set(base['objetivos']):
            raise ValueError(f'Objetivo desconhecido em {slug}.')
        ids = set()
        for competencia in trilha['competencias']:
            if competencia['id'] in ids:
                raise ValueError(f'Competência duplicada em {slug}: {competencia["id"]}.')
            ids.add(competencia['id'])
            niveis = competencia['niveis']
            if not all(n in niveis for n in NIVEIS):
                raise ValueError(f'Níveis ausentes em {slug}/{competencia["id"]}.')
            if not 1 <= niveis['junior'] <= niveis['pleno'] <= niveis['senior'] <= 5:
                raise ValueError(f'Níveis incoerentes em {slug}/{competencia["id"]}.')
            if competencia['ordem'] < 1 or not isinstance(competencia.get('tecnologias'), list):
                raise ValueError(f'Competência inválida em {slug}/{competencia["id"]}.')
        for penalidade in trilha.get('penalidades', []):
            if penalidade['atributo'] not in base['atributos'] or penalidade['operador'] not in ('<=', '<', '>=', '>') or penalidade['pontos'] < 0:
                raise ValueError(f'Penalidade inválida em {slug}.')
        if not isinstance(trilha.get('certificacoes_opcionais'), list) or not isinstance(trilha.get('projeto_portfolio'), dict):
            raise ValueError(f'Recomendações incompletas em {slug}.')
    return True


def _validar_perfil(base, afinidades, objetivos):
    esperados = set(base['atributos'])
    if set(afinidades) != esperados:
        faltam = sorted(esperados - set(afinidades))
        extras = sorted(set(afinidades) - esperados)
        raise ValueError(f'Afinidades incompletas ou desconhecidas. Faltando: {faltam}; extras: {extras}.')
    minimo, maximo = base['parametros']['faixa_afinidade']
    for atributo, valor in afinidades.items():
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor < minimo or valor > maximo:
            raise ValueError(f'Afinidade inválida em {atributo}: {valor}.')
    if len(objetivos) > base['parametros']['maximo_objetivos'] or len(set(objetivos)) != len(objetivos):
        raise ValueError('A quantidade de objetivos é inválida ou há objetivos duplicados.')
    if set(objetivos) - set(base['objetivos']):
        raise ValueError('Há um objetivo desconhecido.')


def _condicao(valor, operador, referencia):
    if operador == '<=':
        return valor <= referencia
    if operador == '<':
        return valor < referencia
    if operador == '>=':
        return valor >= referencia
    return valor > referencia


def calcular_ranking(base, afinidades, objetivos):
    _validar_perfil(base, afinidades, objetivos)
    p = base['parametros']
    minimo, maximo = p['faixa_afinidade']
    amplitude = maximo - minimo
    if amplitude <= 0:
        raise ValueError('Intervalo de afinidades inválido.')
    resultados = []
    for slug, trilha in base['trilhas'].items():
        pesos = trilha['pesos']
        soma_pesos = sum(pesos.values())
        contribuicoes = {atributo: peso * (afinidades[atributo] - minimo) / amplitude for atributo, peso in pesos.items()}
        media_ponderada = sum(contribuicoes.values()) / soma_pesos
        pontos_afinidades = p['peso_afinidades'] * media_ponderada
        maximo_objetivos = len(objetivos) or p['maximo_objetivos']
        encontros = [alvo for alvo in objetivos if alvo in trilha['objetivos']]
        pontos_objetivos = p['peso_objetivos'] * (len(encontros) / maximo_objetivos)
        penalidades = []
        for regra in trilha.get('penalidades', []):
            if _condicao(afinidades[regra['atributo']], regra['operador'], regra['valor']):
                penalidades.append({'motivo':regra['motivo'],'pontos':regra['pontos']})
        total_penalidades = sum(pen['pontos'] for pen in penalidades)
        pontuacao = max(0, min(100, pontos_afinidades + pontos_objetivos - total_penalidades))
        fortes = [
            {'atributo':atributo,'rotulo':base['atributos'][atributo]['rotulo'],'afinidade':afinidades[atributo], 'contribuicao':round(valor,3)}
            for atributo, valor in sorted(contribuicoes.items(), key=lambda item: (-item[1], -afinidades[item[0]], item[0]))
            if afinidades[atributo] >= 3
        ][:3]
        resultados.append({
            'id':slug,'nome':trilha['nome'],'descricao':trilha['descricao'],
            'compatibilidade':round(pontuacao,2),
            'pontos_afinidades':round(pontos_afinidades,2),
            'pontos_objetivos':round(pontos_objetivos,2),
            'pontos_penalidades':round(total_penalidades,2),
            'afinidades_fortes':fortes,'objetivos_em_comum':[base['objetivos'][x] for x in encontros],
            'penalidades':penalidades
        })
    resultados.sort(key=lambda resultado: (-resultado['compatibilidade'], -resultado['pontos_afinidades'], resultado['nome']))
    melhor = resultados[0]['compatibilidade']
    limite_empate = p['empate_tecnico_pontos']
    for posicao, resultado in enumerate(resultados, start=1):
        resultado['posicao'] = posicao
        resultado['empate_tecnico_com_primeiro'] = posicao > 1 and melhor - resultado['compatibilidade'] <= limite_empate
    return resultados


def avaliar_competencias(base, id_trilha, conhecimentos, nivel='junior'):
    if id_trilha not in base['trilhas']:
        raise ValueError(f'Trilha inexistente: {id_trilha}.')
    if nivel not in NIVEIS:
        raise ValueError('Nível de referência desconhecido.')
    trilha = base['trilhas'][id_trilha]
    competencias = trilha['competencias']
    esperados = {item['id'] for item in competencias}
    if set(conhecimentos) != esperados:
        raise ValueError('A avaliação deve conter todas as competências da trilha selecionada.')
    minimo, maximo = base['parametros']['faixa_competencia']
    if any(isinstance(valor,bool) or not isinstance(valor,(int,float)) or valor < minimo or valor > maximo for valor in conhecimentos.values()):
        raise ValueError('Todas as competências precisam estar entre 0 e 5.')
    lacunas = []
    consolidadas = []
    atingido = 0
    exigido = 0
    for competencia in competencias:
        atual = conhecimentos[competencia['id']]
        esperado = competencia['niveis'][nivel]
        diferenca = max(0, esperado - atual)
        atingido += min(atual, esperado)
        exigido += esperado
        registro = {'id':competencia['id'],'nome':competencia['nome'], 'nivel_atual':atual,
                    'nivel_requerido':esperado, 'lacuna':diferenca,'ordem':competencia['ordem'],
                    'tecnologias':competencia['tecnologias'],'orientacao':competencia['orientacao']}
        if diferenca:
            lacunas.append(registro)
        else:
            consolidadas.append(registro)
    lacunas.sort(key=lambda x: (x['ordem'], -x['lacuna'], x['nome']))
    consolidadas.sort(key=lambda x: (x['ordem'], x['nome']))
    tecnologias = []
    for lacuna in lacunas:
        for tech in lacuna['tecnologias']:
            if tech not in tecnologias:
                tecnologias.append(tech)
    marcos = {}
    for referencia in NIVEIS:
        necessario = sum(item['niveis'][referencia] for item in competencias)
        somatorio = sum(min(conhecimentos[item['id']],item['niveis'][referencia]) for item in competencias)
        marcos[referencia] = round(100*somatorio/necessario,1)
    nivel_indicativo = 'Em formação para Júnior'
    for referencia, rotulo in [('junior','Júnior'),('pleno','Pleno'),('senior','Sênior')]:
        if all(conhecimentos[item['id']] >= item['niveis'][referencia] for item in competencias):
            nivel_indicativo = rotulo
    return {'trilha_id':id_trilha,'nome_trilha':trilha['nome'],'nivel_referencia':nivel,
            'prontidao':round(100*atingido/exigido,1), 'marcos':marcos,
            'nivel_indicativo':nivel_indicativo,'lacunas':lacunas, 'consolidadas':consolidadas,
            'tecnologias_prioritarias':tecnologias,'certificacoes_opcionais':deepcopy(trilha['certificacoes_opcionais']),
            'projeto_portfolio':deepcopy(trilha['projeto_portfolio']),
            'proximos_passos':[f'Estudar {item["nome"]}: {item["orientacao"]}' for item in lacunas[:3]]}
