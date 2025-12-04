import os
from app import app, db, login_manager, bcrypt
from flask import render_template, redirect, request, session, flash, url_for, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from app.models import User, Genero, Artista, Musica, UserGenero, UserArtista
from app.forms import LoginForm, RegisterForm 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    if current_user.is_authenticated:
        user_generos_ids = [ug.genero_id for ug in current_user.generos]
        user_artistas_ids = [ua.artista_id for ua in current_user.artistas]
        recomendacoes = Musica.query.filter(
            Musica.generos.any(Genero.id.in_(user_generos_ids)) |
            (Musica.artista_id.in_(user_artistas_ids))
        ).all()
        
        return render_template("home.html", recomendacoes=recomendacoes)
    
    else:
        return render_template("home.html")
@app.route("/sobre")
def sobre():
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
            if not user.generos and not user.artistas:
                 flash('Login com sucesso! Por favor, personalize seus gostos.', 'success')
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
        is_admin_user = False
        if form.email.data.lower() == 'admin@gmail.com':
            is_admin_user = True
            
        novo_user = User(
            nome=form.nome.data, 
            email=form.email.data, 
            senha=hashed_senha,
            is_admin=is_admin_user
        )
        
        db.session.add(novo_user)
        db.session.commit()
        login_user(novo_user) 
        if is_admin_user:
            flash('Conta de Administrador criada com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Conta criada com sucesso! Agora, personalize seus gostos.', 'success')
            return redirect(url_for('escolher_gostos')) 
    return render_template("register.html", form=form) 

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/api/artistas/search")
@login_required
def api_search_artistas():
    query = request.args.get('q', '').strip()
    
    if query:
        artistas = Artista.query.filter(
            Artista.nome.ilike(f'%{query}%')
        ).limit(10).all()
        return jsonify([artista.nome for artista in artistas])
        
    else:
        artistas = Artista.query.order_by(Artista.nome).all()
        return jsonify([artista.nome for artista in artistas])

@app.route("/escolher-gostos", methods=["GET", "POST"])
@login_required
def escolher_gostos():
    generos = Genero.query.all() 
    if request.method == "POST":
        db.session.query(UserGenero).filter_by(usuario_id=current_user.id).delete()
        db.session.query(UserArtista).filter_by(usuario_id=current_user.id).delete()
        generos_selecionados = request.form.getlist("generos")
        for genero_id in generos_selecionados:
            db.session.add(UserGenero(usuario_id=current_user.id, genero_id=genero_id))
        artistas_string = request.form.get("artistas", "")
        nomes_artistas = [nome.strip() for nome in artistas_string.split(',') if nome.strip()]
        for nome in nomes_artistas:
            artista = Artista.query.filter(db.func.lower(Artista.nome) == nome.lower()).first()
            if not artista:
                artista = Artista(nome=nome)
                db.session.add(artista)
                db.session.flush() 
            db.session.add(UserArtista(usuario_id=current_user.id, artista_id=artista.id))
        db.session.commit()
        flash('Preferências salvas! Aproveite suas recomendações.', 'success')
        return redirect(url_for('home')) 
    generos_selecionados_ids = [ug.genero_id for ug in current_user.generos]
    artistas_selecionados = ", ".join([ua.artista.nome for ua in current_user.artistas])

    return render_template(
        "escolher_gostos.html", 
        generos=generos,
        generos_selecionados_ids=generos_selecionados_ids,
        artistas_selecionados=artistas_selecionados
    )

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        db.session.query(UserGenero).filter_by(usuario_id=current_user.id).delete()
        db.session.query(UserArtista).filter_by(usuario_id=current_user.id).delete()
        generos_selecionados = request.form.getlist("generos")
        for genero_id in generos_selecionados:
            db.session.add(UserGenero(usuario_id=current_user.id, genero_id=genero_id))
        artistas_string = request.form.get("artistas", "")
        nomes_artistas = [nome.strip() for nome in artistas_string.split(',') if nome.strip()]
        for nome in nomes_artistas:
            artista = Artista.query.filter(db.func.lower(Artista.nome) == nome.lower()).first()
            if not artista:
                artista = Artista(nome=nome)
                db.session.add(artista)
                db.session.flush()
            db.session.add(UserArtista(usuario_id=current_user.id, artista_id=artista.id))
        db.session.commit()
        flash('Preferências atualizadas com sucesso!', 'success')
        return redirect(url_for('perfil'))
    generos = Genero.query.all()
    generos_selecionados_ids = [ug.genero_id for ug in current_user.generos]
    artistas_selecionados = ", ".join([ua.artista.nome for ua in current_user.artistas])

    return render_template(
        "perfil.html", 
        generos=generos,
        generos_selecionados_ids=generos_selecionados_ids,
        artistas_selecionados=artistas_selecionados
    )

@app.route("/perfil/excluir", methods=["POST"])
@login_required
def excluir_conta():
    db.session.query(UserGenero).filter_by(usuario_id=current_user.id).delete()
    db.session.query(UserArtista).filter_by(usuario_id=current_user.id).delete()
    user = User.query.get(current_user.id)
    db.session.delete(user)
    db.session.commit()
    flash('Sua conta foi excluída permanentemente.', 'success')
    return redirect(url_for('home'))

# -------------------- ADMIN --------------------
def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Acesso negado. Você precisa ser um administrador.', 'danger')
        return redirect(url_for('home'))

@app.route("/admin")
@login_required
def admin_dashboard():
    admin_required() 
    
    generos = Genero.query.all()
    artistas = Artista.query.all()
    musicas = Musica.query.all()
    return render_template("admin_dashboard.html", generos=generos, artistas=artistas, musicas=musicas)

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

@app.route("/admin/musicas", methods=["POST"])
@login_required
def admin_add_musica():
    admin_required()
    genero_ids = request.form.getlist("genero_ids")
    generos = Genero.query.filter(Genero.id.in_(genero_ids)).all()
    
    nova = Musica(
        titulo=request.form["titulo"],
        artista_id=request.form["artista_id"]
    )
    nova.generos.extend(generos)
    
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
        genero_ids = request.form.getlist("genero_ids")
        generos_selecionados = Genero.query.filter(Genero.id.in_(genero_ids)).all()
        
        m.generos.clear()
        m.generos.extend(generos_selecionados)
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    generos_selecionados_ids = [g.id for g in m.generos]

    return render_template(
        "edit_musica.html", 
        musica=m, 
        generos=generos, 
        artistas=artistas,
        generos_selecionados_ids=generos_selecionados_ids
    )


@app.route("/admin/musicas/delete/<int:id>")
@login_required
def admin_del_musica(id):
    admin_required()
    db.session.delete(Musica.query.get(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))