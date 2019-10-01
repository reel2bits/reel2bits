import click
import texttable
from models import Role
from flask.cli import with_appcontext


@click.group()
def roles():
    """
    Role commands.
    """
    pass


@roles.command(name="list")
@with_appcontext
def list():
    """
    List roles.
    """
    roles = Role.query.order_by(Role.id.asc())

    table = texttable.Texttable()
    table.set_deco(texttable.Texttable().HEADER)
    table.set_cols_dtype(["t", "t"])
    table.set_cols_align(["l", "l"])
    table.add_rows([["Name", "Description"]])

    for role in roles.all():
        table.add_row([role.name, role.description])

    print(table.draw())
