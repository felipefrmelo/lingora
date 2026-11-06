# Exclude Lingora from the existing automatic account linker

The existing tenant's active Post Login flow starts with an `account linking` Action. Inspection of its deployed editor showed that it looks up users by email, keeps other verified users, selects the oldest account, and links identities. This conflicts with Lingora's explicit-account-linking policy.

Apply only after approval of the shared Action change. Preserve the current version and all existing statements; do not rewrite the legacy Action or change other applications' behavior.

1. Copy the constant and helper functions from `legacy-linker-exclusion.cjs` into the Action, without the `module.exports` line.
2. Add `LINGORA_CLIENT_ID` to this Action's configuration using the dedicated SPA's public client ID. This value is a public identifier, not a client secret.
3. At the start of its existing `onExecutePostLogin` handler, before `try`, insert:

```js
if (skipLegacyLinking(event, event.secrets.LINGORA_CLIENT_ID)) return
```

4. Extend its existing `others` candidate filter, preserving both current conditions:

```js
const others = matches.filter(
  (u) => u.user_id !== event.user.user_id && u.email_verified && !isLingoraAccount(u)
)
```

The candidate exclusion matters: skipping only the Lingora client would still let another tenant application automatically link a new Lingora database identity later. Existing users outside Lingora retain the same selection and linking logic. Do not unlink or modify already-linked Auth0 accounts.

## MCP extension (prepared; not yet deployed)

For the dedicated MCP API, provide the exact MCP resource URL and comma-separated approved Auth0 client IDs as `LINGORA_MCP_RESOURCE_URL` and `LINGORA_MCP_CLIENT_IDS`. The new helper skips linking only when **both** the resource and the client match. Preserve the existing SPA/database/candidate exclusions and unrelated linking behavior. Apply the same two values to the verification Action, which uses the same pair check and keeps the existing verified-email claim. Keep the existing handler invocation unchanged; the helper reads these values from `event.secrets`.

Inspect and back up the currently deployed Action before applying this change. Do not grant a client access until both Actions are deployed and tested. Adding a ChatGPT client ID without checking the target resource would affect other applications in this shared tenant.
