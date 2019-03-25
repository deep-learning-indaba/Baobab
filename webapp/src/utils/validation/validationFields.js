const validationFields = {
  email: { name: "email", display: "Email Address" },
  title: { name: "title", display: "Title" },
  firstName: { name: "firstName", display: "First Name" },
  lastName: { name: "lastName", display: "Last Name" },
  gender: { name: "gender", display: "Gender" },
  nationality: { name: "nationality", display: "Country of Nationality" },
  residence: { name: "residence", display: "Country of Residence" },
  ethnicity: { name: "ethnicity", display: "Ethnicity", description: "We use South African demographic groupings for reporting." },
  affiliation: { name: "affiliation", display: "Affiliation", description: "Please enter the name of your university if academic or student, or the name of your company if industry professional" },
  department: { name: "department", display: "Department", description: "Please enter the name of your faculty if academic or student, the department you work for if industry professional or N/A if not applicable." },
  disability: {
    name: "disability",
    display: "Disability",
    placeholder: "Type of Disability or None",
    description: "We use the Washington Group difficulty schemes, and it helps us to ensure that our facilities can accommodate the needs of all attendees."
  },
  username: { name: "username", display: "Username" },
  password: { name: "password", display: "Password" },
  category: { name: "category", display: "User Category", description: "If you are a part-time student working as an academic, choose academic. Similarly for industry." },
  confirmPassword: { name: "confirmPassword", display: "Confirm Password" },
  dateOfBirth: { name: "dateOfBirth", display: "Date of Birth" },
  primaryLanguage: {name: "primaryLanguage", display: "Primary Language"}
};

export default validationFields;
