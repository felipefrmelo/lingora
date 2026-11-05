/** Scope this Post-Login Action to the dedicated Lingora SPA only. */
exports.onExecutePostLogin = async (event, api) => {
  if (!event.secrets.LINGORA_CLIENT_ID || event.client.client_id !== event.secrets.LINGORA_CLIENT_ID) return
  if (event.user.email_verified !== true) {
    api.access.deny('lingora_email_verification_required')
    return
  }
  api.accessToken.setCustomClaim('https://lingora.local/api/email_verified', true)
}
