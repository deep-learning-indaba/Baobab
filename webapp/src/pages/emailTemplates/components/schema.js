// Helpers over an email type's context schema, as returned by
// GET .../email-types/<key>: { name: { label, fields: { field: {type, ...} } } }.

// {loopVariable: ['offer', 'grants']} for every `{% for x in a.b %}` and
// `{% assign x = a.b %}` in the template, so completions and the field
// browser know what `x.` refers to.
export function loopBindings(text) {
  const bindings = {};
  const pattern = /\{%-?\s*(?:for\s+(\w+)\s+in|assign\s+(\w+)\s*=)\s*([\w.]+)/g;
  let match;
  while ((match = pattern.exec(text || '')) !== null) {
    const name = match[1] || match[2];
    const path = match[3].split('.');
    const resolved = bindings[path[0]] ? bindings[path[0]].concat(path.slice(1)) : path;
    bindings[name] = match[1] ? resolved.concat(['[item]']) : resolved;
  }
  return bindings;
}

// The schema node at `path` (an object with `fields`), or null.
export function fieldAt(context, path, bindings = {}) {
  if (!path || path.length === 0) return null;
  let segments = path;
  if (bindings[path[0]]) segments = bindings[path[0]].concat(path.slice(1));
  let node = context[segments[0]];
  for (const segment of segments.slice(1)) {
    if (!node) return null;
    if (node.type === 'list') {
      if (segment === '[item]' || segment === 'first' || segment === 'last') {
        node = node.item;
        continue;
      }
      return null;
    }
    node = node.fields ? node.fields[segment] : null;
  }
  if (node && node.type === 'list') {
    return {
      fields: {
        size: { type: 'number', description: 'Number of items' },
        first: node.item.fields ? { type: 'object', fields: node.item.fields, description: 'First item' } : node.item,
        last: node.item.fields ? { type: 'object', fields: node.item.fields, description: 'Last item' } : node.item,
      },
    };
  }
  return node && node.fields ? node : null;
}

// Every field reachable without entering a list, as [{path, field}].
export function flattenFields(context) {
  const out = [];
  const walk = (prefix, fields) => {
    Object.entries(fields || {}).forEach(([name, field]) => {
      const path = `${prefix}.${name}`;
      if (field.type === 'object') walk(path, field.fields);
      else out.push({ path, field });
    });
  };
  Object.entries(context || {}).forEach(([name, node]) => walk(name, node.fields));
  return out;
}

export function linkFields(context) {
  return flattenFields(context).filter(({ field }) => field.type === 'url');
}

// Things the preview can switch to see the template's other branches:
// booleans flipped, lists emptied, optional values removed.
export function scenarioSwitches(context) {
  const switches = [];
  Object.entries(context || {}).forEach(([name, node]) => {
    if (node.nullable) {
      switches.push({ path: name, kind: 'present', label: node.label || name });
    }
    if (name === 'recipient' || name === 'organisation') return;
    Object.entries(node.fields || {}).forEach(([fieldName, field]) => {
      const path = `${name}.${fieldName}`;
      if (field.type === 'boolean') {
        switches.push({ path, kind: 'boolean', label: field.description, initial: field.sample !== false });
      }
      else if (field.type === 'list') switches.push({ path, kind: 'list', label: field.description });
      else if (field.type === 'object' && field.nullable) {
        switches.push({ path, kind: 'present', label: field.description });
      }
    });
  });
  return switches;
}

// A Liquid string literal for any text.
export function liquidString(text) {
  return `"${String(text).replace(/\\/g, '').replace(/"/g, "'")}"`;
}
