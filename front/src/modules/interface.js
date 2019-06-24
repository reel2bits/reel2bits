import vue from 'vue'

const defaultState = {
  settings: {
    currentSaveStateNotice: null,
    noticeClearTimeout: null
  }
}

const interfaceMod = {
  state: defaultState,
  mutations: {
    settingsSaved (state, { success, error }) {
      if (success) {
        if (state.noticeClearTimeout) {
          clearTimeout(state.noticeClearTimeout)
        }
        vue.set(state.settings, 'currentSaveStateNotice', { error: false, data: success })
        vue.set(state.settings, 'noticeClearTimeout',
          setTimeout(() => vue.delete(state.settings, 'currentSaveStateNotice'), 2000))
      } else {
        vue.set(state.settings, 'currentSaveStateNotice', { error: true, errorData: error })
      }
    }
  },
  actions: {
    setPageTitle ({ rootState }, option = '') {
      document.title = `${option} ${rootState.instance.name}`
    },
    settingsSaved ({ commit, dispatch }, { success, error }) {
      commit('settingsSaved', { success, error })
    }
  }
}

export default interfaceMod
