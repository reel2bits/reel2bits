import click
from models import db, user_datastore, create_actor, Role, User
from flask.cli import with_appcontext
from flask import current_app
from flask_security.utils import hash_password
from flask_security import confirmable as FSConfirmable
import texttable


@click.group()
def users():
    """
    User commands.
    """
    pass


@users.command(name="list")
@click.option("--remote", default=False, is_flag=True, help="List remote users instead")
@with_appcontext
def list(remote):
    """
    List local users.
    """
    users = User.query.filter(User.local.is_(not remote))

    table = texttable.Texttable(max_width=120)
    table.set_deco(texttable.Texttable().HEADER)
    if remote:
        table.set_cols_dtype(["i", "t", "t", "i", "t"])
        table.set_cols_align(["l", "l", "l", "l", "l"])
        table.add_rows([["ID", "username", "display name", "tracks", "instance"]])
    else:
        table.set_cols_dtype(["i", "t", "t", "a", "i", "i", "i", "t"])
        table.set_cols_align(["l", "l", "l", "l", "r", "l", "l", "l"])
        table.add_rows([["ID", "username", "display name", "active", "quota", "remain", "tracks", "roles"]])

    for user in users.all():
        if user.local:
            table.add_row(
                [
                    user.id,
                    user.name,
                    user.actor[0].preferred_username,
                    ("Yes" if user.active else "No"),
                    f"{user.quota_count} / {user.quota}",
                    (user.quota - user.quota_count),
                    user.sounds.count(),
                    (", ".join(r.name for r in user.roles)),
                ]
            )
        else:
            table.add_row(
                [user.id, user.name, user.actor[0].preferred_username, user.sounds.count(), user.actor[0].domain]
            )

    print(table.draw())


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
            with current_app.app_context():
                FSConfirmable.send_confirmation_instructions(u)
                print("Look at your emails for validation instructions.")
