const validationFields = {
  email: { name: "email", display: "Email Address" },
  title: { name: "title", display: "Title" },
  firstName: { name: "firstName", display: "First Name" },
  lastName: { name: "lastName", display: "Last Name" },
  gender: { name: "gender", display: "Gender" },
  nationality: { name: "nationality", display: "Country of Nationality" },
  residence: { name: "residence", display: "Country of Residence" },
  ethnicity: {
    name: "ethnicity",
    display: "Ethnicity",
    description: "We use South African demographic groupings for reporting."
  },
  affiliation: {
    name: "affiliation",
    display: "Affiliation",
    description:
      "Please enter the name of your university if academic or student, or the name of your company if industry professional"
  },
  department: {
    name: "department",
    display: "Department",
    description:
      "Please enter the name of your faculty if academic or student, the department you work for if industry professional or N/A if not applicable."
  },
  disability: {
    name: "disability",
    display: "Disability",
    placeholder: "Type of Disability or None",
    description:
      "We use the Washington Group difficulty schemes, and it helps us to ensure that our facilities can accommodate the needs of all attendees."
  },
  username: { name: "username", display: "Username" },
  password: { name: "password", display: "Password" },
  category: {
    name: "category",
    display: "User Category",
    description:
      "If you are a part-time student working as an academic, choose academic. Similarly for industry."
  },
  confirmPassword: { name: "confirmPassword", display: "Confirm Password" },
  dateOfBirth: { name: "dateOfBirth", display: "Date of Birth" },
  primaryLanguage: { name: "primaryLanguage", display: "Primary Language" },
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
    display: "Addressed to: ",
    description:
      "Who the visa letter should be addressed to, e.g. Immigration Officer of X Embassy"
  }
};

export default validationFields;
