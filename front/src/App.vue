<template>
  <div id="app">
    <!-- Top navigation -->
    <nav class="navbar fixed-top bg-light">
      <div class="container">
        <div class="w-100 border-bottom align-items-center d-flex justify-content-between">
          <b-link to="/" class="navbar-brand">
            <img src="/static/logo.svg" width="64" height="64"
                 alt="Reel2Bits logo"
            ><h3 class="text-body mx-3 d-inline">
              {{ sitename }}
            </h3>
          </b-link>
          <div class="col-md-4">
            <input id="topsearch" class="form-control" type="search"
                   placeholder="Search" aria-label="Search"
            >
          </div>
          <div>
            <router-link to="/about">
              About
            </router-link>
            <span v-if="currentUser">
              | <router-link to="/tracks/upload">Upload track</router-link>
              | <router-link to="/albums/new">New album</router-link>
              | <router-link :to="{ name: 'user-profile', params: { name: currentUser.screen_name } }">Me</router-link>
              | <a
                href="#"
                @click.prevent="logout"
              >Logout</a></span>
            <span v-else>
              | <router-link to="/login">Login</router-link>
              |
              <router-link
                v-if="!currentUser"
                to="/register"
              >Register</router-link>
            </span>
          </div>
        </div>
      </div>
    </nav>

    <!-- content -->
    <div class="container">
      <router-view />
    </div>
  </div>
</template>

<style lang="scss">
//Reel2Bits Colour Plate

$brand-1: #313DF2;
$brand-2: #D100B7;

$shade-0:    #fff;
$shade-25:   #E7EDF7;
$shade-50:   #C8D1F4;
$shade-75:   #0E4F5F;
$shade-100:  #06161A;

//Redifining Bootstrap colours

$blue:    $brand-1;
$pink:    $brand-2;

$white:    $shade-0;
$gray-100: $shade-0;
$gray-200: $shade-25;
$gray-300: $shade-25;
$gray-400: $shade-25;
$gray-500: $shade-50;
$gray-600: $shade-50;
$gray-700: $shade-75;
$gray-800: $shade-75;
$gray-900: $shade-100;
$black:    $shade-100;

$primary:       $brand-1;
$secondary:     $brand-2;
$light:         $shade-0;
$dark:          $shade-100;

//Redifining Bootstrap typography

@import url('https://fonts.googleapis.com/css?family=Lato:400,900&display=swap');
$font-family-base:  'Lato', sans-serif;
$font-size-base:    0.875rem;
$font-weight-bold:  900;
$line-height-base:  1.3;
$h1-font-size:      $font-size-base * 2.29;
$h2-font-size:      $font-size-base * 1.71;
$h3-font-size:      $font-size-base * 1.43;
$headings-font-weight: 900;

//Redifining Bootstrap sizing and spacing

$navbar-brand-padding-y:  0;
$navbar-padding-y: 0;
$input-btn-padding-x: 1rem;
$input-btn-padding-y: .62rem;
$input-btn-padding-y-sm: .11rem;

$input-border-color: $shade-50;
$card-border-color:  $shade-25;

//Customizing grid

$grid-breakpoints: (
  xs: 0,
  sm: 576px,
  md: 768px,
  lg: 992px,
  xl: 1270px
);
$container-max-widths: (
  sm: 540px,
  md: 720px,
  lg: 960px,
  xl: 1200px
);
$grid-gutter-width: 24px;

//Import Required Bootstrap stuff

@import 'node_modules/bootstrap/scss/bootstrap';
@import 'node_modules/bootstrap-vue/src/index.scss';

//Custom stuff

//compensate navbar
body {
    padding-top: 80px;
}

.btn-play {
    width: 2.5rem;
    padding-left: .9rem;
}

.nav .nav-link.active {
    font-weight: $font-weight-bold;
    color: $shade-100;
    border-bottom: 4px $brand-2 solid;
}
#topsearch::placeholder::before {
    content: "HI";
    //box-sizing: border-box;
    //font-family: ForkAwesome;
}
#topsearch::placeholder {
    color: $brand-1;
}
#topsearch:placeholder-shown {
    text-align: center;
}
</style>

<script>
export default {
  name: 'App',
  computed: {
    currentUser () { return this.$store.state.users.currentUser },
    sitename () { return this.$store.state.instance.name }
  },
  methods: {
    logout () {
      this.$router.replace('/')
      this.$store.dispatch('logout')
    }
  }
}
</script>
