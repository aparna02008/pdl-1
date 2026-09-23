import { NavLink } from 'react-router-dom'
import { LogoMark, IconReport, IconList } from './Icons'

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__mark">
        <LogoMark className="sidebar__mark-glyph" />
        <span className="sidebar__mark-text">CiviSense</span>
      </div>

      <nav className="sidebar__nav">
        <NavLink
          to="/report"
          className={({ isActive }) => 'sidebar__link' + (isActive ? ' is-active' : '')}
        >
          <IconReport width={18} height={18} />
          Report an issue
        </NavLink>
        <NavLink
          to="/complaints"
          className={({ isActive }) => 'sidebar__link' + (isActive ? ' is-active' : '')}
        >
          <IconList width={18} height={18} />
          My complaints
        </NavLink>
      </nav>

      <div className="sidebar__footer">
        CiviSense · civic issue reporting
      </div>
    </aside>
  )
}
