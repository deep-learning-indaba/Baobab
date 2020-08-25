// TODO: HOW TO TRANSLATE THESE?
export const isRequiredDropdown = fieldName => `${fieldName} is required`;
export const isRequiredText = fieldName => `${fieldName} is required`;
export const isRequiredCheckBox = fieldName => `${fieldName} is required`;
export const isNotValidEmail = fieldName =>
  `${fieldName} is not a valid email address`;
export const isNotValid = fieldName => `${fieldName} is not valid`;
export const minLength = length => {
  return fieldName => `${fieldName} must be at least ${length} characters`;
};
export const maxLength = length => {
  return fieldName => `${fieldName} must be less than ${length} characters`;
};
export const isNotValidUsername = fieldName =>
  `Please enter a valid email or cell phone number`;
export const isNotValidDate = fieldName => `${fieldName} is not a valid date.`;
