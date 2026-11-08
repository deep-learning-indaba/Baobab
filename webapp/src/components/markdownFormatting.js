// Pure helpers that compute markdown edits for a textarea toolbar.

const INLINE = {
  bold: { open: '**', close: '**' },
  italic: { open: '_', close: '_' },
};

const LINE_PREFIX = {
  heading: { prefix: '### ', pattern: /^### / },
  bulletList: { prefix: '- ', pattern: /^- / },
  numberedList: { prefix: null, pattern: /^\d+\. / },
  quote: { prefix: '> ', pattern: /^> / },
};

// A previous line with one of these prefixes already forms a block, so no
// separating blank line is needed.
const BLOCK_LINE = /^(- |\d+\. |> )/;

function result(replaceStart, replaceEnd, text, selStart, selEnd) {
  return {
    replaceStart,
    replaceEnd,
    text,
    selectionStart: replaceStart + selStart,
    selectionEnd: replaceStart + selEnd,
  };
}

function applyLink(value, start, end, placeholderText) {
  const label = start === end ? placeholderText : value.slice(start, end);
  const url = 'https://';
  const text = `[${label}](${url})`;
  const urlStart = label.length + 3;
  return result(start, end, text, urlStart, urlStart + url.length);
}

function applyInline(action, value, start, end, placeholderText) {
  const { open, close } = INLINE[action];
  const selected = value.slice(start, end);

  // Selection covers the markers: **word**
  if (
    selected.length >= open.length + close.length &&
    selected.startsWith(open) &&
    selected.endsWith(close)
  ) {
    const inner = selected.slice(open.length, selected.length - close.length);
    return result(start, end, inner, 0, inner.length);
  }

  // Markers sit just outside the selection: **[word]**
  if (
    start >= open.length &&
    value.slice(start - open.length, start) === open &&
    value.slice(end, end + close.length) === close
  ) {
    return result(
      start - open.length,
      end + close.length,
      selected,
      0,
      selected.length
    );
  }

  const label = start === end ? placeholderText : selected;
  return result(
    start,
    end,
    open + label + close,
    open.length,
    open.length + label.length
  );
}

function applyLinePrefix(action, value, start, end, placeholderText) {
  const { prefix, pattern } = LINE_PREFIX[action];
  const prefixFor = (n) => (prefix === null ? `${n}. ` : prefix);

  // A selection ending right after a newline doesn't include the next line.
  const lastChar = end > start && value[end - 1] === '\n' ? end - 1 : end;
  const blockStart = value.lastIndexOf('\n', start - 1) + 1;
  const newlineAfter = value.indexOf('\n', lastChar);
  const blockEnd = newlineAfter === -1 ? value.length : newlineAfter;

  const lines = value.slice(blockStart, blockEnd).split('\n');
  const contentLines = lines.filter((l) => l !== '');

  if (contentLines.length > 0 && contentLines.every((l) => pattern.test(l))) {
    const text = lines.map((l) => l.replace(pattern, '')).join('\n');
    return result(blockStart, blockEnd, text, 0, text.length);
  }

  let text;
  let selStart = 0;
  let selEnd;
  if (contentLines.length === 0) {
    text = prefixFor(1) + placeholderText;
    selStart = prefixFor(1).length;
    selEnd = text.length;
  } else {
    let n = 0;
    text = lines
      .map((l) => (l === '' ? l : prefixFor(++n) + l.replace(pattern, '')))
      .join('\n');
    selEnd = text.length;
  }

  let lead = '';
  if (blockStart > 0) {
    const prevEnd = blockStart - 1;
    const prev = value.slice(value.lastIndexOf('\n', prevEnd - 1) + 1, prevEnd);
    if (prev !== '' && !BLOCK_LINE.test(prev)) lead = '\n';
  }

  return result(
    blockStart,
    blockEnd,
    lead + text,
    lead.length + selStart,
    lead.length + selEnd
  );
}

// Computes the edit for a toolbar action. `value.slice(replaceStart,
// replaceEnd)` is replaced by `text`; the selection offsets are absolute in
// the resulting string.
export function applyFormat(action, value, start, end, placeholderText) {
  if (action === 'link') return applyLink(value, start, end, placeholderText);
  if (INLINE[action]) {
    return applyInline(action, value, start, end, placeholderText);
  }
  if (LINE_PREFIX[action]) {
    return applyLinePrefix(action, value, start, end, placeholderText);
  }
  throw new Error(`Unknown markdown action: ${action}`);
}
