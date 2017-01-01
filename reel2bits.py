# encoding: utf-8
import datetime
import os
from pprint import pprint as pp

import texttable
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import MigrateCommand
from flask_script import Manager

from crons import cron_generate_sound_infos
from dbseed import make_db_seed
from models import db

try:
    from raven.contrib.flask import Sentry
    import raven
    print(" * Sentry support loaded")
    HAS_SENTRY = True
except ImportError as e:
    print(" * No Sentry support")
    HAS_SENTRY = False

from app import create_app

app = create_app()

if HAS_SENTRY:
    app.config['SENTRY_RELEASE'] = raven.fetch_git_sha(os.path.dirname(__file__))
    sentry = Sentry(app, dsn=app.config['SENTRY_DSN'])
    print(" * Sentry support activated")
    print(" * Sentry DSN: %s" % app.config['SENTRY_DSN'])

toolbar = DebugToolbarExtension(app)
manager = Manager(app)


# Other commands
@manager.command
def routes():
    """Dump all routes of defined app"""
    table = texttable.Texttable()
    table.set_deco(texttable.Texttable().HEADER)
    table.set_cols_dtype(['t', 't', 't'])
    table.set_cols_align(["l", "l", "l"])
    table.set_cols_width([60, 30, 90])

    table.add_rows([["Prefix", "Verb", "URI Pattern"]])

    for rule in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
        methods = ','.join(rule.methods)
        table.add_row([rule.endpoint, methods, rule])

    print(table.draw())


@manager.command
def config():
    """Dump config"""
    pp(app.config)


@MigrateCommand.command
def seed():
    """Seed database with default content"""
    make_db_seed(db)

CacheCommand = Manager(usage='Perform cache actions')
CronCommand = Manager(usage='Perform crons actions')


@CronCommand.command
@CronCommand.option('--dryrun', dest='dry_run', action='store_true', default=False,
                    help="Dry run, doesn't commit anything")
@CronCommand.option('--force', dest='force', action='store_true', default=False,
                    help="Force re-generation")
def generate_sound_infos(dry_run=False, force=False):
    """Generate Sound Infos """
    print("-- STARTED on {0}".format(datetime.datetime.now()))
    cron_generate_sound_infos(dry_run, force)
    print("-- FINISHED on {0}".format(datetime.datetime.now()))


manager.add_command('db', MigrateCommand)
manager.add_command('cache', CacheCommand)
manager.add_command('cron', CronCommand)

if __name__ == '__main__':
    try:
        manager.run()
    except KeyboardInterrupt as e:
        print("Got KeyboardInterrupt, halting...")
        print(e)
