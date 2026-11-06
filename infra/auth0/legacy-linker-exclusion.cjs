// Copy these helpers into the existing account-linking Action before its handler.
// They contain no credentials and preserve the original behavior for unrelated users.
const LINGORA_DATABASE_CONNECTION = 'Lingora-Users-Development'

function isLingoraAccount(user) {
  return Array.isArray(user?.identities) && user.identities.some(
    (identity) => identity.connection === LINGORA_DATABASE_CONNECTION,
  )
}

function skipLegacyLinking(event, lingoraClientId) {
  const clients = (event.secrets?.LINGORA_MCP_CLIENT_IDS || '').split(',').map(x => x.trim()).filter(Boolean)
  const resource = event.secrets?.LINGORA_MCP_RESOURCE_URL
  const lingoraMcp = Boolean(resource && event.resource_server?.identifier === resource && clients.includes(event.client?.client_id))
  return lingoraMcp || Boolean(lingoraClientId && event.client?.client_id === lingoraClientId)
    || event.connection?.name === LINGORA_DATABASE_CONNECTION
    || isLingoraAccount(event.user)
}

module.exports = { isLingoraAccount, skipLegacyLinking }
