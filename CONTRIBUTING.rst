Contribute to reel2bits development
===================================

First of all, thank you for your interest in the project! We really
appreciate the fact that you're about to take some time to read this
and hack on the project.

This document will guide you through common operations such as:

- Setup your development environment
- Working on your first issue
- Writing unit tests to validate your work
- Submit your work

Quick summary of the various stacks / libraries we use
------------------------------------------------------

Backend:

- `Flask <https://flask.palletsprojects.com/en/1.1.x/>`_
- `SQLAlchemy <https://www.sqlalchemy.org/>`_
- `Gettext <https://www.gnu.org/software/gettext/>`_
- `Celery <http://www.celeryproject.org/>`_
- ActivityPub (through `little-boxes <https://little-boxes.readthedocs.io/en/latest/>`_ library)
- `PostgreSQL <https://www.postgresql.org/>`_

Frontend

- `VueJS <https://vuejs.org/>`_
- `Bootstrap-vue <https://bootstrap-vue.js.org/>`_
- `Gettext <https://www.gnu.org/software/gettext/>`_

A quick path to contribute on the front-end
-------------------------------------------

The next sections of this document include a full installation guide to help
you setup a local, development version of reel2bits.

As the front-end can work with any reel2bits server, you can work with the front-end only,
and make it talk with an existing instance (like the demo one, or you own instance, if you have one).

Setup front-end only development environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Clone the repository::

    git clone https://github.com/rhaamo/reel2bits.git
    cd reel2bits
    cd front

2. Install `nodejs <https://nodejs.org/en/download/package-manager/>`_ and `yarn <https://yarnpkg.com/lang/en/docs/install/#debian-stable>`_

3. Install the dependencies::

    yarn install

4. Compile the translations::

    yarn i18n-compile

5. Configure your frontend for instance location::

    cp config/local.example.json config/local.json
    # Then edit config/local.json to point to any instance wanted
    # Don't forget to set the "host" to the right hostname the instance expect

6. Launch the development server::

    # this will serve the front-end on http://localhost:8081/
    npm run dev

7. Start hacking!

Setup your development environment
----------------------------------

If you want to fix a bug or implement a feature, you'll need
to run a local, development copy of reel2bits.

We provide a docker based development environment, which should
be both easy to setup and work similarly regardless of your
development machine setup.

Installing docker and docker-compose
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is already cover in the relevant documentations:

- https://docs.docker.com/install/
- https://docs.docker.com/compose/install/

A note about branches
^^^^^^^^^^^^^^^^^^^^^

Everything happens in ``master`` branch. Therefore, when submitting Merge Requests, ensure you are merging on the master branch.

Working with docker
^^^^^^^^^^^^^^^^^^^

In development, we use the docker-compose file named ``dev.yml``, and this is why all our docker-compose commands will look like this::

    docker-compose -f dev.yml logs

If you do not want to add the ``-f dev.yml`` snippet every time, you can run this command before starting your work::

    export COMPOSE_FILE=dev.yml


Creating your env file
^^^^^^^^^^^^^^^^^^^^^^

We provide a working .env.dev configuration file that is suitable for
development. However, to enable customization on your machine, you should
also create a .env file that will hold your personal environment
variables (those will not be commited to the project).

Create it like this::

    touch .env

Create docker network
^^^^^^^^^^^^^^^^^^^^^

Create the federation network::

    docker network create federation


Building the containers
^^^^^^^^^^^^^^^^^^^^^^^

On your initial clone, or if there have been some changes in the
app dependencies, you will have to rebuild your containers. This is done
via the following command::

    docker-compose -f dev.yml build


Database management
^^^^^^^^^^^^^^^^^^^

You first have to add an extension in the postgresql database, run this command one time::

    docker-compose -f dev.yml run --rm api psql -U postgres -h postgres -w -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' postgres

Then you can run the database migrations::

    docker-compose -f dev.yml run --rm api flask db upgrade

This will create all the tables needed for the API to run properly.
You will also need to run this whenever changes are made on the database
schema.

It is safe to run this command multiple times, so you can run it whenever
you fetch develop.

