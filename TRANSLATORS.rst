Translating reel2bits
=====================

Thank you for reading this! If you want to help translate reel2bits,
you found the proper place :)

This doc is a placeholder for when we will have our own Weblate instance for translating more easily.

Translation workflow
--------------------

Once you're logged-in on the Weblate instance, you can suggest translations. Your suggestions will then be reviewed
by the project maintainer or other translators to ensure consistency.

Guidelines
----------

Respecting those guidelines is mandatory if you want your translation to be included:

- Use gender-neutral language and wording

Submitting a new language
-------------------------

1. Pull the latest version of ``master``
2. Create a new branch, e.g ``git checkout -b translations-new-fr-ca``
3. Add your new language code and name in ``front/src/locales.js``. Use the native language name, as it is what appears in the UI selector.
4. Create the ``po`` file from template:

.. code-block:: shell

    export LOCALE=fr_CA  # replace with your actual locale code
    mkdir -p front/locales/$LOCALE/LC_MESSAGES
    msginit --no-wrap --no-translator --locale=$LOCALE --input=front/locales/app.pot --output-file=front/locales/$LOCALE/LC_MESSAGES/app.po

5. Then commit your changes, push, and submit a pull request on the ``master`` branch

Requesting a new language
-------------------------

If you cannot submit a new language yourself, you can request it by opening an issue here:
https://github.com/rhaamo/reel2bits/issues

Extracting messages from source
-------------------------------

We offer a script to update existing ``po`` and ``pot`` files with new translations
from the source code. This action should be run regularly, and in particular before
lots of translation work is expected (e.g a few weeks before a new release), or when
the UI code changes a lot. Otherwise, translators end up translating some obsolete messages,
or not translationg new messages.

1. `Lock the translations on weblate <https://FIXME/projects/reel2bits/front/#repository>`_ (``Lock`` button in the sidebar). This will prevent translators from working, and help prevent potential conflicts in the source code
2. `Commit and push changes from weblate <https://FIXME/projects/reel2bits/front/#repository>`_ (``Commit`` and ``Push`` buttons in the sidebar)
3. Pull ``master`` in your local git repository to ensure you have the latest version of the translations
4. Create a dedicated branch with ``git checkout -b translations-integration``
5. Extract the translations with ``cd front && ./scripts/i18n-extract.sh``. This will update all ``po`` files as necessary
6. Review, commit and push the changes, then open a merge request on the ``master`` branch
7. When the PR is merged, `Unlock the translations on weblate <https://FIXME/projects/reel2bits/front/#repository>`_ (``Unlock`` button in the sidebar).
