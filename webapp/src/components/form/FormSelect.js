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

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  render() {
    const { id, options, placeholder, onChange, defaultValue, searchable } = this.props;
    let value = this.props.value;
    if (defaultValue) {
      value = options.filter(option => option.value === defaultValue);
    }
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
            defaultValue={value || null}
            isSearchable={searchable}
            className={
              this.shouldDisplayError()
                ? "select-control is-invalid"
                : "select-control"
            }
            styles={{
              // Fixes the overlapping problem of the component
              menu: provided => ({ ...provided, zIndex: 9999 })
            }}
          />
        </FormGroup>
      </div>
    );
  }
}
export default FormSelect;
