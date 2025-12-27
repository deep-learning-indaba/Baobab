import React, { useState, useMemo } from 'react';
import { default as ReactSelect } from 'react-select';
import {
  REGIONS,
  REGION_CATEGORIES,
  ALL_COUNTRIES,
  getCountriesForRegions,
  buildCountryList
} from '../../../utils/countryData';
import './CountryEditor.css';

const CountryEditor = ({ settings, onChange, t }) => {
  const [showAllCountries, setShowAllCountries] = useState(false);
  
  // Handle null/undefined settings
  const safeSettings = settings || {};
  const {
    regions = [],
    countries = [],
    excludeCountries = []
  } = safeSettings;

  // Build region options grouped by category
  const regionOptions = useMemo(() => {
    return Object.entries(REGION_CATEGORIES).map(([categoryKey, category]) => ({
      label: category.label,
      options: category.regions.map(regionKey => ({
        value: regionKey,
        label: `${REGIONS[regionKey].name} (${REGIONS[regionKey].countries.length} countries)`,
        description: REGIONS[regionKey].description
      }))
    }));
  }, []);

  // Build country options
  const countryOptions = useMemo(() => {
    return ALL_COUNTRIES.map(country => ({
      value: country.code,
      label: `${country.flag} ${country.name}`,
      country
    }));
  }, []);

  // Get currently selected region values
  const selectedRegions = useMemo(() => {
    return regions.map(regionKey => {
      const region = REGIONS[regionKey];
      return region ? {
        value: regionKey,
        label: `${region.name} (${region.countries.length} countries)`,
        description: region.description
      } : null;
    }).filter(Boolean);
  }, [regions]);

  // Get currently selected country values
  const selectedCountries = useMemo(() => {
    return countries.map(code => {
      const country = ALL_COUNTRIES.find(c => c.code === code);
      return country ? {
        value: country.code,
        label: `${country.flag} ${country.name}`,
        country
      } : null;
    }).filter(Boolean);
  }, [countries]);

  // Get excluded country values
  const excludedCountries = useMemo(() => {
    return excludeCountries.map(code => {
      const country = ALL_COUNTRIES.find(c => c.code === code);
      return country ? {
        value: country.code,
        label: `${country.flag} ${country.name}`,
        country
      } : null;
    }).filter(Boolean);
  }, [excludeCountries]);

  // Preview of included countries
  const previewCountries = useMemo(() => {
    return buildCountryList(settings);
  }, [settings]);

  const handleRegionsChange = (selected) => {
    const newRegions = selected ? selected.map(opt => opt.value) : [];
    onChange({
      ...settings,
      regions: newRegions
    });
  };

  const handleCountriesChange = (selected) => {
    const newCountries = selected ? selected.map(opt => opt.value) : [];
    onChange({
      ...settings,
      countries: newCountries
    });
  };

  const handleExcludeChange = (selected) => {
    const newExclude = selected ? selected.map(opt => opt.value) : [];
    onChange({
      ...settings,
      excludeCountries: newExclude
    });
  };

  const handleClearAll = () => {
    onChange({
      regions: [],
      countries: [],
      excludeCountries: []
    });
  };

  // Format option with description for regions
  const formatRegionOption = ({ label, description }, { context }) => {
    if (context === 'menu') {
      return (
        <div className="region-option">
          <div className="region-option-label">{label}</div>
          {description && <div className="region-option-description">{description}</div>}
        </div>
      );
    }
    return label;
  };

  // Countries that come from selected regions (for reference)
  const countriesFromRegions = useMemo(() => {
    if (regions.length === 0) return [];
    return getCountriesForRegions(regions);
  }, [regions]);

  const hasSelections = regions.length > 0 || countries.length > 0;

  return (
    <div className="country-editor">
      <div className="country-editor-header">
        <h4>{t('Country Selection')}</h4>
        <p className="country-editor-hint">
          {t('Select regions to include groups of countries, or add individual countries. Leave empty to include all countries.')}
        </p>
      </div>

      <div className="country-editor-section">
        <label className="country-editor-label">
          <i className="fas fa-globe-africa"></i>
          {t('Include Regions')}
        </label>
        <ReactSelect
          isMulti
          options={regionOptions}
          value={selectedRegions}
          onChange={handleRegionsChange}
          placeholder={t('Select regions to include...')}
          formatOptionLabel={formatRegionOption}
          className="country-editor-select"
          classNamePrefix="country-select"
          styles={{
            control: (base, state) => ({
              ...base,
              minHeight: '38px',
              borderColor: state.isFocused ? '#3b82f6' : '#d1d5db',
              boxShadow: state.isFocused ? '0 0 0 3px rgba(59, 130, 246, 0.1)' : 'none',
              '&:hover': { borderColor: '#3b82f6' }
            }),
            multiValue: base => ({
              ...base,
              backgroundColor: '#e0e7ff',
              borderRadius: '4px'
            }),
            multiValueLabel: base => ({
              ...base,
              color: '#3730a3',
              fontWeight: 500
            }),
            multiValueRemove: base => ({
              ...base,
              color: '#3730a3',
              '&:hover': {
                backgroundColor: '#c7d2fe',
                color: '#1e1b4b'
              }
            }),
            option: (base, state) => ({
              ...base,
              backgroundColor: state.isSelected 
                ? '#3b82f6' 
                : state.isFocused 
                  ? '#eff6ff' 
                  : 'white',
              color: state.isSelected ? 'white' : '#333'
            }),
            groupHeading: base => ({
              ...base,
              fontWeight: 600,
              fontSize: '0.75rem',
              color: '#6b7280',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            })
          }}
        />
      </div>

      <div className="country-editor-section">
        <div className="country-editor-label-row">
          <label className="country-editor-label">
            <i className="fas fa-plus-circle"></i>
            {t('Add Individual Countries')}
          </label>
          <button
            type="button"
            className="country-toggle-btn"
            onClick={() => setShowAllCountries(!showAllCountries)}
          >
            {showAllCountries ? (
              <>
                <i className="fas fa-chevron-up"></i>
                {t('Hide country list')}
              </>
            ) : (
              <>
                <i className="fas fa-chevron-down"></i>
                {t('Show all countries')}
              </>
            )}
          </button>
        </div>
        <ReactSelect
          isMulti
          options={countryOptions}
          value={selectedCountries}
          onChange={handleCountriesChange}
          placeholder={t('Search and add individual countries...')}
          className="country-editor-select"
          classNamePrefix="country-select"
          filterOption={(option, inputValue) => {
            if (!inputValue) return true;
            const searchLower = inputValue.toLowerCase();
            return (
              option.data.country.name.toLowerCase().includes(searchLower) ||
              option.data.country.code.toLowerCase().includes(searchLower)
            );
          }}
          styles={{
            control: (base, state) => ({
              ...base,
              minHeight: '38px',
              borderColor: state.isFocused ? '#3b82f6' : '#d1d5db',
              boxShadow: state.isFocused ? '0 0 0 3px rgba(59, 130, 246, 0.1)' : 'none',
              '&:hover': { borderColor: '#3b82f6' }
            }),
            multiValue: base => ({
              ...base,
              backgroundColor: '#dcfce7',
              borderRadius: '4px'
            }),
            multiValueLabel: base => ({
              ...base,
              color: '#166534',
              fontWeight: 500
            }),
            multiValueRemove: base => ({
              ...base,
              color: '#166534',
              '&:hover': {
                backgroundColor: '#bbf7d0',
                color: '#14532d'
              }
            }),
            option: (base, state) => ({
              ...base,
              backgroundColor: state.isSelected 
                ? '#3b82f6' 
                : state.isFocused 
                  ? '#eff6ff' 
                  : 'white',
              color: state.isSelected ? 'white' : '#333'
            })
          }}
        />
      </div>

      {showAllCountries && (
        <div className="country-grid">
          {ALL_COUNTRIES.map(country => {
            const isSelected = countries.includes(country.code);
            const isFromRegion = countriesFromRegions.some(c => c.code === country.code);
            const isExcluded = excludeCountries.includes(country.code);
            
            return (
              <button
                key={country.code}
                type="button"
                className={`country-grid-item ${isSelected ? 'selected' : ''} ${isFromRegion ? 'from-region' : ''} ${isExcluded ? 'excluded' : ''}`}
                onClick={() => {
                  if (isSelected) {
                    handleCountriesChange(selectedCountries.filter(c => c.value !== country.code));
                  } else {
                    handleCountriesChange([...selectedCountries, { value: country.code, label: `${country.flag} ${country.name}`, country }]);
                  }
                }}
                title={country.name}
              >
                <span className="country-grid-flag">{country.flag}</span>
                <span className="country-grid-code">{country.code}</span>
              </button>
            );
          })}
        </div>
      )}

      {hasSelections && (
        <div className="country-editor-section">
          <label className="country-editor-label">
            <i className="fas fa-minus-circle"></i>
            {t('Exclude Countries')}
          </label>
          <p className="country-editor-hint">
            {t('Remove specific countries from the selected regions')}
          </p>
          <ReactSelect
            isMulti
            options={countryOptions}
            value={excludedCountries}
            onChange={handleExcludeChange}
            placeholder={t('Select countries to exclude...')}
            className="country-editor-select"
            classNamePrefix="country-select"
            filterOption={(option, inputValue) => {
              if (!inputValue) return true;
              const searchLower = inputValue.toLowerCase();
              return (
                option.data.country.name.toLowerCase().includes(searchLower) ||
                option.data.country.code.toLowerCase().includes(searchLower)
              );
            }}
            styles={{
              control: (base, state) => ({
                ...base,
                minHeight: '38px',
                borderColor: state.isFocused ? '#3b82f6' : '#d1d5db',
                boxShadow: state.isFocused ? '0 0 0 3px rgba(59, 130, 246, 0.1)' : 'none',
                '&:hover': { borderColor: '#3b82f6' }
              }),
              multiValue: base => ({
                ...base,
                backgroundColor: '#fee2e2',
                borderRadius: '4px'
              }),
              multiValueLabel: base => ({
                ...base,
                color: '#991b1b',
                fontWeight: 500
              }),
              multiValueRemove: base => ({
                ...base,
                color: '#991b1b',
                '&:hover': {
                  backgroundColor: '#fecaca',
                  color: '#7f1d1d'
                }
              }),
              option: (base, state) => ({
                ...base,
                backgroundColor: state.isSelected 
                  ? '#3b82f6' 
                  : state.isFocused 
                    ? '#eff6ff' 
                    : 'white',
                color: state.isSelected ? 'white' : '#333'
              })
            }}
          />
        </div>
      )}

      <div className="country-editor-preview">
        <div className="country-preview-header">
          <span className="country-preview-title">
            <i className="fas fa-eye"></i>
            {t('Preview')}
          </span>
          <span className="country-preview-count">
            {previewCountries.length === ALL_COUNTRIES.length
              ? t('All countries ({{count}})', { count: previewCountries.length })
              : t('{{count}} countries selected', { count: previewCountries.length })}
          </span>
        </div>
        {previewCountries.length > 0 && previewCountries.length <= 50 && (
          <div className="country-preview-list">
            {previewCountries.map(country => (
              <span key={country.code} className="country-preview-item" title={country.name}>
                {country.flag}
              </span>
            ))}
          </div>
        )}
        {previewCountries.length > 50 && (
          <div className="country-preview-overflow">
            {previewCountries.slice(0, 40).map(country => (
              <span key={country.code} className="country-preview-item" title={country.name}>
                {country.flag}
              </span>
            ))}
            <span className="country-preview-more">
              +{previewCountries.length - 40} {t('more')}
            </span>
          </div>
        )}
      </div>

      <div className="country-editor-actions">
        {hasSelections && (
          <button
            type="button"
            className="country-action-btn country-action-clear"
            onClick={handleClearAll}
          >
            <i className="fas fa-times"></i>
            {t('Clear selections (include all)')}
          </button>
        )}
      </div>
    </div>
  );
};

export default CountryEditor;
