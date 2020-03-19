// Todo find a way to clean up created users
describe("Login", function() {
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

  before(function() {
    // If running outside of docker, then start container
    if (Cypress.config().baseUrl.includes("webapp") == false) {
      cy.exec("docker-compose up --detach");
    }
    // Delete test user if they exist
    cy.request({
      method: "get",
      url: "http://web:5000/api/v1/integration-tests/createUser", // baseUrl is prepended to url
      headers: {
        Origin: "webapp"
      }
    }).then(response => {
      expect(response.status).to.eq(200);
    });
  });

  after(function() {
    // stop running containers
    if (Cypress.config().baseUrl.includes("webapp") == false) {
      cy.exec("docker-compose stop");
    }
    // Delete test user if they exist
    cy.request({
      method: "post",
      url: "http://web:5000/api/v1/integration-tests/deleteUser", // baseUrl is prepended to url
      headers: {
        Origin: "webapp"
      },
      body: {
        email:"john@thewall.com"
      }
    }).then(response => {
      expect(response.status).to.eq(200);
    });
  });


  it("Login page successfully loads.", function() {
    cy.visit("/");
    cy.get("#nav-login").click();
    // we should be redirected to /login
    cy.url().should("include", "/login");
  });

 
  it("Login form works.", function() {
    let user = testUser();
    cy.visit("/login");
    cy.get("input[id=email]").type(user.email);
    cy.get("input[id=password]").type(user.password);
    cy.get("#btn-login").click();
    cy.wait(500)
    // No error.
    cy.get("#error-login").should('not.exist')
  });
});
