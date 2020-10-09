
export function tagList() {
  return new Promise(resolve => {
    resolve([
        { "id": 1, "event_id": 3, "name": "First Tag" },
        { "id": 2, "event_id": 3, "name": "Second Tag" },
        { "id": 3, "event_id": 3, "name": "Third Tag" }
    ])
})
    
}