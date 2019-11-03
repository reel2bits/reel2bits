Management commands
===================

Users
-----
- ``flask users list``: List local users (default), specify ``--remote`` to list remote users.
- ``flask users create``: Create a new user
- ``flask users promote-mod``: Promote an user as moderator
- ``flask users demote-mod``: Demote an user as moderator
- ``flask users confirm``: Force user activation

Roles
-----
- ``flask roles list``: List available roles

Database
--------

By default all commands are non-breaking, meaning you can launch them at any time when needed, otherwise breaking will be specified and needed to be acknowledged.

- ``flask db upgrade``: Upgrade database migrations
- ``flask db-datas 000-seeds``: Seed database with default roles and config
- ``flask db-datas 001-generate-tracks-uuids``: Generate tracks UUIDs when missing
- ``flask db-datas 002-set-local-users``: Fix user.local to match the actor
- ``flask db-datas 003-set-user-quota``: Set the default user quota
- ``flask db-datas 004-update-file-sizes``: Recompute all track files and transcodings sizes
- ``flask db-datas 005-update-user-quotas``: Recompute all users quotas

System
------
- ``flask system test-email``: Test sending an email to check it works properly
- ``flask system config``: Dump the whole configuration after interpreting it with interpolated variables
- ``flask system routes``: Print all known routes of the backend

Tracks
------
- ``flask tracks regenerate-waveform``: Regenerate a waveform or all
- ``flask tracks create-missing-activities``: Create missing Track Activity (useful if migrating from pre-frontv2)
