<template>
  <div class="card my-4">
    <div class="card-body py-3 px-3">
      <div class="d-flex mb-2">
        <div class="d-flex rounded-circle mr-2" style="width:96px; height:96px; overflow:hidden">
          <img :src="user.profile_image_url" alt="user avatar" style="height:96px;">
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
            </b-link> <b-button v-if="!user.following" type="button" variant="primary"
                                size="sm" :disabled="followRequestInProgress" @click="followUser"
            >
              Follow
            </b-button>
            <b-button v-else-if="followRequestInProgress" type="button" variant="primary"
                      size="sm" disabled @click="unfollowUser"
            >
              Follow in progress
            </b-button>
            <b-button v-else type="button" variant="primary"
                      size="sm" @click="unfollowUser"
            >
              Unfollow
            </b-button>
          </p>
          <p class="text-muted m-0">
            <template v-if="user.follows_you && loggedIn && isOtherUser">
              Follows you
            </template>
          </p>
        </div>
      </div>
      <p class="card-text">
        {{ user.description }}
      </p>
      <ul class="nav nav-fill">
        <li class="nav-item border-right">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ user.statuses_count }}</p><p class="m-0">Tracks</p></a>
        </li>
        <li class="nav-item border-right">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ user.reel2bits.albums_count }}</p><p class="m-0">Albums</p></a>
        </li>
        <li class="nav-item border-right">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ user.followers_count }}</p><p class="m-0">Followers</p></a>
        </li>
        <li class="nav-item">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ user.friends_count }}</p><p class="m-0">Following</p></a>
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
        store.commit('removeStatus', { timeline: 'friends', userId: this.user.id })
      })
    }
  }
}

export default UserCard
</script>