Then run the database seeds:

    docker-compose -f dev.yml run --rm api flask db-datas 000-seeds

You should run only one time this command.

Development data
^^^^^^^^^^^^^^^^

You'll need at least an admin user to work
locally.

Create an admin user with the following command::

    docker-compose -f dev.yml run --rm api flask users create


Launch all services
^^^^^^^^^^^^^^^^^^^

Before the first reel2bits launch, it is required to run this::

    docker-compose -f dev.yml run --rm front yarn run i18n-compile

Then you can run everything with::

    docker-compose -f dev.yml up front api nginx celeryworker

This will launch all services, and output the logs in your current terminal window.
If you prefer to launch them in the background instead, use the ``-d`` flag, and access the logs when you need it via ``docker-compose -f dev.yml logs --tail=50 --follow``.

Once everything is up, you can access the various funkwhale's components:

- The Vue webapp, on http://localhost:8081/
- The Backend API, on http://localhost:8000/home
- The documentation, on http://localhost:8001/ if you launch the 'docs' container.

Development note only:
Unfortunately because on how the frontend is made, we can't proxy it through http from the backend.
You have to access the frontend directly, which will automatically proxy the backend API.

Stopping everything
^^^^^^^^^^^^^^^^^^^

Once you're down with your work, you can stop running containers, if any, with::

    docker-compose -f dev.yml stop


Removing everything
^^^^^^^^^^^^^^^^^^^

If you want to wipe your development environment completely (e.g. if you want to start over from scratch), just run::

    docker-compose -f dev.yml down -v

This will wipe your containers and data, so please be careful before running it.

You can keep your data by removing the ``-v`` flag.


Working with federation locally
-------------------------------

This is not needed unless you need to work on federation-related features.

To achieve that, you'll need:

1. to update your dns resolver to resolve all your .dev hostnames locally
2. a reverse proxy (such as traefik or nginx) to catch those .dev requests and
   and with https certificate
3. two instances (or more) running locally, following the regular dev setup

Typical workflow for a contribution
-----------------------------------

0. Fork the project if you did not already or if you do not have access to the main repository
1. Checkout the development branch and pull most recent changes: ``git checkout master && git pull``
2. If working on an issue, assign yourself to the issue. Otherwise, consider open an issue before starting to work on something, especially for new features.
3. Create a dedicated branch for your work ``42-awesome-fix``. It is good practice to prefix your branch name with the ID of the issue you are solving.
4. Work on your stuff
5. Commit small, atomic changes to make it easier to review your contribution
6. Add a changelog fragment to summarize your changes: ``echo "Implemented awesome stuff (#42)" >> CHANGELOG``
7. Push your branch
8. Create your merge request
9. Take a step back and enjoy, we're really grateful you did all of this and took the time to contribute!

Internationalization
--------------------

We're using https://github.com/Polyconseil/vue-gettext to manage i18n in the project.

When working on the front-end, any end-user string should be marked as a translatable string,
with the proper context, as described below.

Translations in HTML
^^^^^^^^^^^^^^^^^^^^

Translations in HTML use the ``<translate>`` tag::

    <template>
      <div>
        <h1><translate translate-context="Content/Profile/Header">User profile</translate></h1>
        <p>
          <translate
            translate-context="Content/Profile/Paragraph"
            :translate-params="{username: 'alice'}">
            You are logged in as %{ username }
          </translate>
        </p>
         <p>
          <translate
            translate-context="Content/Profile/Paragraph"
            translate-plural="You have %{ count } new messages, that's a lot!"
            :translate-n="unreadMessagesCount"
            :translate-params="{count: unreadMessagesCount}">
            You have 1 new message
          </translate>
        </p>
      </div>
    </template>

Anything between the `<translate>` and `</translate>` delimiters will be considered as a translatable string.
You can use variables in the translated string via the ``:translate-params="{var: 'value'}"`` directive, and reference them like this:
``val value is %{ value }``.

For pluralization, you need to use ``translate-params`` in conjunction with ``translate-plural`` and ``translate-n``:

- ``translate-params`` should contain the variable you're using for pluralization (which is usually shown to the user)
- ``translate-n`` should match the same variable
- The ``<translate>`` delimiters contain the non-pluralized version of your string
- The ``translate-plural`` directive contains the pluralized version of your string


