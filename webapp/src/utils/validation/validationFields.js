const validationFields = {
  idNumber: { name: "idNumber", display: "RSA ID Number" },
  passportNumber: { name: "passportNumber", display: "Passport Number" },
  countryOfIssue: { name: "countryOfIssue", display: "Country of Issue" },
  passportExpiry: { name: "passportExpiry", display: "Passport Expiry Date" },
  idType: { name: "idType", display: "Type of Identification" },
  employmentStartDate: {
    name: "employmentStartDate",
    display: "Employment start date",
  },
  title: { name: "title", display: "Title" },
  firstName: { name: "firstName", display: "First Name" },
  lastName: { name: "lastName", display: "Last Name" },
  email: { name: "email", display: "Email Address" },
  maritalStatus: { name: "maritalStatus", display: "Marital Status" },
  currentEmployer: { name: "currentEmployer", display: "Current Employer" },
  monthlySalary: { name: "monthlySalary", display: "Gross Monthly Salary (R)" },
  phoneNumber: { name: "phoneNumber", display: "Phone Number" },
  contactNumber: { name: "contactNumber", display: "Contact Number" },
  username: { name: "username", display: "Username" },
  password: { name: "password", display: "Password" },
  confirmPassword: { name: "confirmPassword", display: "Confirm Password" },
  gender: { name: "gender", display: "Gender" },
  dateOfBirth: { name: "upgradedateOfBirth", display: "Date of Birth" },

  firstNameAndSurname: {
    name: "firstNameAndSurname",
    display: "First Name & Surname",
  },
  mobileNumber: { name: "mobileNumber", display: "Mobile Number" },

  upgradeNameAndSuname: {
    name: "upgradeName",
    display: "Name & Surname",
  },
  upgradeEmailAddress: {
    name: "upgradeEmailAddress",
    display: "Email Address",
  },
  upgradeAlternateContactNumber: {
    name: "upgradeContactNumber",
    display: "Contact Number",
  },
  upgradeNumber: {
    name: "upgradeNumber",
    display: "Cell C Number you want to upgrade",
  },
  networkOptions: {
    name: "networkOptions",
    display: "Current Network",
  },
  accountType: {
    name: "accountType",
    display: "Account Type",
  },
  companyRegistrationNumber: {
    name: "companyRegistrationNumber",
    display: "Company Registration Number",
  },
  previousNetworkAccountNumbers: {
    name: "previousNetworkAccountNumbers",
    display: "Previous Account Number",
  },
}

export default validationFields
