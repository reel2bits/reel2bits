const defaultState = {}

const interfaceMod = {
  state: defaultState,
  mutations: {

  },
  actions: {
    setPageTitle ({ rootState }, option = '') {
      document.title = `${option} ${rootState.instance.name}`
    }
  }
}

export default interfaceMod
