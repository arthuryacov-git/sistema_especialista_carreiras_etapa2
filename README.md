# Consultor Avançado de Carreiras em TI

Sistema especialista desenvolvido em Python para a **2ª etapa da disciplina de Inteligência Artificial** do curso de Ciência da Computação da **UNIPAC Barbacena**.

A aplicação analisa afinidades técnicas e objetivos profissionais, compara dez trilhas de carreira em tecnologia e propõe um plano individualizado de desenvolvimento de competências.

## Funcionalidades

- Entrevista interativa em quatro etapas: perfil pessoal, afinidades técnicas, objetivos profissionais e resultados.
- Avaliação gradual de afinidades em uma escala de **1 a 5**.
- Motor de inferência próprio baseado em **pontuação ponderada**, objetivos profissionais e penalidades por conflitos de perfil.
- **Ranking das dez carreiras**, com destaque para as três mais compatíveis e seus percentuais de aderência.
- Gráfico de barras e justificativas das principais recomendações.
- Autoavaliação de competências de **0 a 5** para a trilha escolhida.
- Identificação de lacunas de conhecimento (*skill gaps*) e comparação com referências de estudo para Júnior, Pleno e Sênior.
- **Roadmap personalizado**, com prioridades de estudo, tecnologias, sugestões de certificações e projeto para portfólio no GitHub.
- Exportação do ranking e do plano de desenvolvimento em JSON.

## Trilhas de carreira

1. Desenvolvimento Back-end
2. Desenvolvimento Front-end/UX
3. Ciência de Dados
4. Engenharia de Dados
5. Cibersegurança
6. DevOps/SRE
7. Cloud Architecture
8. Desenvolvimento Mobile
9. Qualidade e Testes (QA)
10. Product Management

## Tecnologias

- **Python 3.10 ou superior**
- **Streamlit** — interface web interativa
- **Pandas** — organização e apresentação dos resultados
- **JSON** — armazenamento externo da base de conhecimento
- **unittest** — testes automatizados
- **Git e GitHub** — versionamento do código

## Estrutura do projeto

```text
sistema_especialista_carreiras_etapa2/
├── app.py                       # Interface web e fluxo da entrevista
├── motor_inferencia.py          # Cálculo do ranking, gaps e roadmap
├── regras_carreiras.json        # Regras, pesos, trilhas e competências
├── requirements.txt             # Dependências do projeto
├── iniciar_windows.bat          # Inicialização facilitada no Windows
├── testar_windows.bat           # Execução dos testes no Windows
├── RESULTADOS_DOS_TESTES.txt    # Registro da validação automatizada
└── tests/
    ├── test_motor.py
    └── test_interface_fluxo.py
```

## Como executar

**Pré-requisito:** Python 3.10 ou superior instalado.

No terminal do VSCode, dentro da pasta do projeto, instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Inicie a aplicação:

```powershell
python -m streamlit run app.py
```

O Streamlit normalmente disponibiliza a interface em **http://localhost:8501**.

**Alternativa no Windows:** execute o arquivo `iniciar_windows.bat` para instalar as dependências e iniciar o sistema.

## Como utilizar

1. Informe sua situação atual na área de tecnologia.
2. Avalie suas afinidades com temas técnicos, de 1 a 5.
3. Selecione seus principais objetivos profissionais.
4. Consulte o **Top 3** e a comparação entre as dez carreiras.
5. Escolha uma trilha e o nível de referência (Júnior, Pleno ou Sênior).
6. Avalie seu conhecimento em cada competência e clique em **Gerar / atualizar roadmap**.
7. Consulte as lacunas, a ordem recomendada de estudo e o projeto de portfólio sugerido. Se desejar, baixe os resultados em JSON.

## Como o sistema calcula a compatibilidade

O motor lê as configurações do arquivo `regras_carreiras.json`, sem manter os pesos e as regras de carreira fixos no código Python.

Cada trilha recebe uma pontuação baseada em:

- **Afinidades:** média normalizada das respostas, considerando os pesos definidos para cada carreira, com contribuição de até 90 pontos.
- **Objetivos profissionais:** bônus de até 10 pontos quando correspondem às características da trilha.
- **Conflitos de perfil:** penalidades previstas nas regras da base de conhecimento.

A pontuação final é limitada à faixa de **0% a 100%**. Os percentuais representam aderência estimada às regras utilizadas, **não** probabilidade de sucesso profissional, diagnóstico psicológico ou garantia de contratação.

A análise de competências compara a autoavaliação do usuário com os níveis de referência definidos para a trilha e organiza o plano de estudo conforme as lacunas identificadas.

## Testes

Para executar os testes automatizados:

```powershell
python -m unittest discover -s tests -v
```

No Windows, também é possível executar `testar_windows.bat`.

O projeto inclui testes de ranking, pesos, penalidades, perfis extremos, empates e fluxo da interface até a geração do roadmap. O arquivo `RESULTADOS_DOS_TESTES.txt` registra a validação automatizada da versão entregue.

## Observações

- As recomendações são orientativas e dependem das respostas e das regras configuradas.
- As classificações Júnior, Pleno e Sênior são **referências de estudo**, não comprovação de experiência profissional.
- Certificações e formações são sugestões opcionais; disponibilidade e requisitos devem ser verificados nos respectivos fornecedores.

## Informações acadêmicas

- **Instituição:** Centro Universitário Presidente Antônio Carlos — UNIPAC Barbacena
- **Curso:** Ciência da Computação
- **Disciplina:** Inteligência Artificial
- **Atividade:** Trabalho da 2ª Etapa — Sistema Especialista Inteligente para Mapeamento, Compatibilidade e Trilha de Carreira em TI
- **Aluno:** Arthur Yacov Claudino Silvano e Silva

## Repositório

https://github.com/arthuryacov-git/sistema_especialista_carreiras_etapa2
