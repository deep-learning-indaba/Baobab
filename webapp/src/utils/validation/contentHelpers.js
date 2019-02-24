import { getNameList, getNames, getData } from "country-list";
import { getContent } from "../../services/content";
export const getTitleOptions = getContent("title");
export const getGenderOptions = getContent("gender");
export const getCounties = getContent("countries");
export const getCategories = getContent("categories");
export const getEthnicityOptions = getContent("ethnicity");
export const getDisabilityOptions = getContent("disability");
