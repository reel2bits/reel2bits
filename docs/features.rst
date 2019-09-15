Features
========

Scope
-----

reel2bits is an application designed to allow users to share content they create, it can be music albums, tracks or your own podcast.

Structure
---------

The project is split in two parts:

1. The backend a REST API developed using Python3 and Flask.
2. The frontend, that consumes the API, built as a single page application with VueJS.

While the main interface to the server and API is the bundled front-end, the project itself is agnostic in the way you connect to it.
Therefore, desktop clients or apps could be developed and could implement the same (or more) features as the bundled frontend.

This modularity also makes it possible to deploy only a single component from the system.

The backend shares some APIs used by Mastodon, so app development can be simplified a bit.

Federation
----------

Each reel2bits instance is able to federate its user profiles and Tracks with projects such as Mastodon or Pleroma.
Albums does not yet federates and will only federate with another reel2bits instance.

Another user using Mastodon or Pleroma can successfully follow a reel2bits user, and receive new tracks notifications as
soon as they are processed and available.
