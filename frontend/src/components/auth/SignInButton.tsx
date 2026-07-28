// Sign-in / sign-out control for SPA per-user auth (MSAL).
//
// When signed in, the axios interceptor attaches the user's access token so the
// backend performs the On-Behalf-Of exchange and trims Azure AI Search results to
// that user's entitlements. When auth is not configured, nothing renders and the
// app keeps running in persona-simulation mode.
import { useMsal } from '@azure/msal-react'
import { authEnabled, loginRequest } from '@/auth/msalConfig'

export default function SignInButton() {
  const { instance, accounts } = useMsal()

  if (!authEnabled) return null

  const account = accounts[0]

  const signIn = async () => {
    const result = await instance.loginPopup(loginRequest)
    instance.setActiveAccount(result.account)
  }

  const signOut = async () => {
    await instance.logoutPopup({ account })
  }

  if (account) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 bg-surface-50 border border-border rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span className="text-xs text-gray-300" title={account.username}>
            {account.name ?? account.username}
          </span>
        </div>
        <button
          onClick={signOut}
          className="text-xs text-gray-400 hover:text-gray-200 underline underline-offset-2"
        >
          Sign out
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={signIn}
      className="text-xs font-medium bg-brand-gold/90 hover:bg-brand-gold text-black rounded-full px-3 py-1"
    >
      Sign in
    </button>
  )
}
