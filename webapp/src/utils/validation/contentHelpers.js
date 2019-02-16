import { getNameList, getNames, getData } from "country-list";
export const titleOptions = [
  { value: "Mr", label: "Mr" },
  { value: "Mrs", label: "Mrs" },
  { value: "Ms", label: "Ms" },
  { value: "Hon", label: "Hon" },
  { value: "Prof", label: "Prof" },
  { value: "Dr", label: "Dr" }
];

export function getCounties() {
  const rawCountryData = getNames();
  let countries = [];
  rawCountryData.forEach(function(country) {
    countries.push({
      value: country.toLowerCase().replace(/\s/g, "_"),
      label: country
    });
  });
  return countries;
}
