import { useEffect, useRef, useState } from 'react'
import { IconBell, IconChevronDown } from './Icons'
import { useAuth } from '../auth/AuthContext'

export default function Topbar() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  const initials = user?.name
    ? user.name.trim().split(/\s+/).slice(0, 2).map((w) => w[0].toUpperCase()).join('')
    : '?'

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <header className="topbar">
      <button type="button" className="topbar__bell" aria-label="Notifications">
        <IconBell width={19} height={19} />
      </button>

      <div className="topbar__user" ref={ref}>
        <button type="button" className="topbar__user-btn" onClick={() => setOpen((v) => !v)}>
          <span className="topbar__avatar">{initials}</span>
          <span className="topbar__name">{user?.name || 'Account'}</span>
          <IconChevronDown width={14} height={14} />
        </button>

        {open && (
          <div className="topbar__menu">
            <div className="topbar__menu-email">{user?.email}</div>
            <button type="button" className="topbar__menu-item" onClick={logout}>
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