Translations in javascript
^^^^^^^^^^^^^^^^^^^^^^^^^^

Translations in javascript work by calling the ``this.$*gettext`` functions::

    export default {
      computed: {
        strings () {
          let tracksCount = 42
          let playButton = this.$pgettext('Sidebar/Player/Button/Verb, Short', 'Play')
          let loginMessage = this.$pgettext('*/Login/Message', 'Welcome back %{ username }')
          let addedMessage = this.$npgettext('*/Player/Message', 'One track was queued', '%{ count } tracks were queued', tracksCount)
          console.log(this.$gettextInterpolate(addedMessage, {count: tracksCount}))
          console.log(this.$gettextInterpolate(loginMessage, {username: 'alice'}))
        }
      }
    }

The first argument of the ``$pgettext`` and ``$npgettext`` functions is the string context.

Contextualization
^^^^^^^^^^^^^^^^^

Translation contexts provided via the ``translate-context`` directive and the ``$pgettext`` and ``$npgettext`` are never shown to end users
but visible by reel2bits translators. They help translators where and how the strings are used,
especially with short or ambiguous strings, like ``May``, which can refer a month or a verb.

While we could in theory use free form context, like ``This string is inside a button, in the main page, and is a call to action``,
reel2bits use a hierarchical structure to write contexts and keep them short and consistents accross the app. The previous context,
rewritten correctly would be: ``Content/Home/Button/Call to action``.

This hierarchical structure is made of several parts:

- The location part, which is required and refers to the big blocks found in reel2bits UI where the translated string is displayed:
    - ``Content``
    - ``Footer``
    - ``Head``
    - ``Menu``
    - ``*`` for strings that are not tied to a specific location

- The feature part, which is required, and refers to the feature/component associated with the translated string:
    - ``About``
    - ``AlbumEdit``
    - ``AlbumNew``
    - ``Login``
    - ``Logs(user)``
    - ``NotFound``
    - ``PasswordReset``
    - ``PasswordResetToken``
    - ``Register``
    - ``Timeline``
    - ``TimelineTabs``
    - ``TrackEdit``
    - ``TrackShow``
    - ``TrackUpload``
    - ``UserCard``
    - ``UserCardList``
    - ``UserFollowers``
    - ``UserFollowings``
    - ``UserSettings``
    - ``UserProfile``
    - ``*`` for strings that are not tied to a specific feature

- The component part, which is required and refers to the type of element that contain the string:
    - ``Button``
    - ``Card``
    - ``Checkbox``
    - ``Dropdown``
    - ``Error message``
    - ``Form``
    - ``Header``
    - ``Help text``
    - ``Hidden text``
    - ``Icon``
    - ``Input``
    - ``Image``
    - ``Label``
    - ``Link``
    - ``List item``
    - ``Menu``
    - ``Message``
    - ``Paragraph``
    - ``Placeholder``
    - ``Tab``
    - ``Table``
    - ``Title``
    - ``Tooltip``
    - ``Feedback``
    - ``*`` for strings that are not tied to a specific component

The detail part, which is optional and refers to the contents of the string itself, such as:
    - ``Adjective``
    - ``Call to action``
    - ``Noun``
    - ``Short``
    - ``Unit``
    - ``Verb``
    - ``Or anything useful``

Here are a few examples of valid context hierarchies:

- ``Sidebar/Player/Button``
- ``Content/Home/Button/Call to action``
- ``Footer/*/Help text``
- ``*/*/*/Verb, Short``
- ``Popup/Playlist/Button``
- ``Content/Admin/Table.Label/Short, Noun (Value is a date)``
- ``Header/*/Input/Search ARIA`` (ARIA html key)

It's possible to nest multiple component parts to reach a higher level of detail. The component parts are then separated by a dot:

- ``Sidebar/Queue/Tab.Title``
- ``Content/*/Button.Title``
- ``Content/*/Table.Header``
- ``Footer/*/List item.Link``
- ``Content/*/Form.Help text``

Collecting translatable strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to ensure your translatable strings are correctly marked for translation,
you can try to extract them.

