const { test } = require('node:test')
const assert = require('node:assert/strict')
const { onExecutePostLogin } = require('./require-verified-email.js')

function fixture(clientId, verified, secret = 'lingora-spa') {
  const calls = []
  return {
    event: { client: { client_id: clientId }, user: { email_verified: verified }, secrets: { LINGORA_CLIENT_ID: secret } },
    api: { access: { deny: (reason) => calls.push(['deny', reason]) }, accessToken: { setCustomClaim: (...args) => calls.push(['claim', ...args]) } },
    calls,
  }
}

test('other tenant applications are unaffected', async () => {
  const f = fixture('another-app', false)
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [])
})
test('unverified Lingora users cannot obtain the verified claim', async () => {
  const f = fixture('lingora-spa', false)
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [['deny', 'lingora_email_verification_required']])
})
test('verified Lingora users receive the required namespaced claim', async () => {
  const f = fixture('lingora-spa', true)
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [['claim', 'https://lingora.local/api/email_verified', true]])
})
test('an unconfigured Action grants no verified claim', async () => {
  const f = fixture('lingora-spa', true, '')
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [])
})
