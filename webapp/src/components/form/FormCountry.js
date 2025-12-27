import React from "react";
import FormGroup from "./FormGroup";
import { default as ReactSelect, components } from "react-select";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import MarkdownRenderer from "../MarkdownRenderer";
import { buildCountryList, countriesToOptions, getCountryByCode } from "../../utils/countryData";

// Note: Country options are stored in question.settings.countryOptions, not question.options
// The 'options' prop passed to this component should be settings.countryOptions

// Custom option component with flag
const CountryOption = (props) => {
  const { data } = props;
  return (
    <components.Option {...props}>
      <span className="country-option">
        <span className="country-flag" role="img" aria-label={data.country && data.country.name}>
          {data.country?.flag}
        </span>
        <span className="country-name">{data.country && data.country.name}</span>
      </span>
    </components.Option>
  );
};

// Custom single value component with flag
const CountrySingleValue = (props) => {
  const { data } = props;
  return (
    <components.SingleValue {...props}>
      <span className="country-option">
        <span className="country-flag" role="img" aria-label={data.country && data.country.name}>
          {data.country?.flag}
        </span>
        <span className="country-name">{data.country && data.country.name}</span>
      </span>
    </components.SingleValue>
  );
};

class FormCountry extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.selectRef?.focus();
    }
  }

  getOptions = () => {
    const { options } = this.props;
    
    // Build country list from settings (regions + individual countries)
    // options format: { regions: ['AFRICA', 'MENA'], countries: ['US', 'GB'], excludeCountries: ['ZW'] }
    const countries = buildCountryList(options);
    return countriesToOptions(countries);
  };

  getValue = () => {
    const { value } = this.props;
    if (!value) return null;
    
    const country = getCountryByCode(value);
    if (!country) return null;
    
    return {
      value: country.code,
      label: `${country.flag} ${country.name}`,
      country
    };
  };

  handleChange = (selected) => {
    const { id, onChange } = this.props;
    if (onChange) {
      onChange(id, selected ? selected.value : null);
    }
  };

  filterOption = (option, inputValue) => {
    if (!inputValue) return true;
    const searchLower = inputValue.toLowerCase();
    const country = option.data.country;
    return (
      country.name.toLowerCase().includes(searchLower) ||
      country.code.toLowerCase().includes(searchLower)
    );
  };

  render() {
    const { id, placeholder } = this.props;
    const options = this.getOptions();
    const value = this.getValue();

    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <div className="rowC">
            <MarkdownRenderer source={this.props.label} />
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : (
              <div />
            )}
          </div>
          <ReactSelect
            ref={(ref) => { this.selectRef = ref; }}
            id={id}
            options={options}
            placeholder={placeholder || "Select a country..."}
            value={value}
            onChange={this.handleChange}
            isSearchable={true}
            filterOption={this.filterOption}
            components={{
              Option: CountryOption,
              SingleValue: CountrySingleValue
            }}
            className={
              this.shouldDisplayError()
                ? "select-control is-invalid"
                : "select-control"
            }
            styles={{
              menu: provided => ({ ...provided, zIndex: 9999 }),
              option: (base, state) => ({
                ...base,
                display: 'flex',
                alignItems: 'center',
                padding: '8px 12px',
                cursor: 'pointer',
                backgroundColor: state.isSelected 
                  ? '#3b82f6' 
                  : state.isFocused 
                    ? '#eff6ff' 
                    : 'white',
                color: state.isSelected ? 'white' : '#333',
                '&:active': {
                  backgroundColor: '#3b82f6'
                }
              }),
              singleValue: base => ({
                ...base,
                display: 'flex',
                alignItems: 'center'
              }),
              control: (base, state) => ({
                ...base,
                minHeight: '38px',
                borderColor: state.isFocused ? '#3b82f6' : '#ced4da',
                boxShadow: state.isFocused ? '0 0 0 3px rgba(59, 130, 246, 0.1)' : 'none',
                '&:hover': {
                  borderColor: '#3b82f6'
                }
              })
            }}
          />
        </FormGroup>
        <style jsx="true">{`
          .country-option {
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .country-flag {
            font-size: 1.2em;
            line-height: 1;
          }
          .country-name {
            flex: 1;
          }
        `}</style>
      </div>
    );
  }
}

export default FormCountry;
