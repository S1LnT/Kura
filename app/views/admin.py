from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
)
from .. import db
from .. import bc
from .. import appConfig
from flask_wtf import FlaskForm
from flask_login import current_user, login_required
from wtforms import StringField, PasswordField, SubmitField, RadioField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError
from ..models import User, updateData, Post
from .. import socketio
import threading
import psutil
import os
from time import sleep
import shutil
import subprocess
from .. import logger

hdd = psutil.disk_usage(appConfig.UPLOAD_FOLDER)
admin = Blueprint("admin", __name__)

thread = None
thread_lock = threading.Lock()


def get_col(table, attribute):
    try:
        # Dynamically access the column
        column = getattr(table, attribute)

        # Query the specified column
        result = db.session.query(column).all()
        result = [item[0] for item in result]
        return result
    except AttributeError:
        return []


class RegisterForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        name="username",
        id="floatingUsername",
        render_kw={"placeholder": "username"},
    )

    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        name="password",
        id="floatingPassword",
        render_kw={"placeholder": "password"},
    )
    perm = RadioField(
        validators=[InputRequired()],
        name="Perm",
        choices=[("1", "Users"), ("999", "Admin")],
    )

    submit = SubmitField("Create")


class EditForm(FlaskForm):
    title = StringField(
        validators=[InputRequired(), Length(min=1, max=1000)],
        name="title",
        id="floatingTitle",
        render_kw={"placeholder": "Title"},
    )
    desc = TextAreaField(
        validators=[InputRequired(), Length(min=1, max=5000)],
        name="Desc",
        id="floatingDesc",
        render_kw={"placeholder": "Description", "style": "resize: none;"},
    )
    file = StringField(name="File", id="floatingDesc", render_kw={"disabled": ""})
    perm = RadioField(
        validators=[InputRequired()],
        name="Perm",
        choices=[("0", "Guests"), ("1", "Users"), ("999", "Admin")],
    )

    def validate_username(self, username):
        exist_username = User.query.filter_by(username=username.data).first()
        if exist_username != None:
            raise ValidationError("username exist")


def updateOvData():
    while True:
        try:
            cpu = subprocess.check_output(
                ["cat", "/sys/class/thermal/thermal_zone1/temp"]
            ).decode("utf-8")
            temp = int(cpu) / 1000
        except Exception as e:
            logger.error(f"there was an error while getting cpu temp{e}")
            temp = "Error"
        try:
            total = round((hdd.total / (2**30)), 2)
            used = round((hdd.used / (2**30)), 2)
            free = round((hdd.free / (2**30)), 2)
        except Exception as e:
            logger.error(f"there was an error while getting disk information{e}")
            total, used, free = "Error"
        data = {"totalhdd": total, "usedhdd": used, "freehdd": free, "temp": temp}
        socketio.emit("update", data)
        sleep(0.5)


@login_required
@admin.route("/admin/wipe") 
def wipe():
    if current_user.permissions == "999":
        try:
            num_rows_deleted = db.session.query(Post).delete()
            logger.info(f"Wiped DB ({num_rows_deleted} rows deleted)")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error wiping DB({e}) rollbacked")
        try:
            for filename in os.listdir(appConfig.UPLOAD_FOLDER):
                file_path = os.path.join(appConfig.UPLOAD_FOLDER, filename)

                try:
                    # If it's a file or symlink, delete it
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # Unlink removes the file
                    # If it's a directory, delete the directory and its contents
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    logger.info(f"Deleted HDD files ({file_path})")
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error deleting {file_path}: {e}")
            return redirect(url_for("admin.main"))
        except Exception as e:
            db.session.rollback()
            logger.error()
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")


@admin.route("/admin/flushtmp")
@login_required
def flush_temp():
    if current_user.permissions == "999":
        
        for filename in os.listdir(appConfig.TEMP_FOLDER):
            file_path = os.path.join(appConfig.TEMP_FOLDER, filename)

            try:
                # If it's a file or symlink, delete it
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Unlink removes the file
                # If it's a directory, delete the directory and its contents
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        return redirect(url_for("admin.main"))
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@admin.route("/admin/create", methods=["GET", "POST"])
def create_user():
    form = RegisterForm()
    if current_user.permissions == "999":
        if form.validate_on_submit():
            hashed_password = bc.generate_password_hash(form.password.data)
            new_user = User(
                username=form.username.data,
                password=hashed_password,
                last_login="N/A",
                permissions=form.perm.data,
            )
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Created User {form.username.data}")
        else:
            logger.error(f"User not created")
            flash("Utente non creato")
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")
    return render_template("/admin/user/create_user.html", form=form)


