// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

const fetchUser = (attempt, user, store) => new Promise((resolve, reject) => {
  setTimeout(() => {
    store.state.api.backendInteractor.fetchUser({ id: user.id })
      .then((user) => store.commit('addNewUsers', [user]))
      .then(() => resolve([user.following, user.requested, user.locked, attempt]))
      .catch((e) => reject(e))
  }, 500)
}).then(([following, sent, locked, attempt]) => {
  if (!following && !(locked && sent) && attempt <= 3) {
    // If we BE reports that we still not following that user - retry,
    // increment attempts by one
    return fetchUser(++attempt, user, store)
  } else {
    // If we run out of attempts, just return whatever status is.
    return sent
  }
})

export const requestFollow = (user, store) => new Promise((resolve, reject) => {
  store.state.api.backendInteractor.followUser(user.id)
    .then((updated) => {
      store.commit('updateUserRelationship', [updated])

      if (updated.following || (user.locked && user.requested)) {
        // If we get result immediately or the account is locked, just stop.
        resolve({ sent: updated.requested })
        return
      }

      // But usually we don't get result immediately, so we ask server
      // for updated user profile to confirm if we are following them
      // Sometimes it takes several tries. Sometimes we end up not following
      // user anyway, probably because they locked themselves and we
      // don't know that yet.
      // Recursive Promise, it will call itself up to 3 times.

      return fetchUser(1, user, store)
        .then((sent) => {
          resolve({ sent })
        })
    })
})

export const requestUnfollow = (user, store) => new Promise((resolve, reject) => {
  store.state.api.backendInteractor.unfollowUser(user.id)
    .then((updated) => {
      store.commit('updateUserRelationship', [updated])
      resolve({
        updated
      })
    })
})
