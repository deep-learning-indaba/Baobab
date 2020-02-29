// Todo find a way to clean up created users
describe("Sign up and Login", function() {
  function testUser() {
    const testUser = {
      firstName: "John",
      lastName: "Snow",
      email: "john@thewall" + Math.floor(Math.random() * 10000000) + ".com",
      password: "white_walker_256",
      confirmPassword: "white_walker_256"
    };
    return testUser;
  }

  before(function() {
    // If running outside of docker, then start container
    if (Cypress.config().baseUrl.includes("webapp") == false) {
      cy.exec("docker-compose up --detach");
    }
  });

  after(function() {
    // stop running containers
    if (Cypress.env("baseUrl").includes("webapp") == False) {
      cy.exec("docker-compose stop");
    }
  });


  Cypress.on("uncaught:exception", (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
  });

  
  it("Signup page successfully loads.", function() {
    cy.visit("/");
    cy.get("#nav-signup").click();
    // we should be redirected to /createAccount
    cy.url().should("include", "/createAccount");
  });

  it("Login page successfully loads.", function() {
    cy.visit("/");
    cy.get("#nav-login").click();
    // we should be redirected to /login
    cy.url().should("include", "/login");
  });

  it("Signup form cannot be submitted in if you havent accepted the policy or if you are underage.", function() {
    let user = testUser();
    cy.visit("/createAccount");
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
    cy.get("#over18").click();
    cy.get("#agreePrivacyPolicy").click();
    cy.get("#btn-signup-confirm").click();

    // account should be created
    cy.get("#account-created").should("exist");
  });

  it("Login form works.", function() {
    let user = testUser();
    cy.visit("/login");
    cy.get("input[id=email]").type(user.email);
    cy.get("input[id=password]").type(user.password);
    cy.get("#btn-login").click();

    // Login should not return error, but email is not verified.
    cy.get("#error-login").contains("not verified");
  });
});
