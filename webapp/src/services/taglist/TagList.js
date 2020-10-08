
export function tagList() {
  return new Promise(resolve => {
    resolve([
        { "id": 5, "event_id": 3, "name": "First Tag" },
        { "id": 6, "event_id": 3, "name": "Second Tag" },
        { "id": 7, "event_id": 3, "name": "Third Tag" }
    ])
})
    
}