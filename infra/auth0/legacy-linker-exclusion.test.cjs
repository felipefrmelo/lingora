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

test('MCP exclusion requires both the approved client and the Lingora resource', () => {
  const event = { client: { client_id: 'chatgpt' }, resource_server: { identifier: 'https://mcp.example/mcp' }, user: {}, secrets: { LINGORA_MCP_RESOURCE_URL: 'https://mcp.example/mcp', LINGORA_MCP_CLIENT_IDS: 'chatgpt' } }
  assert.equal(skipLegacyLinking(event, 'lingora'), true)
  event.secrets.LINGORA_MCP_RESOURCE_URL = 'https://other.example/mcp'
  assert.equal(skipLegacyLinking(event, 'lingora'), false)
  event.secrets.LINGORA_MCP_RESOURCE_URL = 'https://mcp.example/mcp'
  event.secrets.LINGORA_MCP_CLIENT_IDS = 'other'
  assert.equal(skipLegacyLinking(event, 'lingora'), false)
})
