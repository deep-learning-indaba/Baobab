import React from "react";
import FormGroup from "./FormGroup";
import { default as ReactSelect } from "react-select";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import MarkdownRenderer from "../MarkdownRenderer";

class FormSelect extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  UNSAFE_componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  // Callers pass the current selection in one of three shapes:
  //  - a raw scalar matching option.value (most callers, via value or defaultValue)
  //  - a {value, label} option object
  //  - a [{value, label}] array, from callers using getContentValue()'s .filter()
  // react-select needs a single {value, label} object (or null), so normalise here.
  resolveOption(rawValue, options) {
    if (rawValue === undefined || rawValue === null || rawValue === "") {
      return null;
    }
    if (Array.isArray(rawValue)) {
      return rawValue.length > 0 ? rawValue[0] : null;
    }
    if (typeof rawValue === "object") {
      return rawValue;
    }
    return (options && options.find(option => option.value === rawValue)) || null;
  }

  render() {
    const { id, options, placeholder, onChange, searchable } = this.props;
    const rawValue = this.props.value ?? this.props.defaultValue;
    const value = this.resolveOption(rawValue, options);
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <div className="rowC">
            <MarkdownRenderer source={this.props.label}/>
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : (
              <div />
            )}
          </div>
          <ReactSelect
            id={id}
            options={options}
            placeholder={placeholder}
            value={value}
            onChange={e => onChange(id, e)}
            isSearchable={searchable}
            className={
              this.shouldDisplayError()
                ? "select-control is-invalid"
                : "select-control"
            }
            styles={{
              menu: provided => ({ ...provided, zIndex: 9999 }),
              control: (provided, state) => ({
                ...provided,
                borderRadius: '1rem',
                borderColor: state.isFocused ? 'var(--clr-action)' : 'var(--clr-outline-variant)',
                boxShadow: state.isFocused ? '0 0 0 3px var(--clr-action-glow)' : 'none',
                fontFamily: 'var(--font-body)',
                fontSize: '0.9375rem',
                padding: '0.0625rem 0.125rem',
                '&:hover': { borderColor: state.isFocused ? 'var(--clr-action)' : 'var(--clr-outline-variant)' }
              }),
              menuList: provided => ({ ...provided, borderRadius: '0.75rem' }),
            }}
          />
        </FormGroup>
      </div>
    );
  }
}
export default FormSelect;
