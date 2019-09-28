#!/bin/bash -eux
waitress-serve --call app:create_app --host 0.0.0.0 --port 8000