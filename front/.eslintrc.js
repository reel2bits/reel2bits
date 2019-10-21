module.exports = {
  root: true,
  parserOptions: {
    parser: 'babel-eslint',
    sourceType: 'module'
  },
  // https://github.com/feross/standard/blob/master/RULES.md#javascript-standard-style
  extends: [
    'standard',
    'plugin:vue/recommended'
  ],
  // required to lint *.vue files
  plugins: [
    'vue'
  ],
  // add your custom rules here
  rules: {
    // allow paren-less arrow functions
    'arrow-parens': 0,
    // allow async-await
    'generator-star-spacing': 0,
    // allow debugger during development
    'no-debugger': process.env.NODE_ENV === 'production' ? 2 : 0,
    // Webpack 4 update commit, most of these probably should be fixed and removed in a separate MR
    // A lot of errors come from .vue files that are now properly linted
    'vue/valid-v-if': 1,
    'vue/use-v-on-exact': 1,
    'vue/no-parsing-error': 1,
    'vue/require-v-for-key': 1,
    'vue/valid-v-for': 1,
    'vue/require-prop-types': 1,
    'vue/no-use-v-if-with-v-for': 1,
    'indent': 1,
    'import/first': 1,
    'object-curly-spacing': 1,
    'prefer-promise-reject-errors': 1,
    'eol-last': 1,
    'no-return-await': 1,
    'no-multi-spaces': 1,
    'no-trailing-spaces': 1,
    'no-unused-expressions': 1,
    'no-mixed-operators': 1,
    'camelcase': 1,
    'no-multiple-empty-lines': 1,
    // don't nag on v-html
    'vue/no-v-html': 0,
    'vue/max-attributes-per-line': ['error', {
      'singleline': 3,
      'multiline': {
        'max': 3,
        "allowFirstLine": true
      }
    }],
    'vue/require-default-prop': 0
  }
}
