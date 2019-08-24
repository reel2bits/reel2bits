import Home from '../views/Home.vue'
import LoginForm from '../components/login_form/login_form.vue'
import Register from '../components/register/register.vue'
import OAuthCallback from '../components/oauth_callback/oauth_callback.vue'
import UserProfile from '../components/user_profile/user_profile.vue'
import TracksUpload from '../views/tracks/Upload.vue'
import TracksShow from '../views/tracks/Show.vue'
import AlbumsNew from '../views/albums/New.vue'
import AlbumsShow from '../views/albums/Show.vue'
import AccountLogs from '../views/account/Logs.vue'

export default (store) => {
  const validateAuthenticatedRoute = (to, from, next) => {
    if (store.state.users.currentUser) {
      next()
    } else {
      next('/')
    }
  }

  return [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/about',
      name: 'about',
      component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
    },
    {
      name: 'profile',
      path: '/profile',
      component: () => import(/* webpackChunkName: "profile" */ '../views/Profile.vue')
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
      beforeEnter: validateAuthenticatedRoute
    },
    {
      name: 'tracks-show',
      path: '/users/:username/track/:trackId',
      component: TracksShow
    },
    // Albums
    {
      name: 'albums-new',
      path: '/albums/new',
      component: AlbumsNew,
      beforeEnter: validateAuthenticatedRoute
    },
    {
      name: 'albums-show',
      path: '/users/:username/album/:albumId',
      component: AlbumsShow
    },
    // Account
    {
      name: 'account-logs',
      path: '/account/logs',
      component: AccountLogs,
      beforeEnter: validateAuthenticatedRoute
    }
  ]
}
