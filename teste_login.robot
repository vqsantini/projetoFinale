*** Settings ***
Documentation     Teste de Login com tratamento de sessão e Screenshots de erro.
Library           SeleniumLibrary
Library           OperatingSystem

# Garante que, se algo der errado, ele tira um print antes de fechar
Test Teardown     Finalizar Teste Com Debug

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
    # Abre o navegador limpo (sem configurações complexas por enquanto)
    Open Browser    ${URL_BASE}    ${BROWSER}
    Maximize Browser Window
    
    # 1. Verifica se já estamos logados (Procura pelo botão 'Sair' ou texto de boas vindas)
    # O timeout curto (2s) é para não perder tempo se não estiver logado
    ${esta_logado} =    Run Keyword And Return Status    Wait Until Page Contains    Sair    timeout=2s
    
    # 2. Se estiver logado, faz o logout antes de começar o teste
    Run Keyword If    ${esta_logado}    Fazer Logout
    
    # 3. Agora garante que o campo de email está visível
    Wait Until Element Is Visible    id:email    timeout=10s    error=O campo de email não apareceu. Verifique o print na pasta de logs.

Fazer Logout
    Log    O usuário já estava logado. Realizando logout...
    Click Link    Sair
    # Espera voltar para a tela de login
    Wait Until Element Is Visible    id:email    timeout=5s

Preencher Login
    [Arguments]    ${email}    ${senha}
    Input Text      id:email    ${email}
    Input Text      id:senha    ${senha}

Clicar Em Entrar
    Wait Until Element Is Enabled    id:submit    timeout=5s
    Click Element    id:submit

Validar Login Com Sucesso
    # Valida pelo texto que vimos no seu print
    Wait Until Page Contains    Olá, teste!    timeout=10s

Validar Mensagem De Erro
    # Valida a mensagem flash do Flask
    Wait Until Page Contains    Login inválido    timeout=5s

Finalizar Teste Com Debug
    # Se o teste falhou, tira um print da tela
    Run Keyword If Test Failed    Capture Page Screenshot    filename=erro_login_{index}.png
    Close Browser