@login_required
@admin.route("/admin")
def main():
    if current_user.permissions == "999":
        global thread
        if thread is None:
            thread = threading.Thread(target=updateOvData, daemon=True)
            thread.start()
        return render_template("/admin/admin_main.html", version=appConfig.APP_VERSION)
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@admin.route("/admin/posts", methods=["GET", "POST"])
def admin_posts():
    if current_user.permissions == "999":

        post_ids = get_col(Post, "id")
        post_title = get_col(Post, "title")
        post_desc = get_col(Post, "desc")
        post_filename = get_col(Post, "file_name")
        post_filetype = get_col(Post, "file_type")
        post_path = get_col(Post, "file_loc")
        post_date = get_col(Post, "date_created")
        post_perm = get_col(Post, "lowest_view_permission")

        return render_template(
            "/admin/post/dashboard.html",
            post_ids=post_ids,
            post_title=post_title,
            post_desc=post_desc,
            post_filename=post_filename,
            post_filetype=post_filetype,
            post_path=post_path,
            post_date=post_date,
            post_perm=post_perm,
        )
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@admin.route("/admin/users", methods=["GET", "POST"])
def admin_users():
    if current_user.permissions == "999":
        user_ids = get_col(User, "id")
        user_name = get_col(User, "username")
        user_date = get_col(User, "date_created")
        user_login = get_col(User, "last_login")
        user_perm = get_col(User, "permissions")

        return render_template(
            "/admin/user/dashboard.html",
            user_ids=user_ids,
            user_name=user_name,
            user_date=user_date,
            user_login=user_login,
            user_perm=user_perm,
        )
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@admin.route("/admin/post/modifica/<id>", methods=["GET", "POST"])
def modifica_post(id):
    form = EditForm()
    ftype = None
    if current_user.permissions == "999":
        post = Post.query.filter(Post.id == id).with_for_update().one()
        if post != None:
            if form.validate_on_submit():
                if ftype == "file":
                    post.title = form.title.data
                    post.desc = form.desc.data
                    post.lowest_view_permission = form.perm.data
                else:
                    post.title = form.title.data
                    post.desc = form.desc.data
                    post.lowest_view_permission = form.perm.data
                try:
                    db.session.commit()
                    logger.info(f"Post({post.id}) {post.title} modified")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error modifying Post({post.id}) {post.title}: {e}")
            if post.file_type == "text":
                form.title.data = post.title
                form.desc.data = post.desc
                ftype = "text"
            else:
                form.title.data = post.title
                form.desc.data = post.desc
                form.file.data = post.file_name
                ftype = "file"

        return render_template("/admin/post/edit.html", ftype=ftype, form=form)
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@admin.route("/admin/post/elimina/<id>", methods=["GET", "POST"])
def elimina_post(id):
    if current_user.permissions == "999":
        post = Post.query.filter(Post.id == id).one()
        if post != None:
            if post.file_type == "text":
                try:
                    db.session.delete(post)
                    db.session.commit()
                    logger.info(f"Post({post.id}) {post.title} deleted")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error deleting Post({post.id}) {post.title}: {e}")
            else:
                file_path = post.file_loc
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    db.session.delete(post)
                    db.session.commit()
                    logger.info(f"Post({post.id}) {post.title} deleted")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error deleting Post({post.id}) {post.title}: {e}")

        return redirect(url_for("admin.admin_posts"))
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@admin.route("/admin/user/elimina/<id>", methods=["GET", "POST"])
def elimina_user(id):
    if current_user.permissions == "999":
        try:
            user = User.query.filter(User.id == id).one()
            if user != None:
                db.session.delete(user)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting User({user.id}) {user.username}: {e}")
        return redirect(url_for("admin.admin_users"))
    else:
        logger.warning(f"Access Denied to {current_user.username}")
        return redirect(url_for("home.main"), 403, "access denied")
