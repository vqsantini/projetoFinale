*** Settings ***
Documentation     Teste de Login com tratamento de sessão
Library           SeleniumLibrary    run_on_failure=None

# Fecha o navegador automaticamente ao final de cada teste
Test Teardown     Close Browser

*** Variables ***
${URL_BASE}       http://127.0.0.1:5000/login
${BROWSER}        Chrome

# Credenciais
${EMAIL_CORRETO}  teste@gmail.com
${SENHA_CORRETA}  teste123
${SENHA_ERRADA}   senha_errada

*** Test Cases ***

Cenario 1: Login Com Sucesso
    [Documentation]    Garante que estamos deslogados, loga e valida o acesso.
    Preparar Navegador E Garantir Logout
    
    Preencher Login    ${EMAIL_CORRETO}    ${SENHA_CORRETA}
    Clicar Em Entrar
    
    Validar Login Com Sucesso

Cenario 2: Login Com Senha Incorreta
    [Documentation]    Tenta logar com senha errada e valida mensagem.
    Preparar Navegador E Garantir Logout
    
    Preencher Login    ${EMAIL_CORRETO}    ${SENHA_ERRADA}
    Clicar Em Entrar
    
    Validar Mensagem De Erro

*** Keywords ***

Preparar Navegador E Garantir Logout
    # Abre o navegador limpo
    Open Browser    ${URL_BASE}    ${BROWSER}
    Maximize Browser Window
    
    # 1. Verifica se já estamos logados
    ${esta_logado} =    Run Keyword And Return Status    Wait Until Page Contains    Sair    timeout=2s
    
    # 2. Se estiver logado, faz o logout
    Run Keyword If    ${esta_logado}    Fazer Logout
    
    # 3. Garante que o campo de email está visível
    Wait Until Element Is Visible    id:email    timeout=10s    error=O campo de email não apareceu.

Fazer Logout
    Log    O usuário já estava logado. Realizando logout...
    Click Link    Sair
    Wait Until Element Is Visible    id:email    timeout=5s

Preencher Login
    [Arguments]    ${email}    ${senha}
    Input Text      id:email    ${email}
    Input Text      id:senha    ${senha}

Clicar Em Entrar
    Wait Until Element Is Enabled    id:submit    timeout=5s
    Click Element    id:submit

Validar Login Com Sucesso
    Wait Until Page Contains    Olá, teste!    timeout=10s

Validar Mensagem De Erro
    Wait Until Page Contains    Login inválido    timeout=5s