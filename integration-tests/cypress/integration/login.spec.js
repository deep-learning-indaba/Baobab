import {login} from "./shared.js"
describe("Login", function() {
  before(function() {
    // If running outside of docker, then start container
    if (Cypress.config().baseUrl.includes("webapp") == false) {
      cy.exec("docker-compose up --detach");
    }
    // Create test user
    cy.request({
      method: "get",
      url: "http://web:5000/api/v1/integration-tests/createUser", // baseUrl is prepended to url
      headers: {
        Origin: "webappintegration"
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
        Origin: "webappintegration"
      },
      body: {
        email:"john@thewall.com"
      }
    }).then(response => {
      expect(response.status).to.eq(200);
    });
  });


  it("Page Loads", function() {
    cy.visit("/");
    cy.get("#nav-login").click();
    // we should be redirected to /login
    cy.url().should("include", "/login");
  });

 
  it("Login form works", function() {
    login()
  });
});
