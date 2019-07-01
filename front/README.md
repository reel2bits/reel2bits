## Build Setup

``` bash
# install dependencies
npm install -g yarn
yarn

# serve with hot reload at localhost:8080
npm run dev

# build for production with minification
npm run build

# run unit tests
npm run unit
```

# For Contributors:

You can create file `/config/local.json` see `/config/local.example.json` to enable some convenience dev options:

* `target`: makes local dev server redirect to some existing instance's BE instead of local BE, useful for testing things in near-production environment and searching for real-life use-cases.

FE Build process also leaves current commit hash in global variable `___reel2bitsfe_commit_hash` so that you can easily see which reel2bits-fe commit instance is running, also helps pinpointing which commit was used when FE was bundled into BE.
