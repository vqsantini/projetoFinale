import os
from app import app, db, login_manager, bcrypt
from flask import render_template, redirect, request, session, flash, url_for
from flask_login import login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from app.models import User, Genero, Artista, Musica, UserGenero, UserArtista
from app.forms import LoginForm, RegisterForm 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Rotas Principais e de Autenticação ---

@app.route("/")
def home():
    """
    Página principal. Mostra a landing page para usuários deslogados
    e a página de recomendações para usuários logados.
    """
    if current_user.is_authenticated:
        # Lógica de recomendações (se estiver logado)
        user_generos_ids = [ug.genero_id for ug in current_user.generos]
        user_artistas_ids = [ua.artista_id for ua in current_user.artistas]

        recomendacoes = Musica.query.filter(
            (Musica.genero_id.in_(user_generos_ids)) |
            (Musica.artista_id.in_(user_artistas_ids))
        ).all()
        
        return render_template("home.html", recomendacoes=recomendacoes)
    
    else:
        # Apenas renderiza o 'else' do home.html (landing page)
        return render_template("home.html")

@app.route("/sobre")
def sobre():
    """Página 'Sobre'."""
    return render_template("sobre.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = LoginForm() 
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and bcrypt.check_password_hash(user.senha, form.senha.data):
            login_user(user)
            # Redireciona para a página de 'escolher_gostos' se for o primeiro login (sem gostos)
            if not user.generos and not user.artistas:
                 flash('Login com sucesso! Personalize seus gostos.', 'success')
                 return redirect(url_for('escolher_gostos'))
            return redirect(url_for('home'))
        else:
            flash('Login inválido. Verifique e-mail e senha.', 'danger') 

    return render_template("login.html", form=form) 


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegisterForm() 
    if form.validate_on_submit():
        hashed_senha = bcrypt.generate_password_hash(form.senha.data).decode('utf-8')
        
        novo_user = User(nome=form.nome.data, email=form.email.data, senha=hashed_senha)
        db.session.add(novo_user)
        db.session.commit()

        login_user(novo_user) 
        flash('Conta criada com sucesso! Agora, personalize seus gostos.', 'success')
        return redirect(url_for('escolher_gostos')) 

    return render_template("register.html", form=form) 


@app.route("/escolher-gostos", methods=["GET", "POST"])
@login_required
def escolher_gostos():
    generos = Genero.query.all()
    artistas = Artista.query.all()

    if request.method == "POST":
        # Limpa gostos antigos
        db.session.query(UserGenero).filter_by(usuario_id=current_user.id).delete()
        db.session.query(UserArtista).filter_by(usuario_id=current_user.id).delete()

        for genero_id in request.form.getlist("generos"):
            db.session.add(UserGenero(usuario_id=current_user.id, genero_id=genero_id))

        for artista_id in request.form.getlist("artistas"):
            db.session.add(UserArtista(usuario_id=current_user.id, artista_id=artista_id))

        db.session.commit()
        flash('Preferências salvas! Aproveite suas recomendações.', 'success')
        return redirect(url_for('home')) 

    return render_template("escolher_gostos.html", generos=generos, artistas=artistas)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home')) # Redireciona para a landing page


# -------------------- ADMIN --------------------
def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('home'))

@app.route("/admin")
@login_required
def admin_dashboard():
    admin_required() # Chama a função de verificação
    generos = Genero.query.all()
    artistas = Artista.query.all()
    musicas = Musica.query.all()
    return render_template("admin_dashboard.html", generos=generos, artistas=artistas, musicas=musicas)


# GÊNEROS
@app.route("/admin/generos", methods=["POST"])
@login_required
def admin_add_genero():
    admin_required()
    db.session.add(Genero(nome=request.form["nome"]))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route("/admin/generos/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_genero(id):
    admin_required()
    g = Genero.query.get(id)
    if request.method == "POST":
        g.nome = request.form["nome"]
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template("edit.html", tipo="Gênero", item=g)


@app.route("/admin/generos/delete/<int:id>")
@login_required
def admin_del_genero(id):
    admin_required()
    db.session.delete(Genero.query.get(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# ARTISTAS
@app.route("/admin/artistas", methods=["POST"])
@login_required
def admin_add_artista():
    admin_required()
    db.session.add(Artista(nome=request.form["nome"]))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route("/admin/artistas/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_artista(id):
    admin_required()
    a = Artista.query.get(id)
    if request.method == "POST":
        a.nome = request.form["nome"]
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template("edit.html", tipo="Artista", item=a)


@app.route("/admin/artistas/delete/<int:id>")
@login_required
def admin_del_artista(id):
    admin_required()
    db.session.delete(Artista.query.get(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# MÚSICAS
@app.route("/admin/musicas", methods=["POST"])
@login_required
def admin_add_musica():
    admin_required()
    nova = Musica(
        titulo=request.form["titulo"],
        artista_id=request.form["artista_id"],
        genero_id=request.form["genero_id"]
    )
    db.session.add(nova)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route("/admin/musicas/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_musica(id):
    admin_required()
    m = Musica.query.get(id)
    generos = Genero.query.all()
    artistas = Artista.query.all()

    if request.method == "POST":
        m.titulo = request.form["titulo"]
        m.artista_id = request.form["artista_id"]
        m.genero_id = request.form["genero_id"]
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template("edit_musica.html", musica=m, generos=generos, artistas=artistas)


@app.route("/admin/musicas/delete/<int:id>")
@login_required
def admin_del_musica(id):
    admin_required()
    db.session.delete(Musica.query.get(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))