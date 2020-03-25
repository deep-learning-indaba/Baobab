import {login,selectDropdown} from "./shared.js"
describe("Invitation Letter", function() {

  function testUser() {
  const testUser = {
    fullNameOnPassport: "John Snow",
    passportNumber : "148413515",
    passportExpiryDate: "2030-01-01",
    passportIssuedByAuthority: "UN",
    letterAddressedTo: "Person of UN",

    residentialStreet1: "add 1",
    residentialStreet2: "add 2" ,
    residentialCity: "add 3",
    residentialPostalCode: "add 4",
    residentialCountry: "Ghana" ,

    nationality: "South Africa" ,
    residence: "Ghana",
    dateOfBirth: "1980-01-01"
  };
  return testUser;
}

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

  it("Page Loads.", function() {
    login()
    let user = testUser();
    cy.visit("/test2021/invitationLetter");
  });

  it("Invitation form can be filled in", function() {
    login()
    let user = testUser();
    cy.visit("/test2021/invitationLetter");
    cy.get("input[id=fullNameOnPassport]").type(user.fullNameOnPassport);
    cy.get("input[id=passportNumber]").type(user.passportNumber);
    cy.get("input[id=passportExpiryDate]").type(user.passportExpiryDate);
    cy.get("input[id=passportIssuedByAuthority]").type(user.passportIssuedByAuthority);
    cy.get("input[id=letterAddressedTo]").type(user.letterAddressedTo);

    cy.get("input[id=residentialStreet1]").type(user.residentialStreet1);
    cy.get("input[id=residentialStreet2]").type(user.residentialStreet2);
    cy.get("input[id=residentialCity]").type(user.residentialCity);
    cy.get("input[id=residentialPostalCode]").type(user.residentialPostalCode);
    selectDropdown("#residentialCountry",user.residentialCountry)

    selectDropdown("#nationality",user.nationality)
    selectDropdown("#residence",user.residence)
    cy.get("input[id=dateOfBirth]").type(user.dateOfBirth);
    
    cy.get("#btn-cookieConsent").click();
    cy.get("#btn-invitationLetter-submit").should("be.enabled");
    cy.get("#btn-invitationLetter-submit").click();
    // For now, this won't succeed since user has not registered
    cy.get("#alert-invitation-letter-failure").contains("Registration not found")
    // cy.get("alert-invitation-letter-success").should("exist");

  });
});