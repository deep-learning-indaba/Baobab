
export function tagList() {
  return new Promise(resolve => {
    resolve([
      { "id": 1, "event_id": 3, "name": "Mock Tag" },
      { "id": 2, "event_id": 3, "name": "Desk Reject" },
      { "id": 7, "event_id": 3, "name": "Healthcare" }
    ])
  })

}