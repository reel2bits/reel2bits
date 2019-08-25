import { cloneDeep } from 'lodash'

import { defaultState, mutations, getters } from '../../../../src/modules/users.js'

describe('The users module', () => {
  describe('mutations', () => {
    it('adds new users to the set, merging in new information for old users', () => {
      const state = cloneDeep(defaultState)
      const user = { id: '1', name: 'Guy' }
      const modUser = { id: '1', name: 'Dude' }

      mutations.addNewUsers(state, [user])
      expect(state.users).to.have.length(1)
      expect(state.users).to.eql([user])

      mutations.addNewUsers(state, [modUser])
      expect(state.users).to.have.length(1)
      expect(state.users).to.eql([user])
      expect(state.users[0].name).to.eql('Dude')
    })
  })

  describe('findUser', () => {
    it('returns user with matching screen_name', () => {
      const user = { screen_name: 'Guy', id: '1' }
      const state = {
        usersObject: {
          1: user,
          guy: user
        }
      }
      const name = 'Guy'
      const expected = { screen_name: 'Guy', id: '1' }
      expect(getters.findUser(state)(name)).to.eql(expected)
    })

    it('returns user with matching id', () => {
      const user = { screen_name: 'Guy', id: '1' }
      const state = {
        usersObject: {
          1: user,
          guy: user
        }
      }
      const id = '1'
      const expected = { screen_name: 'Guy', id: '1' }
      expect(getters.findUser(state)(id)).to.eql(expected)
    })
  })
})
