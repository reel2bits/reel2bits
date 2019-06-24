import { set, delete as del } from 'vue'

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
        set(state.settings, 'currentSaveStateNotice', { error: false, data: success })
        set(state.settings, 'noticeClearTimeout',
          setTimeout(() => del(state.settings, 'currentSaveStateNotice'), 2000))
      } else {
        set(state.settings, 'currentSaveStateNotice', { error: true, errorData: error })
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
