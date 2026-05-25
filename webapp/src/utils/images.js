// Vite's import.meta.glob replaces webpack/CRA's dynamic require() for image loading.
// Eagerly importing with ?url gives us a map of filename → asset URL at build time.
const imageMap = import.meta.glob('../images/*', { eager: true, query: '?url', import: 'default' })

export const getImage = (filename) => imageMap[`../images/${filename}`]
