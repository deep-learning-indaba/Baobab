import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import MarkdownRenderer from "../MarkdownRenderer";

class FormDate extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  UNSAFE_componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus && this.dateInput) {
      this.dateInput.focus();
    }
  }

  onChange = e => {
    if (this.props.onChange) {
      this.props.onChange(e.target.value);
    }
  }

  render() {
    const hasError = this.props.id && this.props.errorText && this.props.errorText.length > 0;
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

          <input
            type="date"
            id={this.props.id}
            ref={input => { this.dateInput = input; }}
            className={`form-control${hasError ? ' is-invalid' : ''}`}
            onChange={this.onChange}
            value={this.props.value || ''}
            disabled={this.props.disabled}
          />

        </FormGroup>
      </div>
    );
  }
}
export default FormDate;
