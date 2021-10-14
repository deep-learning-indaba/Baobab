import React from "react";
class FormGroup extends React.Component {
  render() {
    let formClass = "form-group";

    return (
      <div id={this.props.id} className={formClass}>
        {this.props.children}
        <div className="invalid-feedback">{this.props.errorText}</div>
      </div>
    );
  }
}

export default FormGroup;
