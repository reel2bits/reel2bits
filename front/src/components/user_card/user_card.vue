<template>
  <div class="card my-4">
    <div class="card-body py-3 px-3">
      <div class="d-flex mb-2">
        <div class="d-flex rounded-circle mr-2" style="width:96px; height:96px; overflow:hidden">
          <img :src="account.avatar" alt="user avatar" style="height:96px;">
        </div>
        <div class="align-self-center">
          <h2 class="h2 m-0">
            {{ account.name }}
          </h2>
          <p class="h3 font-weight-normal m-0">
            @{{ account.screen_name }} <button type="button" class="btn btn-primary btn-sm">
              Follow
            </button>
          </p>
          <p class="text-muted m-0">
            <!-- Follows you -->
          </p>
        </div>
      </div>
      <p class="card-text">
        {{ account.note }}
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
  ]
}

export default UserCard
</script>
