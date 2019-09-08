#!/bin/bash -eux
# Script imported from https://dev.funkwhale.audio/funkwhale/funkwhale/
locales=$(tail -n +2 src/locales.js | sed -e 's/export default //' | jq '.locales[].code' | grep -v 'en_US' | xargs echo)
mkdir -p src/translations

for locale in $locales; do
    $(yarn bin)/gettext-compile locales/$locale/LC_MESSAGES/app.po --output src/translations/$locale.json
done

# find locales -name '*.po' | xargs $(yarn bin)/gettext-compile --output src/translations.json
