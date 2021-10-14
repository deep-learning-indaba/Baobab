import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import ReactMarkdown from "react-markdown";

class FormCheckbox extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  linkRenderer = (props) => (
    <a href={props.href} target="_blank">
      {props.children}
    </a>
  );

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <div className="rowC">
            <ReactMarkdown
              source={this.props.label}
              renderers={{ link: this.linkRenderer }}
            />
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : (
              <div />
            )}
          </div>
          <input
            id={this.props.id}
            className={
              this.shouldDisplayError()
                ? "form-control is-invalid"
                : "form-control"
            }
            type="checkbox"
            placeholder={this.props.placeholder}
            checked={this.props.value}
            onChange={this.props.onChange}
            min={this.props.min || null}
            ref={(input) => {
              this.nameInput = input;
            }}
            tabIndex={this.props.tabIndex}
            autoFocus={this.props.autoFocus}
            required={this.props.required || null}
          />
        </FormGroup>
      </div>
    );
  }
}
export default FormCheckbox;
