import React from "react";
import DateTimePicker from 'react-datetime-picker'
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import * as moment from 'moment';

class FormDate extends React.Component {
  constructor(props) {
    super(props);
  //   this.state = {
  //     value: new Date()
  //   }
  }

  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  // componentDidMount() {
  //   // this.setState({
  //   //   value: this.props.value ? new Date(this.props.value) : new Date()
  //   // });
  // }

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.dateInput.focus();
    }
  }

  // componentDidUpdate(prevProps) {
  //   console.log('Component did update: ');
  //   console.log(this.props);
  //   if (prevProps.value !== this.props.value) {
  //     this.setState({
  //       value: this.props.value ? new Date(this.props.value) : new Date()
  //     });
  //   }
  // }

  onChange = value => {
    if (value && this.props.onChange) {
      this.props.onChange(moment(value).format("YYYY-MM-DD"));
    }
    //this.setState({value});
  }

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <div className="rowC">
            <label htmlFor={this.props.id}>{this.props.label}</label>
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
          onChange={this.onChange}
          value={this.props.value ? new Date(this.props.value) : new Date()}
          format="y-MM-dd"
        />
        </FormGroup>
      </div>
    );
  }
}
export default FormDate;
