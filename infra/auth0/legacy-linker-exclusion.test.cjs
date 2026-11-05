const { test } = require('node:test')
const assert = require('node:assert/strict')
const { isLingoraAccount, skipLegacyLinking } = require('./legacy-linker-exclusion.cjs')

test('the Lingora client never invokes legacy automatic linking', () => {
  assert.equal(skipLegacyLinking({ client: { client_id: 'lingora' }, user: {} }, 'lingora'), true)
})
test('Lingora database users are excluded even through another client', () => {
  const user = { identities: [{ connection: 'Lingora-Users-Development' }] }
  assert.equal(isLingoraAccount(user), true)
  assert.equal(skipLegacyLinking({ client: { client_id: 'other' }, user }, 'lingora'), true)
})
test('Lingora database connections are excluded before matching by email', () => {
  assert.equal(skipLegacyLinking({ connection: { name: 'Lingora-Users-Development' }, user: {} }, 'lingora'), true)
})
test('unrelated existing accounts keep their legacy linking behavior', () => {
  const event = { client: { client_id: 'other' }, connection: { name: 'Username-Password-Authentication' }, user: { identities: [{ connection: 'google-oauth2' }] } }
  assert.equal(skipLegacyLinking(event, 'lingora'), false)
  assert.equal(isLingoraAccount(event.user), false)
})
