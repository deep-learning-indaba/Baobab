import React from "react";
import DateTimePicker from 'react-datetime-picker'
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import * as moment from 'moment';
import ReactMarkdown from "react-markdown";

class FormDate extends React.Component {
  constructor(props) {
    super(props);
  }

  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";

  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.dateInput.focus();
    }



  }

  onChange = value => {
    if (value && this.props.onChange) {
      this.props.onChange(moment(value).format("YYYY-MM-DD"));
    }
  }

  linkRenderer = (props) => <a href={props.href} target="_blank">{props.children}</a>

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <div className="rowC">
            <ReactMarkdown source={this.props.label} renderers={{link: this.linkRenderer}}/>
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : (
                <div />
              )}

          </div>

          <DateTimePicker
            id={this.props.id}
            ref={input => {
              this.dateInput = input;
            }}
            className={this.props.id && this.props.errorText && this.props.errorText.length > 0  ? "react-datetime-picker error" : "react-datetime-picker"}
            onChange={this.onChange}
            value={this.props.value ? new Date(this.props.value) : null}
            format="y-MM-dd"
          />

        </FormGroup>
      </div>
    );
  }
}
export default FormDate;
