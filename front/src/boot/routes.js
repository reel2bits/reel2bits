import PublicTimeline from '../components/public_timeline/public_timeline.vue'
import PublicAndExternalTimeline from '../components/public_and_external_timeline/public_and_external_timeline.vue'
import FriendsTimeline from '../components/friends_timeline/friends_timeline.vue'
import LoginForm from '../components/login_form/login_form.vue'
import Register from '../components/register/register.vue'
import OAuthCallback from '../components/oauth_callback/oauth_callback.vue'
import UserProfile from '../components/user_profile/user_profile.vue'
import UserFollowers from '../components/user_followers/user_followers.vue'
import UserFollowings from '../components/user_followings/user_followings.vue'
import UserSettings from '../components/user_settings/user_settings.vue'
import TracksUpload from '../views/tracks/Upload.vue'
import TracksShow from '../views/tracks/Show.vue'
import TracksEdit from '../views/tracks/Edit.vue'
import AlbumsNew from '../views/albums/New.vue'
import AlbumsShow from '../views/albums/Show.vue'
import AlbumsEdit from '../views/albums/Edit.vue'
import AccountLogs from '../views/account/Logs.vue'
import AccountQuota from '../views/account/Quota.vue'
import About from '../views/About.vue'
import NotFound from '../views/NotFound.vue'
import PasswordReset from '../components/password_reset/password_reset.vue'
import PasswordResetToken from '../components/password_reset_token/password_reset_token.vue'

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
    {
      name: 'home',
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
    { name: 'password-reset', path: '/password-reset', component: PasswordReset },
    { name: 'password-reset-token', path: '/password-reset/:token', component: PasswordResetToken },
    { name: 'oauth-callback', path: '/oauth-callback', component: OAuthCallback, props: (route) => ({ code: route.query.code }) },
    // External user profile (remote)
    { name: 'external-user-profile', path: '/users/:id', component: UserProfile },
    { name: 'external-user-profile-tracks', path: '/users/:id/tracks', component: UserProfile },
    { name: 'external-user-profile-albums', path: '/users/:id/albums', component: UserProfile },
    { name: 'external-user-profile-drafts', path: '/users/:id/drafts', component: UserProfile },
    { name: 'external-user-profile-followers', path: '/users/:id/followers', component: UserFollowers },
    { name: 'external-user-profile-followings', path: '/users/:id/followings', component: UserFollowings },
    { name: 'external-tracks-show', path: '/users/:id/track/:trackId', component: TracksShow },
    { name: 'external-albums-show', path: '/users/:id/album/:albumId', component: AlbumsShow },
    // Internal user profile (local)
    { name: 'user-profile', path: '/(users/)?:name', component: UserProfile },
    { name: 'user-profile-tracks', path: '/(users/)?:name/tracks', component: UserProfile },
    { name: 'user-profile-albums', path: '/(users/)?:name/albums', component: UserProfile },
    { name: 'user-profile-drafts', path: '/(users/)?:name/drafts', component: UserProfile },
    { name: 'user-profile-unprocessed', path: '/(users/)?:name/unprocessed', component: UserProfile },
    { name: 'user-profile-followers', path: '/(users/)?:name/followers', component: UserFollowers },
    { name: 'user-profile-followings', path: '/(users/)?:name/followings', component: UserFollowings },
    { name: 'user-settings', path: '/account/settings', component: UserSettings, beforeEnter: validateAuthenticatedRoute },
    // Tracks
    { name: 'tracks-upload', path: '/tracks/upload', component: TracksUpload, beforeEnter: validateAuthenticatedRoute },
    { name: 'tracks-show', path: '/:username/track/:trackId', component: TracksShow },
    { name: 'tracks-edit', path: '/:username/track/:trackId/edit', component: TracksEdit, beforeEnter: validateAuthenticatedRoute },
    // Albums
    { name: 'albums-new', path: '/albums/new', component: AlbumsNew, beforeEnter: validateAuthenticatedRoute },
    { name: 'albums-show', path: '/:username/album/:albumId', component: AlbumsShow },
    { name: 'albums-edit', path: '/:username/album/:albumId/edit', component: AlbumsEdit, beforeEnter: validateAuthenticatedRoute },
    // Account
    { name: 'account-logs', path: '/account/logs', component: AccountLogs, beforeEnter: validateAuthenticatedRoute },
    { name: 'account-quota', path: '/account/quota', component: AccountQuota, beforeEnter: validateAuthenticatedRoute },
    // Always last
    { path: '*', component: NotFound }
  ]
}
