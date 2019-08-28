import { parseUser } from '../../../../../src/services/entity_normalizer/entity_normalizer.service.js'

const makeMockUserMasto = (overrides = {}) => {
  return Object.assign({
    acct: 'hj',
    avatar:
    'https://shigusegubu.club/media/1657b945-8d5b-4ce6-aafb-4c3fc5772120/8ce851029af84d55de9164e30cc7f46d60cbf12eee7e96c5c0d35d9038ddade1.png',
    avatar_static:
    'https://shigusegubu.club/media/1657b945-8d5b-4ce6-aafb-4c3fc5772120/8ce851029af84d55de9164e30cc7f46d60cbf12eee7e96c5c0d35d9038ddade1.png',
    bot: false,
    created_at: '2017-12-17T21:54:14.000Z',
    display_name: 'whatever whatever whatever witch',
    emojis: [],
    fields: [],
    followers_count: 705,
    following_count: 326,
    header:
    'https://shigusegubu.club/media/7ab024d9-2a8a-4fbc-9ce8-da06756ae2db/6aadefe4e264133bc377ab450e6b045b6f5458542a5c59e6c741f86107f0388b.png',
    header_static:
    'https://shigusegubu.club/media/7ab024d9-2a8a-4fbc-9ce8-da06756ae2db/6aadefe4e264133bc377ab450e6b045b6f5458542a5c59e6c741f86107f0388b.png',
    id: '1',
    locked: false,
    note:
    'Volatile Internet Weirdo. Name pronounced as Hee Jay. JS and Java dark arts mage, Elixir trainee. I love sampo and lain. Matrix is <span><a data-user="1" href="https://shigusegubu.club/users/hj">@<span>hj</span></a></span>:matrix.heldscal.la Pronouns are whatever. Do not DM me unless it\'s truly private matter and you\'re instance\'s admin or you risk your DM to be reposted publicly.Wish i was Finnish girl.',
    pleroma: { confirmation_pending: false, tags: null },
    reel2bits: { albums_count: 42 },
    source: { note: '', privacy: 'public', sensitive: false },
    statuses_count: 41775,
    url: 'https://shigusegubu.club/users/hj',
    username: 'hj'
  }, overrides)
}

describe('API Entities normalizer', () => {
  // Statuses generally already contain some info regarding users and there's nearly 1:1 mapping, so very little to test
  describe('parseUsers (MastoAPI)', () => {
    it('sets correct is_local for users depending on their screen_name', () => {
      const local = makeMockUserMasto({ acct: 'foo' })
      const remote = makeMockUserMasto({ acct: 'foo@bar.baz' })

      expect(parseUser(local)).to.have.property('is_local', true)
      expect(parseUser(remote)).to.have.property('is_local', false)
    })
  })
})
