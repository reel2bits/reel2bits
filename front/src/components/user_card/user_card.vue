<template>
  <div class="card my-4">
    <div class="card-body py-3 px-3">
      <div class="d-flex mb-2">
        <div class="d-flex rounded-circle mr-2" style="width:96px; height:96px; overflow:hidden">
          <img :src="user.profile_image_url" :alt="userAvatarAlt" style="height:96px;">
        </div>
        <div class="align-self-center">
          <h2 class="h2 m-0">
            <b-link :to="{ name: 'user-profile', params: { name: user.screen_name } }" class="text-decoration-none text-body">
              {{ user.name }}
            </b-link>
          </h2>
          <p class="h3 font-weight-normal m-0">
            <b-link :to="{ name: 'user-profile', params: { name: user.screen_name } }" class="text-decoration-none text-body">
              @{{ user.screen_name }}
            </b-link>
          </p>
          <div v-if="isOtherUser && loggedIn">
            <b-button v-if="!user.following" type="button" variant="primary"
                      size="sm" :disabled="followRequestInProgress" @click="followUser"
            >
              <template v-if="followRequestInProgress">
                <translate translate-context="Content/UserCard/Button/Follow/in progress">
                  Follow in progress
                </translate>
              </template>
              <template v-else-if="followRequestSent">
                <translate translate-context="Content/UserCard/Button/Follow/sent">
                  Follow sent
                </translate>
              </template>
              <template v-else>
                <translate translate-context="Content/UserCard/Button/Follow">
                  Follow
                </translate>
              </template>
            </b-button>
            <b-button v-else-if="followRequestInProgress" type="button" variant="primary"
                      size="sm" disabled @click="unfollowUser"
            >
              <translate translate-context="Content/UserCard/Button/Follow/change in progress">
                Change in progress
              </translate>
            </b-button>
            <b-button v-else type="button" variant="primary"
                      size="sm" @click="unfollowUser"
            >
              <translate translate-context="Content/UserCard/Button/Unfollow">
                Unfollow
              </translate>
            </b-button>
          </div>
          <p class="text-muted m-0">
            <template v-if="user.follows_you && loggedIn && isOtherUser">
              <translate translate-context="Content/UserCard/Text/Follows you">
                Follows you
              </translate>
            </template>
          </p>
        </div>
      </div>
      <p class="card-text">
        {{ user.description }}
      </p>
      <ul class="nav nav-fill">
        <li class="nav-item border-right">
          <router-link :to="{ name: 'user-profile-tracks', params: { name: user.screen_name } }">
            <p class="h3 font-weight-normal m-0">
              {{ user.statuses_count }}
            </p><p class="m-0">
              <translate translate-context="Content/UserCard/Text/Tracks (number of)">
                Tracks
              </translate>
            </p>
          </router-link>
        </li>
        <li class="nav-item border-right">
          <router-link :to="{ name: 'user-profile-albums', params: { name: user.screen_name } }">
            <p class="h3 font-weight-normal m-0">
              {{ user.reel2bits.albums_count }}
            </p><p class="m-0">
              <translate translate-context="Content/UserCard/Text/Albums (number of)">
                Albums
              </translate>
            </p>
          </router-link>
        </li>
        <li class="nav-item border-right">
          <router-link :to="{ name: 'user-profile-followers', params: { name: user.screen_name } }">
            <p class="h3 font-weight-normal m-0">
              {{ user.followers_count }}
            </p><p class="m-0">
              <translate translate-context="Content/UserCard/Text/Followers (number of)">
                Followers
              </translate>
            </p>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link :to="{ name: 'user-profile-followings', params: { name: user.screen_name } }">
            <p class="h3 font-weight-normal m-0">
              {{ user.friends_count }}
            </p><p class="m-0">
              <translate translate-context="Content/UserCard/Text/Following (number of)">
                Following
              </translate>
            </p>
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { requestFollow, requestUnfollow } from '../../services/follow_manipulate/follow_manipulate.js'
const UserCard = {
  props: [
    'user'
  ],
  data: () => ({
    followRequestInProgress: false,
    followRequestSent: false
  }),
  computed: {
    isOtherUser () {
      return this.user.id !== this.$store.state.users.currentUser.id
    },
    loggedIn () {
      return this.$store.state.users.currentUser
    },
    userAvatarAlt () {
      let msg = this.$pgettext('Content/UserCard/Image/Avatar alt', '%{username} avatar')
      return this.$gettextInterpolate(msg, { username: this.user.screen_name })
    }
  },
  created () {
    this.$store.dispatch('fetchUserRelationship', this.user.id)
  },
  methods: {
    followUser () {
      const store = this.$store
      this.followRequestInProgress = true
      requestFollow(this.user, store).then(({ sent }) => {
        this.followRequestInProgress = false
        this.followRequestSent = sent
      })
    },
    unfollowUser () {
      const store = this.$store
      this.followRequestInProgress = true
      requestUnfollow(this.user, store).then(() => {
        this.followRequestInProgress = false
      })
    }
  }
}

export default UserCard
</script>
