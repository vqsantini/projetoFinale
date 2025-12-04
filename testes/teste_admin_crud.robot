*** Settings ***
Documentation     Teste CRUD Admin com Bypass de CSRF.
Library           RequestsLibrary
Library           DatabaseLibrary
Library           Collections
Library           String

Suite Setup       Preparar Ambiente De Teste
Suite Teardown    Limpar Ambiente De Teste

*** Variables ***
${URL_BASE}       http://127.0.0.1:5000
${DB_PATH}        ./instance/musics.db
${DB_MODULE}      sqlite3

# Dados para o teste
${EMAIL_ADMIN}    admin_robot@gmail.com
${SENHA_ADMIN}    123456
${NOME_ADMIN}     Robot Admin

*** Test Cases ***

Cenario 1: Autenticar Como Admin (Com Token CSRF)
    [Documentation]    Pega o token da página e faz login.
    Criar Sessao Web
    
    # 1. Acessa a página de login via GET para pegar o Token
    ${resp_get}    GET On Session    alias=flask_app    url=/login
    
    # 2. Extrai o token escondido no HTML
    ${csrf_token}  Obter Token CSRF    ${resp_get.text}
    Log    Token encontrado: ${csrf_token}
    
    # 3. Faz o Login enviando o token junto
    ${data}    Create Dictionary    email=${EMAIL_ADMIN}    senha=${SENHA_ADMIN}    csrf_token=${csrf_token}
    ${resp_post}    POST On Session    alias=flask_app    url=/login    data=${data}    expected_status=200
    
    # 4. Verifica se logou (procura texto da Home Logada)
    # Nota: O Flask pode redirecionar para 'home' ou 'escolher-gostos'
    Should Contain    ${resp_post.text}    Olá, Robot Admin

Cenario 2: Criar Musica (POST)
    [Documentation]    Cria uma música. (Se houver erro 400/500, pode ser falta de CSRF aqui também)
    
    # Prepara os dados
    ${generos}    Create List    ${GENERO_ID}
    ${dados_form}    Create Dictionary    titulo=Musica Robot Teste    artista_id=${ARTISTA_ID}    genero_ids=${generos}
    
    # Tenta enviar o POST. Se suas rotas manuais (/admin/musicas) não usam FlaskForm, 
    # talvez não precisem de token. Se falhar, precisaremos pegar o token da dashboard.
    ${resp}    POST On Session    alias=flask_app    url=/admin/musicas    data=${dados_form}    expected_status=200
    
    # Valida sucesso
    Should Contain    ${resp.text}    Musica Robot Teste

    # Recupera ID
    ${resultado}    Query    SELECT id FROM musica WHERE titulo = 'Musica Robot Teste';
    ${id_musica}    Set Variable    ${resultado}[0][0]
    Set Suite Variable    ${ID_MUSICA_CRIADA}    ${id_musica}

Cenario 3: Ler/Verificar Musica (GET)
    [Documentation]    Verifica dashboard.
    ${resp}    GET On Session    alias=flask_app    url=/admin    expected_status=200
    Should Contain    ${resp.text}    Musica Robot Teste

Cenario 4: Atualizar Musica (POST)
    [Documentation]    Edita a música.
    ${generos}    Create List    ${GENERO_ID}
    ${dados_edit}    Create Dictionary    titulo=Musica Editada Robot    artista_id=${ARTISTA_ID}    genero_ids=${generos}
    
    ${resp}    POST On Session    alias=flask_app    url=/admin/musicas/edit/${ID_MUSICA_CRIADA}    data=${dados_edit}    expected_status=200
    
    Should Contain    ${resp.text}    Musica Editada Robot

Cenario 5: Deletar Musica (GET)
    [Documentation]    Deleta a música.
    ${resp}    GET On Session    alias=flask_app    url=/admin/musicas/delete/${ID_MUSICA_CRIADA}    expected_status=200
    Should Not Contain    ${resp.text}    Musica Editada Robot

*** Keywords ***

Obter Token CSRF
    [Arguments]    ${html_content}
    # Procura no HTML por: name="csrf_token" ... value="TOKEN_AQUI"
    # O Regex abaixo captura o valor do atributo value dentro do input do csrf_token
    ${matches}    Get Regexp Matches    ${html_content}    name="csrf_token" type="hidden" value="(.+?)"    1
    
    # Se não achar do jeito padrão, tenta procurar só por value="..." perto do name="csrf_token"
    ${token}      Set Variable    ${matches}[0]
    RETURN        ${token}

Preparar Ambiente De Teste
    # Atualizei para a Keyword correta (sem o warning de Deprecated)
    Connect To Database    ${DB_MODULE}    ${DB_PATH}
    
    Execute Sql String    INSERT INTO genero (nome) VALUES ('Robot Rock');
    ${res_gen}    Query    SELECT id FROM genero WHERE nome = 'Robot Rock';
    Set Suite Variable    ${GENERO_ID}    ${res_gen}[0][0]
    
    Execute Sql String    INSERT INTO artista (nome) VALUES ('Daft Punk Robot');
    ${res_art}    Query    SELECT id FROM artista WHERE nome = 'Daft Punk Robot';
    Set Suite Variable    ${ARTISTA_ID}    ${res_art}[0][0]
    
    # Cria Admin via SQL direto (já com hash simulado ou login via requests)
    # DICA: Para evitar complexidade de Hash de senha no teste, vamos criar via Rota de Registro
    # Mas precisamos do CSRF token para registrar também! 
    # Vamos simplificar: INSERIR direto no banco um usuário e assumir que a senha bate se criarmos o hash manualmente?
    # Melhor: Vamos usar a rota de registro mas pegando o token antes.
    
    Criar Sessao Web
    ${resp_reg}    GET On Session    alias=flask_app    url=/register
    ${token_reg}   Obter Token CSRF    ${resp_reg.text}
    
    ${dados_reg}    Create Dictionary    nome=${NOME_ADMIN}    email=${EMAIL_ADMIN}    senha=${SENHA_ADMIN}    csrf_token=${token_reg}
    POST On Session    alias=flask_app    url=/register    data=${dados_reg}
    
    # Transforma em Admin
    Execute Sql String    UPDATE user SET is_admin = 1 WHERE email = '${EMAIL_ADMIN}';

Limpar Ambiente De Teste
    Execute Sql String    DELETE FROM musica WHERE titulo LIKE '%Robot%';
    Execute Sql String    DELETE FROM genero WHERE id = ${GENERO_ID};
    Execute Sql String    DELETE FROM artista WHERE id = ${ARTISTA_ID};
    Execute Sql String    DELETE FROM user WHERE email = '${EMAIL_ADMIN}';
    Disconnect From Database

Criar Sessao Web
    Create Session    alias=flask_app    url=${URL_BASE}