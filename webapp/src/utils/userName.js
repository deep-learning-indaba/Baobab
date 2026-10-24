export function formatUserName(title, firstname, lastname) {
  return [title, firstname, lastname].filter(Boolean).join(" ");
}
