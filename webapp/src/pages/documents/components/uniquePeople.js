// The profile list has one row per response or invitation, so a person with several of
// either appears several times. Pickers need one entry per person.
export function uniquePeople(profiles) {
  const seen = new Set();
  return profiles.filter((p) => {
    if (seen.has(p.user_id)) return false;
    seen.add(p.user_id);
    return true;
  });
}
