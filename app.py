import json
import pandas as pd
import streamlit as st

from motor_inferencia import avaliar_competencias, calcular_ranking, carregar_base

st.set_page_config(page_title='Consultor de Carreiras em TI', page_icon='🧭', layout='wide')

base = carregar_base()

if 'etapa' not in st.session_state:
    st.session_state.etapa = 0
if 'avaliacoes' not in st.session_state:
    st.session_state.avaliacoes = {}


def ir_para(numero):
    st.session_state.etapa = numero
    st.rerun()


def mostrar_resultados():
    afinidades = dict(st.session_state['respostas_afinidades'])
    objetivos = list(st.session_state['respostas_objetivos'])
    ranking = calcular_ranking(base, afinidades, objetivos)

    st.subheader('Ranking de compatibilidade: suas 3 trilhas principais')
    st.caption('Percentuais indicam aderência estimada às regras configuradas, não probabilidade de sucesso ou avaliação psicológica.')
    colunas = st.columns(3)
    for i, coluna in enumerate(colunas):
        item = ranking[i]
        with coluna:
            st.metric(f'{i+1}º lugar', f'{item["compatibilidade"]:.1f}%')
            st.markdown(f'**{item["nome"]}**')
            st.caption(item['descricao'])
            if item['empate_tecnico_com_primeiro']:
                st.info('Empate técnico com a primeira colocada (até 2 pontos).')

    tabela = pd.DataFrame([
        {'Trilha':item['nome'], 'Compatibilidade (%)':item['compatibilidade'],
         'Afinidades (pontos)':item['pontos_afinidades'],
         'Objetivos (pontos)':item['pontos_objetivos'],
         'Penalidades (pontos)':item['pontos_penalidades']}
        for item in ranking
    ])
    st.subheader('Comparação entre as 10 carreiras')
    st.bar_chart(tabela.set_index('Trilha')[['Compatibilidade (%)']], horizontal=True, height=445)
    with st.expander('Ver detalhes do cálculo das 10 trilhas'):
        st.dataframe(tabela, use_container_width=True, hide_index=True)
        st.write('**Fórmula aplicada:** 90 × média ponderada normalizada das afinidades + até 10 pontos por objetivos coincidentes − penalidades por conflitos. Resultado limitado de 0% a 100%.')
        st.write('Nota 1 equivale a 0% de afinidade naquela dimensão e nota 5 a 100%; os pesos, os objetivos e as regras de penalidade estão no JSON.')

    st.subheader('Por que estas recomendações?')
    for item in ranking[:3]:
        with st.expander(f'{item["posicao"]}º — {item["nome"]} ({item["compatibilidade"]:.1f}%)'):
            if item['afinidades_fortes']:
                st.write('**Afinidades relevantes:** ' + ', '.join(f'{a["rotulo"]} ({a["afinidade"]}/5)' for a in item['afinidades_fortes']))
            else:
                st.write('As afinidades relevantes receberam notas baixas; a indicação é apenas comparativa.')
            if item['objetivos_em_comum']:
                st.write('**Objetivos alinhados:** ' + '; '.join(item['objetivos_em_comum']))
            else:
                st.write('**Objetivos alinhados:** nenhum entre os selecionados.')
            if item['penalidades']:
                st.write('**Conflitos detectados:** ' + '; '.join(f'{p["motivo"]} (−{p["pontos"]} pontos)' for p in item['penalidades']))
            else:
                st.write('**Conflitos:** não foram identificados conflitos nas regras desta trilha.')

    st.divider()
    st.subheader('Mapa de competências e plano individual de estudo')
    st.write('Escolha uma das dez trilhas para avaliar competências. O sistema verifica o que falta para o nível de referência selecionado, prioriza estudos e indica um projeto de portfólio.')
    ids = [item['id'] for item in ranking]
    trilha_id = st.selectbox('Trilha para aprofundar', options=ids, format_func=lambda chave:base['trilhas'][chave]['nome'], key='trilha_escolhida')
    nivel = st.selectbox('Nível de referência para o roadmap', options=['junior','pleno','senior'], format_func=lambda x:{'junior':'Júnior','pleno':'Pleno','senior':'Sênior'}[x], key='nivel_meta')
    st.caption('Comece pelo nível Júnior; Pleno e Sênior são comparações adicionais baseadas em requisitos de estudo. Experiência profissional não pode ser medida por estes controles.')
    competencias = base['trilhas'][trilha_id]['competencias']
    st.markdown('**Autoavaliação das competências da trilha**')
    st.caption('0 = ainda não conheço · 1 = iniciante · 2 = básico · 3 = intermediário · 4 = avançado · 5 = domínio elevado. Clique em "Gerar / atualizar roadmap" para confirmar suas notas.')
    with st.form(f'avaliacao_{trilha_id}'):
        colunas = st.columns(2)
        for posicao, competencia in enumerate(competencias):
            with colunas[posicao % 2]:
                st.slider(competencia['nome'], min_value=0, max_value=5,
                          value=st.session_state.avaliacoes.get(trilha_id, {}).get(competencia['id'], 0),
                          key=f'conhecimento_{trilha_id}_{competencia["id"]}',
                          help=competencia['orientacao'])
        confirmado = st.form_submit_button('Gerar / atualizar roadmap', type='primary', use_container_width=True)
    if confirmado:
        st.session_state.avaliacoes[trilha_id] = {
            competencia['id']:int(st.session_state[f'conhecimento_{trilha_id}_{competencia["id"]}'])
            for competencia in competencias
        }

    if trilha_id not in st.session_state.avaliacoes:
        st.info('Preencha a autoavaliação e clique em “Gerar / atualizar roadmap” para ver suas lacunas de competências.')
        return

    plano = avaliar_competencias(base, trilha_id, st.session_state.avaliacoes[trilha_id], nivel)
    st.subheader(f'Roadmap personalizado: {plano["nome_trilha"]}')
    c1,c2,c3 = st.columns(3)
    c1.metric('Preparação estimada para a meta', f'{plano["prontidao"]:.1f}%')
    c2.metric('Competências a desenvolver', str(len(plano['lacunas'])))
    c3.metric('Competências no nível esperado', str(len(plano['consolidadas'])))
    st.progress(plano['prontidao']/100)
    st.caption(f'Nível indicativo segundo a autoavaliação: {plano["nivel_indicativo"]}. Isso não equivale a certificação nem a senioridade profissional comprovada.')

    with st.expander('Comparar preparação estimada para Júnior, Pleno e Sênior'):
        c1,c2,c3 = st.columns(3)
        c1.metric('Júnior', f'{plano["marcos"]["junior"]:.1f}%')
        c2.metric('Pleno', f'{plano["marcos"]["pleno"]:.1f}%')
        c3.metric('Sênior', f'{plano["marcos"]["senior"]:.1f}%')

    if plano['lacunas']:
        st.markdown('**Etapas de estudo, na ordem das dependências**')
        for posicao, lacuna in enumerate(plano['lacunas'], start=1):
            with st.container(border=True):
                st.markdown(f'**{posicao}. {lacuna["nome"]}**')
                st.caption(f'Conhecimento informado: {lacuna["nivel_atual"]}/5 · Referência: {lacuna["nivel_requerido"]}/5 · Lacuna: {lacuna["lacuna"]} ponto(s)')
                st.write(lacuna['orientacao'])
                st.write('Tecnologias / temas: ' + ', '.join(lacuna['tecnologias']))
        st.markdown('**Tecnologias e assuntos prioritários**')
        st.write(', '.join(plano['tecnologias_prioritarias']))
        st.markdown('**Próximas ações recomendadas**')
        for passo in plano['proximos_passos']:
            st.write('• ' + passo)
    else:
        st.success('Você já indicou domínio suficiente para todas as competências da meta escolhida. Foque em projetos práticos, revisão e documentação de resultados.')

    projeto = plano['projeto_portfolio']
    st.markdown('**Projeto recomendado para o portfólio GitHub**')
    st.write(f'**{projeto["titulo"]}** — {projeto["descricao"]}')
    for entrega in projeto['entregaveis']:
        st.write('• ' + entrega)
    if plano['lacunas']:
        st.caption('Personalização: utilize o projeto para praticar primeiro as três competências pendentes indicadas no roadmap.')

    st.markdown('**Certificações e formações opcionais**')
    for certificacao in plano['certificacoes_opcionais']:
        st.write('• ' + certificacao)
    st.caption('As certificações são apenas sugestões, não requisitos para contratação. Confirme nomes, validade, pré-requisitos e disponibilidade nos provedores antes de se inscrever.')

    exportacao = {'perfil':{'apelido_opcional':st.session_state.get('perfil_dados',{}).get('apelido',''),
                           'experiencia_autodeclarada':st.session_state.get('perfil_dados',{}).get('experiencia',''),
                           'afinidades':afinidades,'objetivos':objetivos},
                  'metodologia':base['descricao'],'ranking':ranking,'plano':plano}
    st.download_button('Baixar ranking e roadmap em JSON', data=json.dumps(exportacao,ensure_ascii=False,indent=2),
                       file_name='analise_carreiras_ti.json',mime='application/json')