Extraction is done by calling ``yarn run i18n-extract``, which
will pull all the strings from source files and put them in a PO files.

You can then inspect the PO files to ensure everything is fine (but don't commit them, it's not needed).

Contributing to the Backend API
-------------------------------

Project structure
^^^^^^^^^^^^^^^^^

.. code-block:: shell

    backend (api/):
    .
    ├── controllers             # backend controllers, some are in this folder, which would be /something endpoints
    ├── └── api                 # anything under the /api/ namespace is here
    ├──     └── v1              # same for /api/v1/
    ├── activitypub             # ActivityPub related things (LittleBoxes backend mostly)
    ├── migrations              # Database migrations, always respect the format "<incr number>_<autogenerated thing>.py" for readability
    ├── templates               # Views rendered by the backend, or email templates
    └── tests                   # unit tests for the backend

    frontend (front/):
    .
    ├── build               # webpack and build related stuff
    ├── config              # configuration for frontend
    ├── locales             # translations locales
    ├── scripts             # helpers scripts
    ├── src
    │   ├── backend         # actually oauth related stuff
    │   ├── boot            # setup of store and front settings
    │   ├── components      # components of vue app
    │   ├── lib             # actually persisted state handling
    │   ├── modules         # modules shared by the whole app
    │   ├── services        # some helpers
    │   ├── translations    # translations files
    │   └── views           # for things bigger than "components", more organised like views/tracks/Show.vue, views/tracks/Upload.vue, ...
    └── test                # testing stuff
        ├── e2e
        ├── fixtures
        └── unit

.. note::

    Unless trivial, API contributions must include unittests to ensure
    your fix or feature is working as expected and won't break in the future

Running tests
^^^^^^^^^^^^^

To run tests for backend::

    APP_SETTINGS="config.testing.Config"
    python setup.py test


Writing tests
^^^^^^^^^^^^^

Although teaching you how to write unit tests is outside of the scope of this
document, you'll find below a collection of tips, snippets and resources
you can use if you want to learn on that subject.

Useful links:

- `A quick introduction to unit test writing with pytest <https://semaphoreci.com/community/tutorials/testing-python-applications-with-pytest>`_
- `A complete guide to Test-Driven Development (although not using Pytest) <https://www.obeythetestinggoat.com/>`_
- `pytest <https://docs.pytest.org/en/latest/>`_: documentation of our testing engine and runner

Recommendations:

- Test files for must target a module and ideally mimic ``controllers`` directory structure: if you're writing tests for ``controllers/api/v1/foobar.py``, you should put thoses tests in ``tests/api/v1/foobar.py``
- Tests should be small and test one thing. If you need to test multiple things, write multiple tests.

We provide some utils and fixtures to make the process of writing tests as
painless as possible.

.. note::

    The back-end test suite coverage is still pretty low

Linters & format
^^^^^^^^^^^^^^^^

We use black and flake8::

    flake8 .
    black .

Various notes
^^^^^^^^^^^^^

- Authlib doesn't handle JSON, do crimes like in controllers/api/v1/auth.py#oauth_token()
- Authlib revoke token wants basic auth, no idea what to give, so it doesn't works
- Authlib does handle optional bearer auth, uses: @require_oauth(optional=True)

Translations notes
^^^^^^^^^^^^^^^^^^

While there is still some in the backend, and that is going to change.

Parse translation strings::

    pybabel extract -F babel.cfg -k gettext -o messages.pot .

create document::

    pybabel init -i messages.pot -d translations -l de

update document::

    pybabel update -i messages.pot -d translations

compile documents::

    pybabel compile -d translations

Contributing to the front-end
-----------------------------

Backend proxy
^^^^^^^^^^^^^

The frontend will automatically proxy the backend configured in ``config/local.json``.

Running tests
^^^^^^^^^^^^^

To run the front-end test suite, use the following command::

    cd front
    npm run unit

.. note::

    The front-end test suite coverage is still pretty low

Linters & format
^^^^^^^^^^^^^^^^

Check::

    npm run lint

Lazy autofix (check if nothing gots wrong)::

    npm run lint-fix
