import os
from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

db_path = os.getenv("SQLITE_DB")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# -------------------- MODELS --------------------
from app.models import User, Genero, Artista, Musica, UserGenero, UserArtista


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------- ROTAS --------------------

@app.route("/")
@login_required
def home():
    # Gêneros e artistas favoritos do usuário
    user_generos_ids = [ug.genero_id for ug in current_user.generos]
    user_artistas_ids = [ua.artista_id for ua in current_user.artistas]

    # Recomendação: músicas que combinem com o gosto do usuário
    recomendacoes = Musica.query.filter(
        (Musica.genero_id.in_(user_generos_ids)) |
        (Musica.artista_id.in_(user_artistas_ids))
    ).all()

    return render_template("home.html", recomendacoes=recomendacoes)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.senha, senha):
            login_user(user)
            return redirect("/")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])

        novo_user = User(nome=nome, email=email, senha=senha)
        db.session.add(novo_user)
        db.session.commit()

        login_user(novo_user)
        return redirect("/escolher-gostos")

    return render_template("register.html")


@app.route("/escolher-gostos", methods=["GET", "POST"])
@login_required
def escolher_gostos():
    generos = Genero.query.all()
    artistas = Artista.query.all()

    if request.method == "POST":
        db.session.query(UserGenero).filter_by(usuario_id=current_user.id).delete()
        db.session.query(UserArtista).filter_by(usuario_id=current_user.id).delete()

        for genero_id in request.form.getlist("generos"):
            db.session.add(UserGenero(usuario_id=current_user.id, genero_id=genero_id))

        for artista_id in request.form.getlist("artistas"):
            db.session.add(UserArtista(usuario_id=current_user.id, artista_id=artista_id))

        db.session.commit()
        return redirect("/")

    return render_template("escolher_gostos.html", generos=generos, artistas=artistas)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# -------------------- ADMIN --------------------
def admin_required():
    if not current_user.is_admin:
        return redirect("/")


@app.route("/admin")
@login_required
def admin_dashboard():
    admin_required()

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
    return redirect("/admin")


@app.route("/admin/generos/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_genero(id):
    admin_required()
    g = Genero.query.get(id)
    if request.method == "POST":
        g.nome = request.form["nome"]
        db.session.commit()
        return redirect("/admin")
    return render_template("edit.html", tipo="Gênero", item=g)


@app.route("/admin/generos/delete/<int:id>")
@login_required
def admin_del_genero(id):
    admin_required()
    db.session.delete(Genero.query.get(id))
    db.session.commit()
    return redirect("/admin")


# ARTISTAS
@app.route("/admin/artistas", methods=["POST"])
@login_required
def admin_add_artista():
    admin_required()
    db.session.add(Artista(nome=request.form["nome"]))
    db.session.commit()
    return redirect("/admin")


@app.route("/admin/artistas/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_artista(id):
    admin_required()
    a = Artista.query.get(id)
    if request.method == "POST":
        a.nome = request.form["nome"]
        db.session.commit()
        return redirect("/admin")
    return render_template("edit.html", tipo="Artista", item=a)


@app.route("/admin/artistas/delete/<int:id>")
@login_required
def admin_del_artista(id):
    admin_required()
    db.session.delete(Artista.query.get(id))
    db.session.commit()
    return redirect("/admin")


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
    return redirect("/admin")


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
        return redirect("/admin")

    return render_template("edit_musica.html", musica=m, generos=generos, artistas=artistas)


@app.route("/admin/musicas/delete/<int:id>")
@login_required
def admin_del_musica(id):
    admin_required()
    db.session.delete(Musica.query.get(id))
    db.session.commit()
    return redirect("/admin")
