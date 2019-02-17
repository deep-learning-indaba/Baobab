export const ruleRunner = (rule, ...validations) => {
  return state => {
    for (let v of validations) {
      let errorMessageFunc = v(state[rule.name])
      if (errorMessageFunc) {
        return { [rule.name]: errorMessageFunc(rule.display) }
      }
    }
    return null
  }
}
export const run = (state, runners) => {
  let array = []
  runners.forEach(function(runner) {
    if (runner(state)) {
      array.push(runner(state))
    }
  })
  return array
}
