import React from "react";
import "./Style.css";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import MarkdownRenderer from "../MarkdownRenderer";

class FormMultiCheckbox extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      options: [],
      checked: []
    };
  }

  componentDidMount() {
    let checkedValues = [];
    if (this.props.defaultValue) {
      checkedValues = this.props.defaultValue.split(' ; ');
    }
    this.setState({
      checked: checkedValues
    });
  }

  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
    // Re-sync when the value arrives after mount (a saved response is loaded
    // asynchronously, so componentDidMount often runs before there is a value).
    if (nextProps.defaultValue !== this.props.defaultValue) {
      this.setState({
        checked: nextProps.defaultValue ? nextProps.defaultValue.split(' ; ') : []
      });
    }
  }

  onCheckChanged = (option, checked) => {
    this.setState(prevState => {
      var newChecked = prevState.checked.filter(c => c !== option.value);
      if (checked) {
        newChecked.push(option.value);
      }
      newChecked = newChecked.sort();
      return {
        checked: newChecked
      };
    }, () => {
      if (this.props.onChange) {
        this.props.onChange(this.state.checked.join(' ; '));
      }
    });
  }

  renderFormCheckbox = (option) => {
    let id = "checkbox_" + this.props.id + "_" + option.value;
    // Plain flex row with an explicit gap between the checkbox and its label.
    // Avoid Bootstrap's `custom-control`/`custom-control-input`/`custom-control-label`
    // classes here - they aren't defined in this app's stylesheet.
    return (
      <div className="flex items-start gap-2 py-1" key={option.value}>
        <input
          id={id}
          className={`mt-0.5 w-4 h-4 shrink-0 cursor-pointer accent-primary${
            this.shouldDisplayError() ? " outline outline-1 outline-error" : ""
          }`}
          type="checkbox"
          checked={this.state.checked.includes(option.value)}
          disabled={this.props.disabled}
          onChange={e => {
            this.onCheckChanged(option, e.target.checked);
          }}
          ref={input => {
            this.nameInput = input;
          }}
          key={this.props.id + '_check_' + option.value}
        />
        <label className="cursor-pointer text-sm leading-snug m-0" htmlFor={id}>{option.label}</label>
      </div>
    );
  }

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
          tabIndex={this.props.tabIndex}
          autoFocus={this.props.autoFocus}
        >
          <div className="rowC">
            <MarkdownRenderer source={this.props.label}/>
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : (
                <div />
              )}
          </div>
          <div className="form text-left multi-checkbox-list">
            {this.props.options.map((option) => this.renderFormCheckbox(option))}
          </div>
        </FormGroup>
      </div>
    );
  }
}
export default FormMultiCheckbox;
