@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -m pip install -r requirements.txt
  if errorlevel 1 goto erro
  py -m streamlit run app.py
  goto fim
)
where python >nul 2>nul
if errorlevel 1 goto sempython
python -m pip install -r requirements.txt
if errorlevel 1 goto erro
python -m streamlit run app.py
goto fim
:sempython
echo Python nao encontrado. Instale Python 3.10 ou superior e execute novamente.
goto fim
:erro
echo Ocorreu um erro. Confira a instalacao do Python e a conexao com a internet.
:fim
pause
