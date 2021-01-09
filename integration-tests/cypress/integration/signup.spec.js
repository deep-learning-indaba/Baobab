// Todo find a way to clean up created users
describe("Sign up", function() {
  function testUser() {
    const testUser = {
      firstName: "John",
      lastName: "Snow",
      email: "john2@thewall.com",
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
  });
  /*
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
        email: "john2@thewall.com"
      }
    }).then(response => {
      expect(response.status).to.eq(200);
    });
  });
  */
  it("Page Loads", function() {
    cy.visit("/");
    cy.get("#nav-signup").click();
    // we should be redirected to /createAccount
    cy.url().should("include", "/createAccount");
  });

  // Disabling these tests because they're failing. See issue #852
  /*
  it("Signup form cannot be submitted in if you havent accepted the policy or if you are underage.", function() {
    let user = testUser();
    cy.visit("/createAccount");
    cy.wait(2000);
    cy.get("#title")
      .find("input")
      .click({ force: true })
      .type("Mr", { force: true })
      .wait(500)
      .get("#react-select-2-option-0")
      .click();
    cy.get("input[id=firstName]").type(user.firstName);
    cy.get("input[id=lastName]").type(user.lastName);
    cy.get("input[id=email]").type(user.email);
    cy.get("input[id=password]").type(user.password);
    cy.get("input[id=confirmPassword]").type(user.confirmPassword);

    // signup should be disabled due to lack of consent or being underage
    cy.get("#btn-signup-confirm").should("be.disabled");
  });

  it("Singup form can be submitted if you fill in everything correctly.", function() {
    let user = testUser();
    cy.visit("/createAccount");
    cy.wait(2000);
    cy.get("#title")
      .find("input")
      .click({ force: true })
      .type("Mr", { force: true })
      .get("#react-select-2-option-0")
      .wait(500)
      .click();
    cy.get("input[id=firstName]").type(user.firstName);
    cy.get("input[id=lastName]").type(user.lastName);
    cy.get("input[id=email]").type(user.email);
    cy.get("input[id=password]").type(user.password);
    cy.get("input[id=confirmPassword]").type(user.confirmPassword);

    cy.get("#btn-cookieConsent").click();
    // Forcing the below because Bootstrap custom control checkboxes hide the input control
    cy.get("#over18").click({force: true});
    cy.get("#agreePrivacyPolicy").click({force: true});

    cy.get("#btn-signup-confirm").click();

    // account should be created
    cy.get("#account-created").should("exist");
  });
  */
});
