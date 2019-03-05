export function authHeader() {
    // return authorization header with basic auth credentials
    let user = JSON.parse(localStorage.getItem("user"));
  
    if (user) {
      return { "Authorization": user.token };
    } else {
      return {};
    }
  }