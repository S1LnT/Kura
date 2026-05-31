from flask import (
    Flask,
    render_template,
    Blueprint,
    url_for,
    send_from_directory,
    request,
    redirect,
    jsonify,
)
from flask_login import login_required, current_user
from .. import db, appConfig
from ..models import Post
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, ValidationError, Length
from ..customjinjafuncs import to_int
from .. import logger  
import json

home = Blueprint("home", __name__)

video_exts = [".mkv", ".mp4", ".webm"]
image_exts = [".jpg", ".png"]
audio_exts = [".mp3", ".ogg", ".m4a"]


class SearchForm(FlaskForm):
    search = StringField(
        validators=[InputRequired(), Length(min=1)],
        name="username",
        id="search",
        render_kw={"autocomplete": "search"},
    )

    submit = SubmitField("Search")


@home.app_template_filter("to_int")
def to_int_filter(value):
    return to_int(value)


@home.route("/home", methods=["GET", "POST"])
@home.route("/", methods=["GET", "POST"])
def main():
    searchbox = SearchForm()

    if searchbox.validate_on_submit and request.method == "POST":
        return redirect(url_for(".searchResults", searchText=searchbox.search.data))
    return render_template(
        "home.html",
        vexts=video_exts,
        aexts=audio_exts,
        POSTS_PER_PAGE=appConfig.POSTS_PER_PAGE,
        searchform=searchbox,
    )


@home.route("fileserve/<path:filename>")
def media(filename):
    return send_from_directory(appConfig.UPLOAD_FOLDER, filename, as_attachment=False)


@home.route("/download/<path:filename>", methods=["GET", "POST"])
def download(filename):
    logger.info(f"{current_user.username} downloaded {filename}")
    return send_from_directory(appConfig.UPLOAD_FOLDER, filename, as_attachment=True)


@home.route("/preview", methods=["GET", "POST"])
def prev():
    searchbox = SearchForm()
    if searchbox.validate_on_submit and request.method == "POST":
        return redirect(url_for(".searchResults", searchText=searchbox.search.data))
    posts = Post.query.offset(1).limit(10)
    return render_template(
        "prev_home.html",
        posts=posts,
        vexts=video_exts,
        aexts=audio_exts,
        searchform=searchbox,
    )


@home.route("/load_posts")
def load_posts():
    searchText = request.args.get("searchText", type=str)
    searchBool = request.args.get("search", type=int)

    if searchBool == 0:
        page = request.args.get("page", 1, type=int)
        posts = Post.query.order_by(Post.id.desc()).paginate(
            page=page, per_page=appConfig.POSTS_PER_PAGE, error_out=False
        )
    else:
        if searchText != None:
            page = request.args.get("page", 1, type=int)
        posts = Post.query.filter(Post.title.like(searchText + "%")).paginate(
            page=page, per_page=appConfig.POSTS_PER_PAGE, error_out=False
        )
    post_list = [
        {
            "current_user": current_user.id if current_user.is_authenticated else None,
            "permissions": current_user.permissions,
            "id": post.id,
            "title": post.title,
            "author": post.author,
            "desc": post.desc,
            "file_name": post.file_name,
            "lowest_view_perm": post.lowest_view_permission,
            "date_created": post.date_created.strftime("%Y/%m/%d %H:%M:%S"),
            "saved_by": post.saved_by,
            "file_type": (
                "video"
                if post.file_type in video_exts
                else (
                    "audio"
                    if post.file_type in audio_exts
                    else (
                        "image"
                        if post.file_type in image_exts
                        else "text" if post.file_type == "text" else "other"
                    )
                )
            ),
        }
        for post in posts.items
    ]
    return jsonify(post_list)


@home.route("/search", methods=["GET", "POST"])
def searchResults():
    searchbox = SearchForm()
    searchText = request.args["searchText"]
    if searchbox.validate_on_submit and request.method == "POST":
        return redirect(url_for(".searchResults", searchText=searchbox.search.data))
    return render_template(
        "home.html",
        vexts=video_exts,
        aexts=audio_exts,
        POSTS_PER_PAGE=appConfig.POSTS_PER_PAGE,
        searchform=searchbox,
        searchText=searchText,
    )


@home.route("/savepost/<id>", methods=["GET", "POST"])
def savePost(id):
    user = current_user.id
    # saves_list = Post.
    action = 1  # 0 = unsave 1 = save


@home.route("/pin/<id>", methods=["GET", "POST"])
def pinPost(id):
    with open(appConfig.DATA_PATH, "r") as f:
        data = json.load(f)

    data["pinned_post"] = id
    with open(appConfig.DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)
        logger.info(f"{current_user.username} pinned post {id}")
