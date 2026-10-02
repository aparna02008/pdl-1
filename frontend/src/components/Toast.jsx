import { useEffect, useState } from 'react'
import { IconCheck, IconAlert } from './Icons'

export default function Toast({ toast, onDismiss }) {
  const [leaving, setLeaving] = useState(false)

  useEffect(() => {
    if (!toast) return
    const dismissTimer = setTimeout(() => setLeaving(true), 3400)
    const removeTimer = setTimeout(() => onDismiss(), 3800)
    return () => { clearTimeout(dismissTimer); clearTimeout(removeTimer) }
  }, [toast, onDismiss])

  if (!toast) return null

  return (
    <div className={'toast' + (leaving ? ' toast--leaving' : '')} role="status">
      {toast.type === 'success' ? <IconCheck width={16} height={16} /> : <IconAlert width={16} height={16} />}
      <span>{toast.message}</span>
    </div>
  )
}
