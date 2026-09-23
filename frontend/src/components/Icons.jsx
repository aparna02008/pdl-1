// Small, hand-drawn icon set. Kept as one file so the visual language
// (1.6 stroke weight, rounded joins, 20px grid) stays consistent everywhere.
const base = {
  width: 20,
  height: 20,
  viewBox: '0 0 20 20',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export function IconReport(props) {
  return (
    <svg {...base} {...props}>
      <path d="M5 2.5v15" />
      <path d="M5 3.5c2-1 4-1 6 0s4 1 6 0v7c-2 1-4 1-6 0s-4-1-6 0" />
    </svg>
  )
}

export function IconList(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="4.5" cy="5" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="4.5" cy="10" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="4.5" cy="15" r="0.9" fill="currentColor" stroke="none" />
      <path d="M8 5h8M8 10h8M8 15h8" />
    </svg>
  )
}

export function IconCamera(props) {
  return (
    <svg {...base} {...props}>
      <path d="M3 6.5a1 1 0 0 1 1-1h2l1.2-1.8a1 1 0 0 1 .8-.4h4a1 1 0 0 1 .8.4L14 5.5h2a1 1 0 0 1 1 1V15a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6.5Z" />
      <circle cx="10" cy="10.5" r="3" />
    </svg>
  )
}

export function IconMic(props) {
  return (
    <svg {...base} {...props}>
      <rect x="7.5" y="2.5" width="5" height="9" rx="2.5" />
      <path d="M4.5 9.5a5.5 5.5 0 0 0 11 0" />
      <path d="M10 15v2.5M7 17.5h6" />
    </svg>
  )
}

export function IconStop(props) {
  return (
    <svg {...base} {...props}>
      <rect x="6" y="6" width="8" height="8" rx="1.5" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function IconPin(props) {
  return (
    <svg {...base} {...props}>
      <path d="M10 17.5s6-5.6 6-10a6 6 0 1 0-12 0c0 4.4 6 10 6 10Z" />
      <circle cx="10" cy="7.5" r="2" />
    </svg>
  )
}

export function IconCheck(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 10.5l4 4 8-9" />
    </svg>
  )
}

export function IconAlert(props) {
  return (
    <svg {...base} {...props}>
      <path d="M10 2.5 18 16.5H2L10 2.5Z" />
      <path d="M10 8v3.5" />
      <circle cx="10" cy="14" r="0.15" fill="currentColor" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  )
}

export function IconTrash(props) {
  return (
    <svg {...base} strokeWidth={1.8} width={11} height={11} viewBox="0 0 20 20" {...props}>
      <path d="M4 6h12M8 6V4.5h4V6M6 6l.7 9.5a1 1 0 0 0 1 .9h4.6a1 1 0 0 0 1-.9L14 6" />
    </svg>
  )
}

export function IconEmptyBox(props) {
  return (
    <svg {...base} width={40} height={40} {...props}>
      <path d="M3 7l7-3.5L17 7v6.5L10 17l-7-3.5V7Z" />
      <path d="M3 7l7 3.2L17 7M10 10.2V17" />
    </svg>
  )
}

export function LogoMark(props) {
  // A road-marker chevron inside a badge — reads as "civic infrastructure",
  // not a generic abstract blob mark.
  return (
    <svg viewBox="0 0 30 30" fill="none" {...props}>
      <rect x="0.75" y="0.75" width="28.5" height="28.5" rx="7" stroke="currentColor" strokeWidth="1.4" opacity="0.5" />
      <path d="M9 20l6-11 6 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M11.5 15.5h7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}
