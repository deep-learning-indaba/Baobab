import React, { useState, useMemo } from 'react';
import { default as ReactSelect } from 'react-select';
import {
  REGIONS,
  REGION_CATEGORIES,
  ALL_COUNTRIES,
  getCountriesForRegions,
  buildCountryList
} from '../../../utils/countryData';

const selectStyles = (multiValueColors) => ({
  control: (base, state) => ({
    ...base,
    minHeight: '38px',
    fontSize: '0.9rem',
    borderColor: state.isFocused ? '#0132c5' : '#bfc9c1',
    boxShadow: state.isFocused ? '0 0 0 3px rgba(1, 50, 197, 0.1)' : 'none',
    '&:hover': { borderColor: '#0132c5' }
  }),
  multiValue: base => ({ ...base, backgroundColor: multiValueColors.bg, borderRadius: '4px' }),
  multiValueLabel: base => ({ ...base, color: multiValueColors.text, fontWeight: 500 }),
  multiValueRemove: base => ({
    ...base,
    color: multiValueColors.text,
    '&:hover': { backgroundColor: multiValueColors.hoverBg, color: multiValueColors.hoverText }
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isSelected ? '#0132c5' : state.isFocused ? '#e8ecfb' : 'white',
    color: state.isSelected ? 'white' : '#333',
    cursor: 'pointer'
  }),
  groupHeading: base => ({
    ...base,
    fontWeight: 600,
    fontSize: '0.75rem',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  })
});

