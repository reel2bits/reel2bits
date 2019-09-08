#!/bin/bash -eux
# Script imported from: https://dev.funkwhale.audio/funkwhale/funkwhale/
locales=$(tail -n +2 src/locales.js | sed -e 's/export default //' | jq '.locales[].code' | xargs echo)
locales_dir="locales"
sources=$(find src -name '*.vue' -o -name '*.html' 2> /dev/null)
js_sources=$(find src -name '*.vue' -o -name '*.js')
touch $locales_dir/app.pot

# Create a main .pot template, then generate .po files for each available language.
# Extract gettext strings from templates files and create a POT dictionary template.
$(yarn bin)/gettext-extract --attribute v-translate --quiet --output $locales_dir/app.pot $sources
xgettext --language=JavaScript --keyword=npgettext:1c,2,3 \
    --from-code=utf-8 --join-existing --no-wrap \
    --package-name=$(node -e "console.log(require('./package.json').name);") \
    --package-version=$(node -e "console.log(require('./package.json').version);") \
    --output $locales_dir/app.pot $js_sources \
    --no-wrap

# Fix broken files path/lines in pot
# TODO: detect sed/gsed properly
gsed -e 's|#: src/|#: front/src/|' -i $locales_dir/app.pot

# Generate .po files for each available language.
echo $locales
for lang in $locales; do \
    po_file=$locales_dir/$lang/LC_MESSAGES/app.po; \
    echo "msgmerge --update $po_file "; \
    mkdir -p $(dirname $po_file); \
    [ -f $po_file ] && msgmerge --lang=$lang --update $po_file $locales_dir/app.pot --no-wrap || msginit --no-wrap --no-translator --locale=$lang --input=$locales_dir/app.pot --output-file=$po_file; \
    msgattrib --no-wrap --no-obsolete -o $po_file $po_file; \
done;
