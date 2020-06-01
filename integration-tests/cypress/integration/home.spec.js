describe("The Home Page", function() {
  before(function() {
    // If running outside of docker, then start container
    if (Cypress.config().baseUrl.includes("webapp") == false) {
      cy.exec("docker-compose up --detach");
    }
  });

  it("Page Loads", function() {
    cy.visit("/");
    cy.wait(50);
    // Home page should show logo with valid source
    cy.get('img[class="img-fluid large-logo"]').should('have.attr', 'src');
  });
});
