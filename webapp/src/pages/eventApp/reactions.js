// Keys match REACTION_EMOJIS in api/app/discussion/models.py (same order).
export var REACTION_OPTIONS = [
  { key: 'thumbs_up', glyph: '👍', label: 'Like' },
  { key: 'heart', glyph: '❤️', label: 'Love' },
  { key: 'clap', glyph: '👏', label: 'Applause' },
  { key: 'celebrate', glyph: '🎉', label: 'Celebrate' },
  { key: 'smile', glyph: '😄', label: 'Happy' },
  { key: 'insightful', glyph: '💡', label: 'Insightful' },
  { key: 'thanks', glyph: '🙏', label: 'Thank you' },
  { key: 'rocket', glyph: '🚀', label: 'Exciting' },
];

export var REACTION_BY_KEY = REACTION_OPTIONS.reduce(function (acc, o) {
  acc[o.key] = o;
  return acc;
}, {});
