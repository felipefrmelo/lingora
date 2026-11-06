/** Apply verification only to Lingora's SPA and approved MCP resource/client pairs. */
exports.onExecutePostLogin = async (event, api) => {
  const client = event.client?.client_id
  const spa = Boolean(event.secrets.LINGORA_CLIENT_ID && client === event.secrets.LINGORA_CLIENT_ID)
  const mcpClients = (event.secrets.LINGORA_MCP_CLIENT_IDS || '').split(',').map(x => x.trim()).filter(Boolean)
  const mcp = Boolean(event.secrets.LINGORA_MCP_RESOURCE_URL &&
    event.resource_server?.identifier === event.secrets.LINGORA_MCP_RESOURCE_URL && mcpClients.includes(client))
  if (!spa && !mcp) return
  if (event.user.email_verified !== true) {
    api.access.deny('lingora_email_verification_required')
    return
  }
  api.accessToken.setCustomClaim('https://lingora.local/api/email_verified', true)
}
