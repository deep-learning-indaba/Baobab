import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const TYPE_ICON = {
  string: 'fa-font',
  number: 'fa-hashtag',
  boolean: 'fa-toggle-on',
  date: 'fa-calendar',
  url: 'fa-link',
  markdown: 'fa-align-left',
  list: 'fa-list',
  object: 'fa-folder',
};

function loopName(path) {
  const last = path.split('.').pop();
  if (last.endsWith('ies')) return last.slice(0, -3) + 'y';
  if (last.endsWith('s')) return last.slice(0, -1);
  return 'item';
}

function FieldRow({ path, field, depth, onInsert, t }) {
  const [open, setOpen] = useState(depth === 0);
  const nested = field.type === 'object' ? field.fields : field.type === 'list' && field.item.fields;
  const insertValue = () => {
    if (field.type === 'list') {
      const item = loopName(path);
      const firstField = field.item.fields ? Object.keys(field.item.fields)[0] : null;
      onInsert(`{% for ${item} in ${path} %}\n- {{ ${item}${firstField ? '.' + firstField : ''} }}\n{% endfor %}\n`);
    } else if (field.type === 'boolean') {
      onInsert(`{% if ${path} %}\n\n{% else %}\n\n{% endif %}`);
    } else {
      onInsert(`{{ ${path} }}`);
    }
  };

  return (
    <li>
      <div className="flex items-start gap-1.5 py-1" style={{ paddingLeft: depth * 14 }}>
        {nested ? (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="mt-0.5 w-4 text-muted-foreground hover:text-foreground cursor-pointer"
            aria-label={open ? t('Collapse') : t('Expand')}
          >
            <i className={`fas fa-chevron-${open ? 'down' : 'right'}`} style={{ fontSize: 10 }} />
          </button>
        ) : (
          <span className="w-4" />
        )}
        <i className={`fas ${TYPE_ICON[field.type] || 'fa-circle'} mt-1 text-muted-foreground`} style={{ fontSize: 11 }} />
        <div className="min-w-0 flex-1">
          {field.type === 'object' && depth === 0 ? (
            <span className="font-mono text-xs font-semibold text-foreground">{path}</span>
          ) : (
            <button
              type="button"
              onClick={insertValue}
              className="font-mono text-xs text-action hover:underline cursor-pointer text-left break-all"
              title={field.type === 'list' ? t('Insert a loop over this list')
                : field.type === 'boolean' ? t('Insert a condition on this value') : t('Insert this value')}
            >
              {path.split('.').pop()}
            </button>
          )}
          {field.description && (
            <div className="text-xs text-muted-foreground leading-snug">{field.description}</div>
          )}
        </div>
      </div>
      {nested && open && (
        <ul>
          {Object.entries(nested).map(([name, child]) => (
            <FieldRow
              key={name}
              path={field.type === 'list' ? `${loopName(path)}.${name}` : `${path}.${name}`}
              field={child}
              depth={depth + 1}
              onInsert={onInsert}
              t={t}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

/** The fields this email can use, as a clickable tree that inserts into the editor. */
export default function FieldBrowser({ context, onInsert }) {
  const { t } = useTranslation();
  return (
    <div className="text-sm">
      <p className="text-xs text-muted-foreground mb-2">
        {t('Click a field to insert it. Lists insert a loop; yes/no values insert a condition.')}
      </p>
      <ul>
        {Object.entries(context || {}).map(([name, node]) => (
          <FieldRow
            key={name}
            path={name}
            field={{ type: 'object', fields: node.fields, description: node.label + (node.nullable ? ` (${t('may be empty')})` : '') }}
            depth={0}
            onInsert={onInsert}
            t={t}
          />
        ))}
      </ul>
    </div>
  );
}
