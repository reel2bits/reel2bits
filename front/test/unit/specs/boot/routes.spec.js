import routes from 'src/boot/routes'
import { createLocalVue } from '@vue/test-utils'
import VueRouter from 'vue-router'

const localVue = createLocalVue()
localVue.use(VueRouter)

describe('routes', () => {
  const router = new VueRouter({
    mode: 'abstract',
    routes: routes({})
  })

  it('root path', () => {
    router.push('/')
    expect(router.history.current.path).to.eql('/')
    // expect(router.getMatchedComponents('/')[0].name).to.eql('Home')
    // const matchedComponents = router.getMatchedComponents()
    // expect(matchedComponents[0].components.hasOwnProperty('Home')).to.eql(true)
  })
})
