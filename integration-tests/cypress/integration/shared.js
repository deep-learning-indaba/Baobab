function testUser() {
  const testUser = {
    firstName: "John",
    lastName: "Snow",
    email: "john@thewall.com",
    password: "whitewalker360",
    confirmPassword: "whitewalker360"
  };
  return testUser;
}

export function login() {
  let user = testUser();
  cy.visit("/login");
  cy.get("input[id=email]").type(user.email);
  cy.get("input[id=password]").type(user.password);
  cy.get("#btn-login").click({force: true});  // Forcing because the button can be hidden by the cookie consent.
  cy.wait(500);
  // No error.
  cy.get("#error-login").should("not.exist");
}

export function selectDropdown(dropdownId,textToType) {
  cy.get(dropdownId)
    .find("input")
    .click({ force: true })
    .type(textToType + "{enter}", { force: true });
}
