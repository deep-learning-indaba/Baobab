// Country data with ISO codes, names, and flag emoji
// Flag emoji is derived from the ISO 3166-1 alpha-2 country code

const getFlag = (countryCode) => {
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
};

// Complete list of countries with ISO 3166-1 alpha-2 codes
export const ALL_COUNTRIES = [
  { code: 'AF', name: 'Afghanistan' },
  { code: 'AL', name: 'Albania' },
  { code: 'DZ', name: 'Algeria' },
  { code: 'AD', name: 'Andorra' },
  { code: 'AO', name: 'Angola' },
  { code: 'AG', name: 'Antigua and Barbuda' },
  { code: 'AR', name: 'Argentina' },
  { code: 'AM', name: 'Armenia' },
  { code: 'AU', name: 'Australia' },
  { code: 'AT', name: 'Austria' },
  { code: 'AZ', name: 'Azerbaijan' },
  { code: 'BS', name: 'Bahamas' },
  { code: 'BH', name: 'Bahrain' },
  { code: 'BD', name: 'Bangladesh' },
  { code: 'BB', name: 'Barbados' },
  { code: 'BY', name: 'Belarus' },
  { code: 'BE', name: 'Belgium' },
  { code: 'BZ', name: 'Belize' },
  { code: 'BJ', name: 'Benin' },
  { code: 'BT', name: 'Bhutan' },
  { code: 'BO', name: 'Bolivia' },
  { code: 'BA', name: 'Bosnia and Herzegovina' },
  { code: 'BW', name: 'Botswana' },
  { code: 'BR', name: 'Brazil' },
  { code: 'BN', name: 'Brunei' },
  { code: 'BG', name: 'Bulgaria' },
  { code: 'BF', name: 'Burkina Faso' },
  { code: 'BI', name: 'Burundi' },
  { code: 'CV', name: 'Cabo Verde' },
  { code: 'KH', name: 'Cambodia' },
  { code: 'CM', name: 'Cameroon' },
  { code: 'CA', name: 'Canada' },
  { code: 'CF', name: 'Central African Republic' },
  { code: 'TD', name: 'Chad' },
  { code: 'CL', name: 'Chile' },
  { code: 'CN', name: 'China' },
  { code: 'CO', name: 'Colombia' },
  { code: 'KM', name: 'Comoros' },
  { code: 'CG', name: 'Congo' },
  { code: 'CD', name: 'Congo (Democratic Republic)' },
  { code: 'CR', name: 'Costa Rica' },
  { code: 'CI', name: "Côte d'Ivoire" },
  { code: 'HR', name: 'Croatia' },
  { code: 'CU', name: 'Cuba' },
  { code: 'CY', name: 'Cyprus' },
  { code: 'CZ', name: 'Czechia' },
  { code: 'DK', name: 'Denmark' },
  { code: 'DJ', name: 'Djibouti' },
  { code: 'DM', name: 'Dominica' },
  { code: 'DO', name: 'Dominican Republic' },
  { code: 'EC', name: 'Ecuador' },
  { code: 'EG', name: 'Egypt' },
  { code: 'SV', name: 'El Salvador' },
  { code: 'GQ', name: 'Equatorial Guinea' },
  { code: 'ER', name: 'Eritrea' },
  { code: 'EE', name: 'Estonia' },
  { code: 'SZ', name: 'Eswatini' },
  { code: 'ET', name: 'Ethiopia' },
  { code: 'FJ', name: 'Fiji' },
  { code: 'FI', name: 'Finland' },
  { code: 'FR', name: 'France' },
  { code: 'GA', name: 'Gabon' },
  { code: 'GM', name: 'Gambia' },
  { code: 'GE', name: 'Georgia' },
  { code: 'DE', name: 'Germany' },
  { code: 'GH', name: 'Ghana' },
  { code: 'GR', name: 'Greece' },
  { code: 'GD', name: 'Grenada' },
  { code: 'GT', name: 'Guatemala' },
  { code: 'GN', name: 'Guinea' },
  { code: 'GW', name: 'Guinea-Bissau' },
  { code: 'GY', name: 'Guyana' },
  { code: 'HT', name: 'Haiti' },
  { code: 'HN', name: 'Honduras' },
  { code: 'HU', name: 'Hungary' },
  { code: 'IS', name: 'Iceland' },
  { code: 'IN', name: 'India' },
  { code: 'ID', name: 'Indonesia' },
  { code: 'IR', name: 'Iran' },
  { code: 'IQ', name: 'Iraq' },
  { code: 'IE', name: 'Ireland' },
  { code: 'IL', name: 'Israel' },
  { code: 'IT', name: 'Italy' },
  { code: 'JM', name: 'Jamaica' },
  { code: 'JP', name: 'Japan' },
  { code: 'JO', name: 'Jordan' },
  { code: 'KZ', name: 'Kazakhstan' },
  { code: 'KE', name: 'Kenya' },
  { code: 'KI', name: 'Kiribati' },
  { code: 'KP', name: 'Korea (North)' },
  { code: 'KR', name: 'Korea (South)' },
  { code: 'KW', name: 'Kuwait' },
  { code: 'KG', name: 'Kyrgyzstan' },
  { code: 'LA', name: 'Laos' },
  { code: 'LV', name: 'Latvia' },
  { code: 'LB', name: 'Lebanon' },
  { code: 'LS', name: 'Lesotho' },
  { code: 'LR', name: 'Liberia' },
  { code: 'LY', name: 'Libya' },
  { code: 'LI', name: 'Liechtenstein' },
  { code: 'LT', name: 'Lithuania' },
  { code: 'LU', name: 'Luxembourg' },
  { code: 'MG', name: 'Madagascar' },
  { code: 'MW', name: 'Malawi' },
  { code: 'MY', name: 'Malaysia' },
  { code: 'MV', name: 'Maldives' },
  { code: 'ML', name: 'Mali' },
  { code: 'MT', name: 'Malta' },
  { code: 'MH', name: 'Marshall Islands' },
  { code: 'MR', name: 'Mauritania' },
  { code: 'MU', name: 'Mauritius' },
  { code: 'MX', name: 'Mexico' },
  { code: 'FM', name: 'Micronesia' },
  { code: 'MD', name: 'Moldova' },
  { code: 'MC', name: 'Monaco' },
  { code: 'MN', name: 'Mongolia' },
  { code: 'ME', name: 'Montenegro' },
  { code: 'MA', name: 'Morocco' },
  { code: 'MZ', name: 'Mozambique' },
  { code: 'MM', name: 'Myanmar' },
  { code: 'NA', name: 'Namibia' },
  { code: 'NR', name: 'Nauru' },
  { code: 'NP', name: 'Nepal' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'NI', name: 'Nicaragua' },
  { code: 'NE', name: 'Niger' },
  { code: 'NG', name: 'Nigeria' },
  { code: 'MK', name: 'North Macedonia' },
  { code: 'NO', name: 'Norway' },
  { code: 'OM', name: 'Oman' },
  { code: 'PK', name: 'Pakistan' },
  { code: 'PW', name: 'Palau' },
  { code: 'PS', name: 'Palestine' },
  { code: 'PA', name: 'Panama' },
  { code: 'PG', name: 'Papua New Guinea' },
  { code: 'PY', name: 'Paraguay' },
  { code: 'PE', name: 'Peru' },
  { code: 'PH', name: 'Philippines' },
  { code: 'PL', name: 'Poland' },
  { code: 'PT', name: 'Portugal' },
  { code: 'QA', name: 'Qatar' },
  { code: 'RO', name: 'Romania' },
  { code: 'RU', name: 'Russia' },
  { code: 'RW', name: 'Rwanda' },
  { code: 'KN', name: 'Saint Kitts and Nevis' },
  { code: 'LC', name: 'Saint Lucia' },
  { code: 'VC', name: 'Saint Vincent and the Grenadines' },
  { code: 'WS', name: 'Samoa' },
  { code: 'SM', name: 'San Marino' },
  { code: 'ST', name: 'Sao Tome and Principe' },
  { code: 'SA', name: 'Saudi Arabia' },
  { code: 'SN', name: 'Senegal' },
  { code: 'RS', name: 'Serbia' },
  { code: 'SC', name: 'Seychelles' },
  { code: 'SL', name: 'Sierra Leone' },
  { code: 'SG', name: 'Singapore' },
  { code: 'SK', name: 'Slovakia' },
  { code: 'SI', name: 'Slovenia' },
  { code: 'SB', name: 'Solomon Islands' },
  { code: 'SO', name: 'Somalia' },
  { code: 'ZA', name: 'South Africa' },
  { code: 'SS', name: 'South Sudan' },
  { code: 'ES', name: 'Spain' },
  { code: 'LK', name: 'Sri Lanka' },
  { code: 'SD', name: 'Sudan' },
  { code: 'SR', name: 'Suriname' },
  { code: 'SE', name: 'Sweden' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'SY', name: 'Syria' },
  { code: 'TW', name: 'Taiwan' },
  { code: 'TJ', name: 'Tajikistan' },
  { code: 'TZ', name: 'Tanzania' },
  { code: 'TH', name: 'Thailand' },
  { code: 'TL', name: 'Timor-Leste' },
  { code: 'TG', name: 'Togo' },
  { code: 'TO', name: 'Tonga' },
  { code: 'TT', name: 'Trinidad and Tobago' },
  { code: 'TN', name: 'Tunisia' },
  { code: 'TR', name: 'Turkey' },
  { code: 'TM', name: 'Turkmenistan' },
  { code: 'TV', name: 'Tuvalu' },
  { code: 'UG', name: 'Uganda' },
  { code: 'UA', name: 'Ukraine' },
  { code: 'AE', name: 'United Arab Emirates' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'US', name: 'United States' },
  { code: 'UY', name: 'Uruguay' },
  { code: 'UZ', name: 'Uzbekistan' },
  { code: 'VU', name: 'Vanuatu' },
  { code: 'VA', name: 'Vatican City' },
  { code: 'VE', name: 'Venezuela' },
  { code: 'VN', name: 'Vietnam' },
  { code: 'YE', name: 'Yemen' },
  { code: 'ZM', name: 'Zambia' },
  { code: 'ZW', name: 'Zimbabwe' }
].map(c => ({ ...c, flag: getFlag(c.code) }));

