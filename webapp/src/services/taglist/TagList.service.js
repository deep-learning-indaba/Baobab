
export const tagList = {
  list,
  post,
  remove
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
    resolve({ "status": 201 })
  })
}

function remove(tag) {
  return new Promise((resolve, reject )=> {
    if (tag) {
      resolve({ "status": 201 })
    }
    else {
      reject({ "status": 400, "message": "Network Error" })
    }
  })
}
   
  


