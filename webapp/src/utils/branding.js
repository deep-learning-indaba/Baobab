import { getImage } from './images'

const HEX = /^#[0-9a-fA-F]{6}$/
const DARK = '#191c1d'
const LIGHT = '#ffffff'

const parse = (hex) => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16))
const toHex = (rgb) => '#' + rgb.map(v => Math.round(v).toString(16).padStart(2, '0')).join('')

const luminance = (hex) => {
  const [r, g, b] = parse(hex).map(v => {
    const c = v / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

export const contrastRatio = (hexA, hexB) => {
  if (!HEX.test(hexA || '') || !HEX.test(hexB || '')) return undefined
  const [a, b] = [luminance(hexA), luminance(hexB)].sort((x, y) => y - x)
  return (a + 0.05) / (b + 0.05)
}

export const readableForeground = (hex) =>
  contrastRatio(hex, LIGHT) >= contrastRatio(hex, DARK) ? LIGHT : DARK

const mixWithWhite = (hex, amount) =>
  toHex(parse(hex).map(v => v + (255 - v) * amount))

const rgba = (hex, alpha) => `rgba(${parse(hex).join(', ')}, ${alpha})`

const PRIMARY_VARS = [
  '--color-primary', '--color-primary-container', '--color-primary-foreground',
  '--clr-primary', '--clr-primary-container', '--clr-on-primary',
  '--clr-on-primary-muted', '--clr-on-primary-divider',
]
const ACTION_VARS = [
  '--color-action', '--color-action-container', '--color-action-foreground', '--color-ring',
  '--clr-action', '--clr-action-container', '--clr-on-action', '--clr-action-glow',
]

const applyRole = (style, names, hex, values) => {
  const valid = typeof hex === 'string' && HEX.test(hex)
  names.forEach(name => {
    if (valid) style.setProperty(name, values(hex)[name])
    else style.removeProperty(name)
  })
}

const primaryValues = (hex) => {
  const container = mixWithWhite(hex, 0.15)
  const fg = readableForeground(hex)
  return {
    '--color-primary': hex,
    '--color-primary-container': container,
    '--color-primary-foreground': fg,
    '--clr-primary': hex,
    '--clr-primary-container': container,
    '--clr-on-primary': fg,
    '--clr-on-primary-muted': rgba(fg, 0.82),
    '--clr-on-primary-divider': rgba(fg, 0.22),
  }
}

const actionValues = (hex) => {
  const container = mixWithWhite(hex, 0.15)
  const fg = readableForeground(hex)
  return {
    '--color-action': hex,
    '--color-action-container': container,
    '--color-action-foreground': fg,
    '--color-ring': hex,
    '--clr-action': hex,
    '--clr-action-container': container,
    '--clr-on-action': fg,
    '--clr-action-glow': rgba(hex, 0.14),
  }
}

// Remembers each link's original attributes so they can be restored.
const rememberLink = (link) => {
  if (link.dataset.brandingOriginal) return
  link.dataset.brandingOriginal = JSON.stringify({
    href: link.getAttribute('href'),
    sizes: link.getAttribute('sizes'),
    type: link.getAttribute('type'),
  })
}

const setLinks = (selector, url) => {
  document.querySelectorAll(selector).forEach(link => {
    rememberLink(link)
    const original = JSON.parse(link.dataset.brandingOriginal)
    if (url) {
      link.setAttribute('href', url)
      link.removeAttribute('sizes')
      link.removeAttribute('type')
    } else {
      ['href', 'sizes', 'type'].forEach(attr => {
        if (original[attr] === null) link.removeAttribute(attr)
        else link.setAttribute(attr, original[attr])
      })
    }
  })
}

export const applyBranding = (org) => {
  const o = org || {}
  const style = document.documentElement.style
  applyRole(style, PRIMARY_VARS, o.primary_colour, primaryValues)
  applyRole(style, ACTION_VARS, o.secondary_colour, actionValues)

  const primaryValid = typeof o.primary_colour === 'string' && HEX.test(o.primary_colour)
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', primaryValid ? o.primary_colour : '#0f172a')

  const favicon = getImage(o.favicon)
  setLinks('link[rel="icon"], link[rel="shortcut icon"]', favicon)
  setLinks('link[rel="apple-touch-icon"]', getImage(o.pwa_icon_192))
}
