import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import LoginForm from './components/login_form/login_form.vue'
import Register from './components/register/register.vue'
import OAuthCallback from './components/oauth_callback/oauth_callback.vue'
import UserProfile from './components/user_profile/user_profile.vue'
import TracksUpload from './views/tracks/Upload.vue'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/about',
      name: 'about',
      component: () => import(/* webpackChunkName: "about" */ './views/About.vue')
    },
    {
      name: 'profile',
      path: '/profile',
      component: () => import(/* webpackChunkName: "profile" */ './views/Profile.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login_form',
      component: LoginForm
    },
    {
      path: '/register',
      name: 'register',
      component: Register
    },
    {
      name: 'oauth-callback',
      path: '/oauth-callback',
      component: OAuthCallback,
      props: (route) => ({ code: route.query.code })
    },
    {
      name: 'external-user-profile',
      path: '/users/:id',
      component: UserProfile
    },
    {
      name: 'user-profile',
      path: '/(users/)?:name',
      component: UserProfile
    },
    // Tracks
    {
      name: 'tracks-upload',
      path: '/tracks/upload',
      component: TracksUpload,
      meta: { requiresAuth: true }
    }
  ]
})

export default router
