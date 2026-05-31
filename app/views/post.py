from flask import (
    Flask,
    render_template,
    Blueprint,
    url_for,
    flash,
    redirect,
    request,
    make_response,
    jsonify,
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, TextAreaField, RadioField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.utils import secure_filename
from .. import db, appConfig
from ..models import Post
from .. import socketio
from threading import Lock
from filelock import FileLock
import os, shutil, re
import time
import clamd
from .. import logger

av = clamd.ClamdUnixSocket()
thread = None
thread_lock = Lock()
post = Blueprint("post", __name__)


class PostForm(FlaskForm):
    title = StringField(
        validators=[InputRequired(), Length(min=1, max=1000)],
        name="title",
        id="floatingTitle",
        render_kw={"placeholder": "Title"},
    )
    desc = TextAreaField(
        validators=[InputRequired(), Length(min=1, max=5000)],
        name="desc",
        id="floatingDesc",
        render_kw={"placeholder": "Description", "style": "resize: none;"},
    )

    perm = RadioField(
        validators=[InputRequired()],
        name="Perm",
        choices=[("0", "Guests"), ("1", "Users"), ("999", "Admin")],
    )


def custom_flash(msg, color, sid):
    data = {"msg": msg, "color": color}
    socketio.emit("flash", data, room=sid)


def format_eta(seconds):
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        return f"{seconds / 60:.0f} minutes"
    elif seconds < 86400:
        return f"{seconds / 3600:.0f} hours"
    else:
        return f"{seconds / 86400:.0f} days"


def count_files_with_base_name(directory, filename, extension):
    pattern = rf"^{re.escape(filename)}(?:_\((\d+)\))?{re.escape(extension)}$"
    count = 0

    for file_name in os.listdir(directory):
        if re.match(pattern, file_name):
            count += 1

    return count


@post.route("/disk-space", methods=["GET", "POST"])
def get_remaining_disk_space():
    """Calculate the remaining disk space minus 1GB."""
    total, used, free = shutil.disk_usage(appConfig.UPLOAD_FOLDER)
    free_space = free - appConfig.DISK_BUFFER_SIZE  # Remaining disk space minus 1GB
    return jsonify({"available_space": free_space})


@login_required
@post.route("/post", methods=["GET", "POST"])
def PostFile():
    global thread
    form = PostForm()
    if request.method == "POST":
        custom_flash("", "lime", request.form.get("sid"))
        if request.form.get("dzuuid") is not None:
            logger.info("File dropzone unique id: " + request.form.get("dzuuid"))
            file = request.files.get("file")
            filename = secure_filename(request.form.get("filename"))
            tmp_dir = os.path.join(appConfig.TEMP_FOLDER, request.form.get("dzuuid"))
            os.makedirs(
                tmp_dir, exist_ok=True
            )  # Create a temporary directory for chunks

            current_chunk = int(request.form.get("dzchunkindex", 0))
            total_chunks = int(request.form.get("dztotalchunkcount", 1))

            chunk_path = os.path.join(tmp_dir, f"chunk_{current_chunk}")
            with open(chunk_path, "wb") as chunk_file:
                chunk_file.write(file.stream.read())  # Save the chunk to a file
            uploaded_chunks = len(
                [name for name in os.listdir(tmp_dir) if name.startswith("chunk_")]
            )

            # Check if all chunks are uploaded
            if uploaded_chunks == total_chunks:
                # All chunks uploaded, merge them

                esits_files = count_files_with_base_name(
                    appConfig.UPLOAD_FOLDER,
                    os.path.splitext(filename)[0],
                    os.path.splitext(filename)[1].lower(),
                )

                # Handle file name collision
                if esits_files != 0:
                    filename = f"{os.path.splitext(filename)[0]}_({esits_files}){os.path.splitext(filename)[1].lower()}"
                final_tmp_path = os.path.join(appConfig.TEMP_FOLDER, filename)
                save_path = os.path.join(appConfig.UPLOAD_FOLDER, filename)

                # Lock the file to prevent concurrent writes
                lockfile = final_tmp_path + ".lock"
                lock = FileLock(lockfile)
                with lock:
                    with open(final_tmp_path, "wb") as final_file:
                        for i in range(total_chunks):
                            chunk_path = os.path.join(tmp_dir, f"chunk_{i}")
                            with open(chunk_path, "rb") as chunk_file:
                                final_file.write(
                                    chunk_file.read()
                                )  # Write each chunk in order

                for i in range(total_chunks):
                    os.remove(os.path.join(tmp_dir, f"chunk_{i}"))
                os.rmdir(tmp_dir)
                if os.path.isfile(lockfile) or os.path.islink(lockfile):
                    os.unlink(lockfile)

                custom_flash("Waiting for AV scan", "yellow", request.form.get("sid"))

                if request.form.get("avchk") != "skip":
                    logger.info("AV alive check: " + av.ping())
                    av_result = av.scan(final_tmp_path)
                    for key, value in av_result.items():
                        result = value[0]
                        logger.info("AV result: " + result)
                else:
                    result = "SKIPPED"

                if result == "OK" or result is None or result == "SKIPPED":
                    shutil.move(final_tmp_path, save_path)
                    if os.path.isfile(final_tmp_path) or os.path.islink(final_tmp_path):
                        os.unlink(final_tmp_path)
                    new_post = Post(
                        title=request.form.get("title"),
                        desc=request.form.get("description"),
                        file_name=filename,
                        file_loc=save_path,
                        author=current_user.username,
                        file_type=os.path.splitext(filename)[1].lower(),
                        lowest_view_permission=request.form.get("perm"),
                    )
                    db.session.add(new_post)
                    db.session.commit()
                    if result == "OK":
                        logger.info(
                            f"File {filename} uploaded and posted by {current_user.username}"
                        )
                        custom_flash(
                            "File verificato e Post pubblicato",
                            "lime",
                            request.form.get("sid"),
                        )
                        return make_response(
                            ("File successfully uploaded and Posted", 200)
                        )
                    elif result == "SKIPPED":
                        logger.info(
                            f"File {filename} uploaded and posted by {current_user.username} but not scanned"
                        )
                        custom_flash(
                            "File verificato e Post pubblicato ma non controllato",
                            "orange",
                            request.form.get("sid"),
                        )
                        return make_response(
                            (
                                "File successfully uploaded and Posted but scan skipped",
                                200,
                            )
                        )
                    else:
                        logger.warning(
                            f"File {filename} uploaded and posted by {current_user.username} but flagged as malware"
                        )
                        custom_flash(
                            "File verificato e Post pubblicato ma risulta posivito all'AV",
                            "orange",
                            request.form.get("sid"),
                        )
                        return make_response(
                            (
                                "File successfully uploaded and Posted (but with positive from AV)",
                                200,
                            )
                        )
                else:
                    logger.warning(
                        f"File {filename} uploaded not posted by {current_user.username} but flagged as malware"
                    )
                    custom_flash(
                        "Flagged as positive for AV, usa admin per caricare il file",
                        "red",
                        request.form.get("sid"),
                    )
                    return make_response(
                        ("File successfully uploaded but malware ", 200)
                    )
        else:
            filename = ""

            new_post = Post(
                title=form.title.data,
                desc=form.desc.data,
                file_name=filename,
                file_loc="",
                author=current_user.username,
                file_type="text",
                lowest_view_permission=form.perm.data,
            )
            db.session.add(new_post)
            db.session.commit()
            logger.info(
                f"Text Post {form.title.data} created by {current_user.username}"
            )
            custom_flash("Post pubblicato", "lime", request.form.get("sid"))
    return render_template("post.html", form=form)
