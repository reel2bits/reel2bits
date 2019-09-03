<template>
  <div class="card my-4">
    <div class="card-body py-3 px-3">
      <div class="d-flex mb-2">
        <div class="d-flex rounded-circle mr-2" style="width:96px; height:96px; overflow:hidden">
          <img :src="account.profile_image_url" alt="user avatar" style="height:96px;">
        </div>
        <div class="align-self-center">
          <h2 class="h2 m-0">
            <b-link :to="{ name: 'user-profile', params: { name: account.screen_name } }" class="text-decoration-none text-body">
              {{ account.name }}
            </b-link>
          </h2>
          <p class="h3 font-weight-normal m-0">
            <b-link :to="{ name: 'user-profile', params: { name: account.screen_name } }" class="text-decoration-none text-body">
              @{{ account.screen_name }}
            </b-link> <button type="button" class="btn btn-primary btn-sm">
              Follow
            </button>
          </p>
          <p class="text-muted m-0">
            <!-- Follows you -->
          </p>
        </div>
      </div>
      <p class="card-text">
        {{ account.description }}
      </p>
      <ul class="nav nav-fill">
        <li class="nav-item border-right">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ account.statuses_count }}</p><p class="m-0">Tracks</p></a>
        </li>
        <li class="nav-item border-right">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ account.reel2bits.albums_count }}</p><p class="m-0">Albums</p></a>
        </li>
        <li class="nav-item border-right">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ account.followers_count }}</p><p class="m-0">Followers</p></a>
        </li>
        <li class="nav-item">
          <a class="nav-link px-2" href="#"><p class="h3 font-weight-normal m-0">{{ account.friends_count }}</p><p class="m-0">Following</p></a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
const UserCard = {
  props: [
    'account'
  ],
  computed: {
    isOtherUser () {
      return this.user.id !== this.$store.state.users.currentUser.id
    }
  }
}

export default UserCard
</script>
