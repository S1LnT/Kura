from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
)
from .. import lm
from .. import bc
from flask_login import (
    login_required,
    current_user,
    login_required,
    logout_user,
    LoginManager,
    UserMixin,
    login_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from ..models import User
from .. import logger


auth = Blueprint("auth", __name__)


@lm.user_loader
def load_user(user_id):
    if user_id != None:
        return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        name="username",
        id="login_username",
        render_kw={"placeholder": "Username", "autocomplete": "username"}
    )

    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        name="password",
        id="login_password",
        render_kw={"placeholder": "Password", "autocomplete" : "off"}
    )

    submit = SubmitField("Login")


class GuestForm(FlaskForm):
    submit = SubmitField("Guest")


@auth.route("/auth/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    guestf = GuestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user != None:
            if bc.check_password_hash(user.password, form.password.data):
                user.last_login = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                login_user(user, remember=True)
                logger.info(f"{user.username} logged in")
                return redirect(url_for("home.main"))
            else:
                logger.warning(
                    f"Failed login attempt for {form.username.data}(password mismatch)"
                )
                flash("Credenziali Errate")
                return redirect(url_for("admin.login"), 403, "password mismatch")
        else:
            logger.warning(
                f"Failed login attempt for {form.username.data}(user not found)"
            )
            flash("Utente non trovato")
            return redirect(url_for("admin.login"), 403, "user not found")
    elif guestf.validate_on_submit():
        logger.info("Guest logged in")
        return redirect(url_for("home.main"))
    return render_template("/auth/login.html", form=form, guestf=guestf)


@auth.route("/logout", methods=["GET", "POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for("auth.login"))
    else:
        return redirect(url_for("auth.login"))
