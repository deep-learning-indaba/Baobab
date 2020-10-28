
export const tagList = {
  list,
  post
};

 function list() {
  return new Promise(resolve => {
    resolve([
      { "id": 1, "event_id": 3, "name": "Mock Tag" },
      { "id": 2, "event_id": 3, "name": "Desk Reject" },
      { "id": 7, "event_id": 3, "name": "Healthcare" }
    ])
  })
}

 function post() {
  return new Promise(resolve => {
    resolve({"status": 201})
  })
}

