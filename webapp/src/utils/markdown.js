/**
 * Reduce markdown source to plain text for contexts that can't render real
 * markdown - e.g. a truncated preview inside a clickable card, where a real
 * <a> would be invalid HTML nested inside the card's <button>.
 */
export function stripMarkdown(text) {
  return (text || '')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/(\*\*|__)(.*?)\1/g, '$2')
    .replace(/(\*|_)(.*?)\1/g, '$2')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .trim();
}
