const validationFields = {
  email: { name: "email", display: "Email Address" },
  title: { name: "title", display: "Title" },
  firstName: { name: "firstName", display: "First Name" },
  lastName: { name: "lastName", display: "Last Name" },
  nationality: { name: "nationality", display: "Country of Nationality" },
  residence: { name: "residence", display: "Country of Residence" },
  password: { name: "password", display: "Password" },
  confirmPassword: { name: "confirmPassword", display: "Confirm Password" },
  dateOfBirth: { name: "dateOfBirth", display: "Date of Birth" },
  role: { name: "role", display: "Role" },
  passportNumber: { name: "passportNumber", display: "Passport Number" },
  fullNameOnPassport: {
    name: "fullNameOnPassport",
    display: "Full Name",
    description: "Full Name as it appears on Passport."
  },
  passportExpiryDate: {
    name: "passportExpiryDate",
    display: "Passport Date of Expiry."
  },
  passportIssuedByAuthority: {
    name: "passportIssuedByAuthority",
    display: "Authority that issued Passport"
  },
  workStreet1: { name: "workStreet1", display: "Work Street Address 1" },
  workStreet2: { name: "workStreet2", display: "Work Street Address 2" },
  workCity: { name: "workCity", display: "Work City" },
  workPostalCode: { name: "workPostalCode", display: "Work Postal Code" },
  workCountry: { name: "workCountry", display: "Work Country" },
  residentialStreet1: {
    name: "residentialStreet1",
    display: "Residential Street Address 1"
  },
  residentialStreet2: {
    name: "residentialStreet2",
    display: "Residential Street Address 2"
  },
  residentialCity: { name: "residentialCity", display: "Residential City" },
  residentialPostalCode: {
    name: "residentialPostalCode",
    display: "Residential Postal Code"
  },
  residentialCountry: {
    name: "residentialCountry",
    display: "Residential Country"
  },
  letterAddressedTo: {
    name: "letterAddressedTo",
    display: "Addressed to ",
    description:
      "Who the visa letter should be addressed to, e.g. Immigration Officer of X Embassy"
  }
};

export default validationFields;
