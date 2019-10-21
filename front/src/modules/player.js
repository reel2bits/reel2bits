const defaultState = {
  track: null,
  isPlaying: null
}

const playerMod = {
  state: defaultState,
  mutations: {
    playerStartedPlaying (state, track) {
      state.isPlaying = true
      state.track = track
    },
    playerStoppedPlaying (state) {
      state.isPlaying = false
    }
  },
  actions: {
  }
}

export default playerMod