st.title('🧭 Consultor Avançado de Carreiras em TI')
st.caption('Sistema especialista baseado em regras, pontuação ponderada e tratamento de conflitos de perfil.')

rotulos = ['1. Perfil pessoal','2. Afinidades técnicas','3. Objetivos profissionais','4. Resultados e roadmap']
st.progress((st.session_state.etapa+1)/len(rotulos))
st.caption(' → '.join(f'**{item}**' if i == st.session_state.etapa else item for i,item in enumerate(rotulos)))

if st.session_state.etapa == 0:
    st.subheader('Passo 1 — Perfil pessoal')
    st.write('Estas informações servem apenas para contextualizar a recomendação. O apelido é opcional e não altera o ranking.')
    with st.form('form_perfil'):
        st.text_input('Como gostaria de ser chamado? (opcional)',
                      value=st.session_state.get('perfil_dados', {}).get('apelido', ''),
                      key='apelido',max_chars=60)
        situacoes = ['Começando a explorar TI','Estudante de TI','Estudo por conta própria','Em transição de carreira','Já trabalho com tecnologia']
        anterior = st.session_state.get('perfil_dados', {}).get('experiencia', situacoes[0])
        st.selectbox('Qual é sua situação atual?', situacoes, index=situacoes.index(anterior) if anterior in situacoes else 0,
                     key='experiencia')
        proximo = st.form_submit_button('Próximo: afinidades',type='primary')
    if proximo:
        st.session_state['perfil_dados'] = {
            'apelido': st.session_state.get('apelido', ''),
            'experiencia': st.session_state['experiencia']
        }
        ir_para(1)

