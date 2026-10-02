import RoadIllustration from './RoadIllustration'
import { LogoMark } from './Icons'

export default function AuthLayout({ eyebrow, title, subtitle, children }) {
  return (
    <div className="auth-shell">
      <div className="auth-visual">
        <div className="auth-visual__brand">
          <LogoMark className="auth-visual__mark" />
          <span>CiviSense</span>
        </div>
        <RoadIllustration className="auth-visual__art" />
        <div className="auth-visual__copy">
          <p>{eyebrow}</p>
          <h2>Report it once. We'll route it to the right desk.</h2>
        </div>
      </div>

      <div className="auth-form-panel">
        <div className="auth-form-panel__inner">
          <h1>{title}</h1>
          {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  )
}