// Region definitions with descriptive names and country codes
export const REGIONS = {
  // Continents
  AFRICA: {
    name: 'Africa',
    description: 'All African countries',
    countries: ['DZ', 'AO', 'BJ', 'BW', 'BF', 'BI', 'CV', 'CM', 'CF', 'TD', 'KM', 'CG', 'CD', 'CI', 'DJ', 'EG', 'GQ', 'ER', 'SZ', 'ET', 'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 'LS', 'LR', 'LY', 'MG', 'MW', 'ML', 'MR', 'MU', 'MA', 'MZ', 'NA', 'NE', 'NG', 'RW', 'ST', 'SN', 'SC', 'SL', 'SO', 'ZA', 'SS', 'SD', 'TZ', 'TG', 'TN', 'UG', 'ZM', 'ZW']
  },
  ASIA: {
    name: 'Asia',
    description: 'All Asian countries',
    countries: ['AF', 'AM', 'AZ', 'BH', 'BD', 'BT', 'BN', 'KH', 'CN', 'CY', 'GE', 'IN', 'ID', 'IR', 'IQ', 'IL', 'JP', 'JO', 'KZ', 'KW', 'KG', 'LA', 'LB', 'MY', 'MV', 'MN', 'MM', 'NP', 'KP', 'OM', 'PK', 'PS', 'PH', 'QA', 'SA', 'SG', 'KR', 'LK', 'SY', 'TW', 'TJ', 'TH', 'TL', 'TR', 'TM', 'AE', 'UZ', 'VN', 'YE']
  },
  EUROPE: {
    name: 'Europe',
    description: 'All European countries',
    countries: ['AL', 'AD', 'AT', 'BY', 'BE', 'BA', 'BG', 'HR', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'LV', 'LI', 'LT', 'LU', 'MT', 'MD', 'MC', 'ME', 'NL', 'MK', 'NO', 'PL', 'PT', 'RO', 'RU', 'SM', 'RS', 'SK', 'SI', 'ES', 'SE', 'CH', 'UA', 'GB', 'VA']
  },
  NORTH_AMERICA: {
    name: 'North America',
    description: 'All North American countries',
    countries: ['AG', 'BS', 'BB', 'BZ', 'CA', 'CR', 'CU', 'DM', 'DO', 'SV', 'GD', 'GT', 'HT', 'HN', 'JM', 'MX', 'NI', 'PA', 'KN', 'LC', 'VC', 'TT', 'US']
  },
  SOUTH_AMERICA: {
    name: 'South America',
    description: 'All South American countries',
    countries: ['AR', 'BO', 'BR', 'CL', 'CO', 'EC', 'GY', 'PY', 'PE', 'SR', 'UY', 'VE']
  },
  OCEANIA: {
    name: 'Oceania',
    description: 'Australia, New Zealand, and Pacific Islands',
    countries: ['AU', 'FJ', 'KI', 'MH', 'FM', 'NR', 'NZ', 'PW', 'PG', 'WS', 'SB', 'TO', 'TV', 'VU']
  },

  // Business/Political Regions
  MENA: {
    name: 'MENA',
    description: 'Middle East and North Africa',
    countries: ['DZ', 'BH', 'EG', 'IR', 'IQ', 'IL', 'JO', 'KW', 'LB', 'LY', 'MA', 'OM', 'PS', 'QA', 'SA', 'SY', 'TN', 'AE', 'YE']
  },
  EMEA: {
    name: 'EMEA',
    description: 'Europe, Middle East, and Africa',
    countries: [] // Computed below
  },
  APAC: {
    name: 'APAC',
    description: 'Asia-Pacific',
    countries: ['AU', 'BD', 'BN', 'KH', 'CN', 'FJ', 'IN', 'ID', 'JP', 'KI', 'LA', 'MY', 'MV', 'MH', 'FM', 'MN', 'MM', 'NR', 'NP', 'NZ', 'KP', 'PK', 'PW', 'PG', 'PH', 'WS', 'SG', 'SB', 'KR', 'LK', 'TW', 'TH', 'TL', 'TO', 'TV', 'VU', 'VN']
  },
  LATAM: {
    name: 'LATAM',
    description: 'Latin America',
    countries: ['AR', 'BO', 'BR', 'CL', 'CO', 'CR', 'CU', 'DO', 'EC', 'SV', 'GT', 'HT', 'HN', 'MX', 'NI', 'PA', 'PY', 'PE', 'PR', 'UY', 'VE']
  },
  EU: {
    name: 'European Union',
    description: 'European Union member states',
    countries: ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']
  },
  SUB_SAHARAN_AFRICA: {
    name: 'Sub-Saharan Africa',
    description: 'African countries south of the Sahara',
    countries: ['AO', 'BJ', 'BW', 'BF', 'BI', 'CV', 'CM', 'CF', 'TD', 'KM', 'CG', 'CD', 'CI', 'GQ', 'ER', 'SZ', 'ET', 'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 'LS', 'LR', 'MG', 'MW', 'ML', 'MR', 'MU', 'MZ', 'NA', 'NE', 'NG', 'RW', 'ST', 'SN', 'SC', 'SL', 'SO', 'ZA', 'SS', 'SD', 'TZ', 'TG', 'UG', 'ZM', 'ZW']
  },
  GULF_STATES: {
    name: 'Gulf States',
    description: 'Persian Gulf countries (GCC)',
    countries: ['BH', 'KW', 'OM', 'QA', 'SA', 'AE']
  },
  SOUTHEAST_ASIA: {
    name: 'Southeast Asia',
    description: 'Southeast Asian countries',
    countries: ['BN', 'KH', 'ID', 'LA', 'MY', 'MM', 'PH', 'SG', 'TH', 'TL', 'VN']
  },
  EAST_ASIA: {
    name: 'East Asia',
    description: 'East Asian countries',
    countries: ['CN', 'JP', 'KP', 'KR', 'MN', 'TW']
  },
  SOUTH_ASIA: {
    name: 'South Asia',
    description: 'South Asian countries',
    countries: ['AF', 'BD', 'BT', 'IN', 'MV', 'NP', 'PK', 'LK']
  },
  CENTRAL_ASIA: {
    name: 'Central Asia',
    description: 'Central Asian countries',
    countries: ['KZ', 'KG', 'TJ', 'TM', 'UZ']
  },
  CARIBBEAN: {
    name: 'Caribbean',
    description: 'Caribbean countries',
    countries: ['AG', 'BS', 'BB', 'CU', 'DM', 'DO', 'GD', 'HT', 'JM', 'KN', 'LC', 'VC', 'TT']
  },
  NORDIC: {
    name: 'Nordic Countries',
    description: 'Scandinavian and Nordic countries',
    countries: ['DK', 'FI', 'IS', 'NO', 'SE']
  },
  COMMONWEALTH: {
    name: 'Commonwealth',
    description: 'Commonwealth of Nations members',
    countries: ['AG', 'AU', 'BS', 'BD', 'BB', 'BZ', 'BW', 'BN', 'CM', 'CA', 'CY', 'DM', 'FJ', 'GM', 'GH', 'GD', 'GY', 'IN', 'JM', 'KE', 'KI', 'LS', 'MW', 'MY', 'MV', 'MT', 'MU', 'MZ', 'NA', 'NR', 'NZ', 'NG', 'PK', 'PG', 'RW', 'KN', 'LC', 'VC', 'WS', 'SC', 'SL', 'SG', 'SB', 'ZA', 'LK', 'SZ', 'TZ', 'TO', 'TT', 'TV', 'UG', 'GB', 'VU', 'ZM']
  }
};

// Compute EMEA as union of Europe, Middle East (from MENA), and Africa
REGIONS.EMEA.countries = [...new Set([
  ...REGIONS.EUROPE.countries,
  ...REGIONS.MENA.countries,
  ...REGIONS.AFRICA.countries
])];

// Region categories for grouping in UI
export const REGION_CATEGORIES = {
  continents: {
    label: 'Continents',
    regions: ['AFRICA', 'ASIA', 'EUROPE', 'NORTH_AMERICA', 'SOUTH_AMERICA', 'OCEANIA']
  },
  business: {
    label: 'Business Regions',
    regions: ['MENA', 'EMEA', 'APAC', 'LATAM']
  },
  political: {
    label: 'Political/Economic',
    regions: ['EU', 'GULF_STATES', 'COMMONWEALTH', 'NORDIC']
  },
  subregions: {
    label: 'Sub-regions',
    regions: ['SUB_SAHARAN_AFRICA', 'SOUTHEAST_ASIA', 'EAST_ASIA', 'SOUTH_ASIA', 'CENTRAL_ASIA', 'CARIBBEAN']
  }
};

// Utility functions

/**
 * Get country object by code
 */
export const getCountryByCode = (code) => {
  return ALL_COUNTRIES.find(c => c.code === code);
};

/**
 * Get countries for a given region
 */
export const getCountriesForRegion = (regionKey) => {
  const region = REGIONS[regionKey];
  if (!region) return [];
  return region.countries
    .map(code => getCountryByCode(code))
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
};

/**
 * Get countries for multiple regions (union)
 */
export const getCountriesForRegions = (regionKeys) => {
  const allCodes = new Set();
  regionKeys.forEach(key => {
    const region = REGIONS[key];
    if (region) {
      region.countries.forEach(code => allCodes.add(code));
    }
  });
  return Array.from(allCodes)
    .map(code => getCountryByCode(code))
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
};

/**
 * Get countries from a list of country codes
 */
export const getCountriesByCodes = (codes) => {
  return codes
    .map(code => getCountryByCode(code))
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
};

/**
 * Build the final list of countries from settings (regions + individual countries)
 */
export const buildCountryList = (settings) => {
  if (!settings) return ALL_COUNTRIES;
  
  const { regions = [], countries = [], excludeCountries = [] } = settings;
  
  // If no regions or countries specified, return all
  if (regions.length === 0 && countries.length === 0) {
    return ALL_COUNTRIES;
  }
  
  const allCodes = new Set();
  
  // Add countries from regions
  regions.forEach(regionKey => {
    const region = REGIONS[regionKey];
    if (region) {
      region.countries.forEach(code => allCodes.add(code));
    }
  });
  
  // Add individual countries
  countries.forEach(code => allCodes.add(code));
  
  // Remove excluded countries
  excludeCountries.forEach(code => allCodes.delete(code));
  
  return Array.from(allCodes)
    .map(code => getCountryByCode(code))
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
};

/**
 * Convert countries to react-select options format
 */
export const countriesToOptions = (countries) => {
  return countries.map(country => ({
    value: country.code,
    label: `${country.flag} ${country.name}`,
    country
  }));
};

/**
 * Get region options for react-select
 */
export const getRegionOptions = () => {
  return Object.entries(REGION_CATEGORIES).map(([categoryKey, category]) => ({
    label: category.label,
    options: category.regions.map(regionKey => ({
      value: regionKey,
      label: REGIONS[regionKey].name,
      description: REGIONS[regionKey].description,
      countryCount: REGIONS[regionKey].countries.length
    }))
  }));
};

/**
 * Get flat list of all region options
 */
export const getAllRegionOptions = () => {
  return Object.keys(REGIONS).map(key => ({
    value: key,
    label: REGIONS[key].name,
    description: REGIONS[key].description,
    countryCount: REGIONS[key].countries.length
  }));
};

/**
 * Get all country options for react-select
 */
export const getAllCountryOptions = () => {
  return countriesToOptions(ALL_COUNTRIES);
};

export { getFlag };
