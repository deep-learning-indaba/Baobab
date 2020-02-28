describe("The Home Page", function() {
  beforeEach(function() {
    // If running outside of docker, then start container
    if (Cypress.env("baseUrl").includes("webapp") == False) {
      cy.exec("docker-compose up --detach");
    }
  });

  Cypress.on("uncaught:exception", (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
  });

  it("successfully loads", function() {
    cy.visit("/");
    cy.wait(60);
  });
});