elif st.session_state.etapa == 1:
    st.subheader('Passo 2 — Afinidades técnicas')
    st.write('Avalie o quanto você gosta de cada tema. Use 1 para pouca afinidade e 5 para muita afinidade. Não é uma prova de conhecimento.')
    with st.form('form_afinidades'):
        colunas = st.columns(2)
        for posicao,(chave,atributo) in enumerate(base['atributos'].items()):
            with colunas[posicao % 2]:
                st.slider(atributo['rotulo'],min_value=1,max_value=5,
                          value=st.session_state.get('respostas_afinidades', {}).get(chave, 3),
                          key=f'afinidade_{chave}',help=atributo['descricao'])
        avancar = st.form_submit_button('Próximo: objetivos profissionais',type='primary')
    if st.button('Voltar ao perfil'):
        ir_para(0)
    if avancar:
        st.session_state['respostas_afinidades'] = {
            chave: int(st.session_state[f'afinidade_{chave}'])
            for chave in base['atributos']
        }
        ir_para(2)

elif st.session_state.etapa == 2:
    st.subheader('Passo 3 — Objetivos profissionais')
    st.write('Escolha até dois objetivos que mais combinam com o que você procura no trabalho.')
    with st.form('form_objetivos'):
        escolhas = st.multiselect('Seus objetivos principais',options=list(base['objetivos'].keys()),
                                  format_func=lambda chave:base['objetivos'][chave],
                                  max_selections=base['parametros']['maximo_objetivos'],
                                  default=st.session_state.get('respostas_objetivos', []),
                                  key='objetivos_usuario')
        avancar = st.form_submit_button('Calcular ranking e abrir roadmap',type='primary')
    if st.button('Voltar às afinidades'):
        ir_para(1)
    if avancar:
        if not escolhas:
            st.warning('Selecione ao menos um objetivo para continuar.')
        else:
            st.session_state['respostas_objetivos'] = list(escolhas)
            ir_para(3)

else:
    if st.button('Editar minhas respostas'):
        ir_para(1)
    if st.button('Começar nova análise'):
        st.session_state.clear()
        st.rerun()
    if (set(st.session_state.get('respostas_afinidades', {})) == set(base['atributos'])
            and st.session_state.get('respostas_objetivos')):
        mostrar_resultados()
    else:
        st.warning('O perfil ainda não está completo. Volte à primeira etapa.')
