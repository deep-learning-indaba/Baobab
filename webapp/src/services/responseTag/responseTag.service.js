
export const tagResponse = {
    post
};
  
function post(param) {
   return new Promise((resolve, reject) => {
        if (param) {
            resolve({"status": 201, "tag_id": param.tag_id})
        }
        else {
            reject({"status": 400, "message": "Status 400"})
        }
    
})
}

/*
 function test() {
    return new Promise(resolve => {
      resolve({"status": 200, "tag": {"headline": "test tag", "id": 101}})
    })
  }
*/

  