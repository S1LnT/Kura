from flask import Flask, render_template, Blueprint, url_for, redirect, request
from .. import socketio, appConfig, logger
import threading, os, json
from time import sleep
from flask_login import current_user, login_required

notes = Blueprint("notes", __name__)


@socketio.on("textareaChanged")
def handle_textarea_change(data):
    try:

        with open(
            os.path.join(appConfig.NOTES_INSTANCES_FOLDER, data["instance"]), "w"
        ) as txtfile:
            txtfile.write(data["text"])

        # Optionally broadcast the change to other clients
        socketio.emit("textareaUpdate", data)

    except Exception as e:
        print(f"Error writing to file: {e}")
        # You can emit an error message back to the client if necessary


# @socketio.on('connect')
# def handle_connect():
#    notes_id = request.args.get('notes_id')
#    if notes_id:
#        socketio.join_room(notes_id)


@login_required
@notes.route("/notes/menu", methods=["GET", "POST"])
def main():
    data = json.load(open(appConfig.NOTES_DATA_PATH))
    for data in data:
        pass


@login_required
@notes.route("/notes/<notes_id:instance>")  
def note(instance):
    data = json.load(open(appConfig.NOTES_DATA_PATH))
    if current_user.is_authenticated:
        try:
            # Use 'with' to safely read the file
            with open(
                os.path.join(appConfig.appConfig.NOTES_INSTANCES_FOLDER, instance), "r"
            ) as txtfile:
                txt = txtfile.read()
            return render_template("notes.html", text=txt, room_num=instance)
        except Exception as e:
            print(f"Error reading file: {e}")
            # Handle errors or redirect to an error page
            return "Error reading notes", 500
    else:
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@notes.route("/notes/create", methods=["GET", "POST"])
def create_notes():
    if current_user.is_authenticated:
        try:
            n_instance = len(os.listdir(appConfig.NOTES_INSTANCES_FOLDER)) + 1
            f = open(
                os.path.join(appConfig.NOTES_INSTANCES_FOLDER, "note" + n_instance + ".txt"), "w"
            )
            f.close()
            return render_template("notes.html")
        except Exception as e:
            print(f"Error reading file: {e}")
            # Handle errors or redirect to an error page
            return "Error reading notes", 500
    else:
        return redirect(url_for("home.main"), 403, "access denied")


@login_required
@notes.route("/notes/delete/<instance>", methods=["GET", "POST"])
def delete_notes(instance):
    owner = ""  # file json
    if current_user.is_authenticated and (
        current_user.id == owner or current_user.permissions == 999
    ):
        try:
            notes_path = os.path.join(appConfig.NOTES_INSTANCES_FOLDER, instance)
            if os.path.isfile(notes_path) or os.path.islink(notes_path):
                os.unlink(notes_path)
                logger.error(f"Deleted Note instance({instance}) owner:{post.title}")
                return redirect(url_for("home.main"), 200, "note deleted")
        except Exception as e:
            logger.error(
                f"Error deleting Note instance({instance}) owner:{post.title}: {e}"
            )
            return redirect(url_for("home.main"), 500, "error deleting note")
    try:
        notes_path = os.path.join(appConfig.NOTES_INSTANCES_FOLDER, instance)
        if os.path.isfile(notes_path) or os.path.islink(notes_path):
            os.unlink(notes_path)
            logger.error(f"Deleted Note instance({instance}) owner:{post.title}")
    except Exception as e:
        logger.error(
            f"Error deleting Note instance({instance}) owner:{post.title}: {e}"
        )
