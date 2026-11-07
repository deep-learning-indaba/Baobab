import { getFileURL } from './files'

// Vite's import.meta.glob replaces webpack/CRA's dynamic require() for image loading.
// Eagerly importing with ?url gives us a map of filename → asset URL at build time.
const imageMap = import.meta.glob('../images/*', { eager: true, query: '?url', import: 'default' })

const FILE_ID = /^[0-9a-f]{32}$/

// Resolves a bundled filename, an absolute URL or an uploaded file id to a URL.
export const getImage = (value) => {
  if (!value) return undefined
  if (FILE_ID.test(value)) return getFileURL(value, 'inline')
  if (/^(https?:)?\/\//.test(value) || value.startsWith('/')) return value
  return imageMap[`../images/${value}`]
}
