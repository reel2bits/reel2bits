import PublicTimeline from '../components/public_timeline/public_timeline.vue'
import PublicAndExternalTimeline from '../components/public_and_external_timeline/public_and_external_timeline.vue'
import FriendsTimeline from '../components/friends_timeline/friends_timeline.vue'
import LoginForm from '../components/login_form/login_form.vue'
import Register from '../components/register/register.vue'
import OAuthCallback from '../components/oauth_callback/oauth_callback.vue'
import UserProfile from '../components/user_profile/user_profile.vue'
import TracksUpload from '../views/tracks/Upload.vue'
import TracksShow from '../views/tracks/Show.vue'
import AlbumsNew from '../views/albums/New.vue'
import AlbumsShow from '../views/albums/Show.vue'
import AccountLogs from '../views/account/Logs.vue'
import About from '../views/About.vue'
import NotFound from '../views/NotFound.vue'

export default (store) => {
  const validateAuthenticatedRoute = (to, from, next) => {
    if (store.state.users.currentUser) {
      next()
    } else {
      next('/')
    }
  }

  // On new routes, don't forget to update utile.py::forbidden_username list
  return [
    { name: 'home',
      path: '/',
      redirect: _to => {
        return (store.state.users.currentUser
          ? store.state.instance.redirectRootLogin
          : store.state.instance.redirectRootNoLogin) || '/main/all'
      }
    },
    { name: 'public-external-timeline', path: '/main/all', component: PublicAndExternalTimeline },
    { name: 'public-timeline', path: '/main/public', component: PublicTimeline },
    { name: 'friends', path: '/main/friends', component: FriendsTimeline, beforeEnter: validateAuthenticatedRoute },
    { path: '/about', name: 'about', component: About },
    { path: '/login', name: 'login_form', component: LoginForm },
    { path: '/register', name: 'register', component: Register },
    { name: 'oauth-callback', path: '/oauth-callback', component: OAuthCallback, props: (route) => ({ code: route.query.code }) },
    { name: 'external-user-profile', path: '/users/:id', component: UserProfile },
    { name: 'user-profile', path: '/(users/)?:name', component: UserProfile },
    // Tracks
    { name: 'tracks-upload', path: '/tracks/upload', component: TracksUpload, beforeEnter: validateAuthenticatedRoute },
    { name: 'tracks-show', path: '/:username/:trackId', component: TracksShow },
    // Albums
    { name: 'albums-new', path: '/albums/new', component: AlbumsNew, beforeEnter: validateAuthenticatedRoute },
    { name: 'albums-show', path: '/users/:username/album/:albumId', component: AlbumsShow },
    // Account
    { name: 'account-logs', path: '/account/logs', component: AccountLogs, beforeEnter: validateAuthenticatedRoute },
    // Always last
    { path: '*', component: NotFound }
  ]
}