const CountryEditor = ({ settings, onChange, t }) => {
  const [showAllCountries, setShowAllCountries] = useState(false);

  const safeSettings = settings || {};
  const { regions = [], countries = [], excludeCountries = [] } = safeSettings;

  const regionOptions = useMemo(() => (
    Object.entries(REGION_CATEGORIES).map(([, category]) => ({
      label: category.label,
      options: category.regions.map(regionKey => ({
        value: regionKey,
        label: `${REGIONS[regionKey].name} (${REGIONS[regionKey].countries.length} countries)`,
        description: REGIONS[regionKey].description
      }))
    }))
  ), []);

  const countryOptions = useMemo(() => (
    ALL_COUNTRIES.map(country => ({ value: country.code, label: `${country.flag} ${country.name}`, country }))
  ), []);

  const selectedRegions = useMemo(() => (
    regions.map(regionKey => {
      const region = REGIONS[regionKey];
      return region ? { value: regionKey, label: `${region.name} (${region.countries.length} countries)`, description: region.description } : null;
    }).filter(Boolean)
  ), [regions]);

  const selectedCountries = useMemo(() => (
    countries.map(code => {
      const country = ALL_COUNTRIES.find(c => c.code === code);
      return country ? { value: country.code, label: `${country.flag} ${country.name}`, country } : null;
    }).filter(Boolean)
  ), [countries]);

  const excludedCountries = useMemo(() => (
    excludeCountries.map(code => {
      const country = ALL_COUNTRIES.find(c => c.code === code);
      return country ? { value: country.code, label: `${country.flag} ${country.name}`, country } : null;
    }).filter(Boolean)
  ), [excludeCountries]);

  const previewCountries = useMemo(() => buildCountryList(settings), [settings]);
  const countriesFromRegions = useMemo(() => (regions.length ? getCountriesForRegions(regions) : []), [regions]);

  const handleRegionsChange = (selected) => onChange({ ...settings, regions: selected ? selected.map(o => o.value) : [] });
  const handleCountriesChange = (selected) => onChange({ ...settings, countries: selected ? selected.map(o => o.value) : [] });
  const handleExcludeChange = (selected) => onChange({ ...settings, excludeCountries: selected ? selected.map(o => o.value) : [] });
  const handleClearAll = () => onChange({ regions: [], countries: [], excludeCountries: [] });

  const formatRegionOption = ({ label, description }, { context }) => {
    if (context === 'menu') {
      return (
        <div className="py-0.5">
          <div className="font-medium">{label}</div>
          {description && <div className="text-xs text-muted-foreground mt-0.5">{description}</div>}
        </div>
      );
    }
    return label;
  };

  const countryFilter = (option, inputValue) => {
    if (!inputValue) return true;
    const s = inputValue.toLowerCase();
    return option.data.country.name.toLowerCase().includes(s) || option.data.country.code.toLowerCase().includes(s);
  };

  const hasSelections = regions.length > 0 || countries.length > 0;

  const gridItemCls = (isSelected, isFromRegion, isExcluded) => {
    const base = 'flex flex-col items-center justify-center p-1.5 rounded border cursor-pointer transition-colors';
    if (isExcluded) return `${base} bg-error-container border-error opacity-60`;
    if (isSelected) return `${base} bg-[#dcfce7] border-[#22c55e]`;
    if (isFromRegion) return `${base} bg-action/10 border-action/40`;
    return `${base} bg-white border-border hover:bg-surface-low`;
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-4 mt-3">
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-foreground mb-1">{t('Country Selection')}</h4>
        <p className="text-xs text-muted-foreground">
          {t('Select regions to include groups of countries, or add individual countries. Leave empty to include all countries.')}
        </p>
      </div>

      {/* Regions */}
      <div className="mb-4">
        <label className="flex items-center gap-1.5 text-sm font-medium text-foreground mb-1.5">
          <i className="fas fa-globe-africa text-muted-foreground text-[0.9em]"></i>
          {t('Include Regions')}
        </label>
        <ReactSelect
          isMulti
          options={regionOptions}
          value={selectedRegions}
          onChange={handleRegionsChange}
          placeholder={t('Select regions to include...')}
          formatOptionLabel={formatRegionOption}
          styles={selectStyles({ bg: '#e8ecfb', text: '#3730a3', hoverBg: '#c7d2fe', hoverText: '#1e1b4b' })}
        />
      </div>

      {/* Individual countries */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1.5">
          <label className="flex items-center gap-1.5 text-sm font-medium text-foreground">
            <i className="fas fa-plus-circle text-muted-foreground text-[0.9em]"></i>
            {t('Add Individual Countries')}
          </label>
          <button
            type="button"
            onClick={() => setShowAllCountries(!showAllCountries)}
            className="flex items-center gap-1 px-2 py-1 text-xs text-action border border-action rounded cursor-pointer hover:bg-action/5 transition-colors bg-transparent"
          >
            <i className={`fas fa-chevron-${showAllCountries ? 'up' : 'down'} text-[0.7em]`}></i>
            {showAllCountries ? t('Hide country list') : t('Show all countries')}
          </button>
        </div>
        <ReactSelect
          isMulti
          options={countryOptions}
          value={selectedCountries}
          onChange={handleCountriesChange}
          placeholder={t('Search and add individual countries...')}
          filterOption={countryFilter}
          styles={selectStyles({ bg: '#dcfce7', text: '#166534', hoverBg: '#bbf7d0', hoverText: '#14532d' })}
        />
      </div>

      {/* Country grid */}
      {showAllCountries && (
        <div
          className="grid gap-1 max-h-[300px] overflow-y-auto p-2 bg-white border border-border rounded-md mt-2 mb-4"
          style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(60px, 1fr))' }}
        >
          {ALL_COUNTRIES.map(country => {
            const isSelected = countries.includes(country.code);
            const isFromRegion = countriesFromRegions.some(c => c.code === country.code);
            const isExcluded = excludeCountries.includes(country.code);
            return (
              <button
                key={country.code}
                type="button"
                className={gridItemCls(isSelected, isFromRegion, isExcluded)}
                onClick={() => {
                  if (isSelected) {
                    handleCountriesChange(selectedCountries.filter(c => c.value !== country.code));
                  } else {
                    handleCountriesChange([...selectedCountries, { value: country.code, label: `${country.flag} ${country.name}`, country }]);
                  }
                }}
                title={country.name}
              >
                <span className="text-2xl leading-none">{country.flag}</span>
                <span className="text-[0.65rem] text-muted-foreground mt-0.5">{country.code}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Exclude countries */}
      {hasSelections && (
        <div className="mb-4">
          <label className="flex items-center gap-1.5 text-sm font-medium text-foreground mb-1">
            <i className="fas fa-minus-circle text-muted-foreground text-[0.9em]"></i>
            {t('Exclude Countries')}
          </label>
          <p className="text-xs text-muted-foreground mb-1.5">{t('Remove specific countries from the selected regions')}</p>
          <ReactSelect
            isMulti
            options={countryOptions}
            value={excludedCountries}
            onChange={handleExcludeChange}
            placeholder={t('Select countries to exclude...')}
            filterOption={countryFilter}
            styles={selectStyles({ bg: '#fee2e2', text: '#991b1b', hoverBg: '#fecaca', hoverText: '#7f1d1d' })}
          />
        </div>
      )}

      {/* Preview */}
      <div className="bg-white border border-border rounded-md p-3 mt-4">
        <div className="flex justify-between items-center mb-2">
          <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
            <i className="fas fa-eye text-muted-foreground"></i>
            {t('Preview')}
          </span>
          <span className="text-xs text-muted-foreground bg-surface px-2 py-0.5 rounded-full">
            {previewCountries.length === ALL_COUNTRIES.length
              ? t('All countries ({{count}})', { count: previewCountries.length })
              : t('{{count}} countries selected', { count: previewCountries.length })}
          </span>
        </div>
        {previewCountries.length > 0 && previewCountries.length <= 50 && (
          <div className="flex flex-wrap gap-1">
            {previewCountries.map(country => (
              <span key={country.code} className="text-xl leading-none cursor-default" title={country.name}>{country.flag}</span>
            ))}
          </div>
        )}
        {previewCountries.length > 50 && (
          <div className="flex flex-wrap gap-1 items-center">
            {previewCountries.slice(0, 40).map(country => (
              <span key={country.code} className="text-xl leading-none cursor-default" title={country.name}>{country.flag}</span>
            ))}
            <span className="flex items-center text-xs text-muted-foreground px-2 py-0.5 bg-surface rounded">
              +{previewCountries.length - 40} {t('more')}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      {hasSelections && (
        <div className="flex gap-2 mt-3">
          <button
            type="button"
            onClick={handleClearAll}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted-foreground bg-white border border-border rounded cursor-pointer hover:bg-surface hover:text-foreground transition-colors"
          >
            <i className="fas fa-times"></i>
            {t('Clear selections (include all)')}
          </button>
        </div>
      )}
    </div>
  );
};

export default CountryEditor;
