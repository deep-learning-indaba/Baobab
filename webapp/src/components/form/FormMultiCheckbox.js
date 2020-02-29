import React from "react";
import "./Style.css";
import FormCheckbox from "./FormCheckbox";

class FormMultiCheckbox extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  renderFormCheckbox(i) {
    return (
      <FormCheckbox
        key={i}
        // checked={this.props.value[i]}
        onChange={() => this.props.onChange(this.props.options)}
        label={this.props.options[i]}
      />
    );
  }

  render() {
    return (
      <div>
        {this.props.options.map((text, index) =>
          {this.renderFormCheckbox(index)}
        )}
      </div>
    );
  }
}
export default FormMultiCheckbox;
