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

test('only an approved MCP client targeting the Lingora resource is verified', async () => {
  const resource = 'https://mcp.example/mcp'
  const f = fixture('mcp-client', true)
  Object.assign(f.event.secrets, { LINGORA_MCP_CLIENT_IDS: 'mcp-client', LINGORA_MCP_RESOURCE_URL: resource })
  f.event.resource_server = { identifier: resource }
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [['claim', 'https://lingora.local/api/email_verified', true]])
  f.calls.length = 0
  f.event.resource_server.identifier = 'https://unrelated.example/mcp'
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [])
  f.event.resource_server.identifier = resource
  f.event.client.client_id = 'other-client'
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [])
})
test('unverified MCP logins are denied', async () => {
  const f = fixture('mcp-client', false)
  Object.assign(f.event.secrets, { LINGORA_MCP_CLIENT_IDS: 'mcp-client', LINGORA_MCP_RESOURCE_URL: 'https://mcp.example/mcp' })
  f.event.resource_server = { identifier: 'https://mcp.example/mcp' }
  await onExecutePostLogin(f.event, f.api)
  assert.deepEqual(f.calls, [['deny', 'lingora_email_verification_required']])
})
