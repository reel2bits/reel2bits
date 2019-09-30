import click
from models import db, user_datastore, create_actor, Role
from flask.cli import with_appcontext
from flask import current_app
from flask_security.utils import hash_password
from flask_security import confirmable as FSConfirmable


@click.group()
def users():
    """
    User commands.
    """
    pass


@users.command(name="create")
@with_appcontext
def create():
    """
    Create a user.
    """
    current_app.config["SERVER_NAME"] = current_app.config["REEL2BITS_HOSTNAME"]
    username = click.prompt("Username", type=str)
    email = click.prompt("Email", type=str)
    password = click.prompt("Password", type=str, hide_input=True, confirmation_prompt=True)
    while True:
        role = click.prompt("Role [admin/user]", type=str)
        if role == "admin" or role == "user":
            break

    if click.confirm("Do you want to continue ?"):
        role = Role.query.filter(Role.name == role).first()
        if not role:
            raise click.UsageError("Roles not present in database")
        u = user_datastore.create_user(name=username, email=email, password=hash_password(password), roles=[role])

        actor = create_actor(u)
        actor.user = u
        actor.user_id = u.id
        db.session.add(actor)

        db.session.commit()

        if FSConfirmable.requires_confirmation(u):
            FSConfirmable.send_confirmation_instructions(u)
            print("Look at your emails for validation instructions.")
