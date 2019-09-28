#!/bin/bash -eux
waitress-serve --host 0.0.0.0 --port 8000 --call 'app:create_app'