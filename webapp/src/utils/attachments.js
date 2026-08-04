// Only markdown links/images pointing at our own upload endpoint are treated
// as attachments - anything else is a link the user typed themselves and
// must survive extraction/rebuild untouched.
var FILE_URL_MARKER = '/api/v1/file?filename=';
var ATTACHMENT_MARKDOWN_RE = /(!?)\[([^\]]*)\]\(([^)]+)\)/g;

/**
 * Split a markdown body into its plain-text part and the image/PDF
 * attachments embedded in it, so a composer can show them as removable
 * chips instead of raw markdown syntax. The inverse of buildBodyMarkdown().
 */
export function extractAttachments(markdown) {
  var attachments = [];
  var text = (markdown || '').replace(ATTACHMENT_MARKDOWN_RE, function (match, bang, alt, url) {
    if (url.indexOf(FILE_URL_MARKER) === -1) return match;
    attachments.push({ id: url, name: alt || 'file', url: url, isImage: bang === '!' });
    return '';
  }).replace(/\n{3,}/g, '\n\n').trim();
  return { text: text, attachments: attachments };
}

/**
 * Combine composer text and attachment chips back into a single markdown
 * body for submission. Attachments always land after the text, since chips
 * don't carry a position within it.
 */
export function buildBodyMarkdown(text, attachments) {
  var trimmedText = (text || '').trim();
  var lines = (attachments || []).map(function (a) {
    return (a.isImage ? '!' : '') + '[' + a.name + '](' + a.url + ')';
  });
  return trimmedText ? [trimmedText].concat(lines).join('\n\n') : lines.join('\n\n');
}
