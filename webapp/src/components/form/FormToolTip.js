import React, { Component } from "react";
import ReactToolTip from "react-tooltip";
class FormToolTip extends React.Component {
  render() {
    const hasDescription = this.props.description;
    let tooltip;

    if (hasDescription) {
      tooltip = (
        <div>
          <i class="fas fa-question-circle" data-tip={this.props.description} />
          <ReactToolTip />
        </div>
      );
    } else {
      tooltip = <div />;
    }
    return tooltip;
  }
}

export default FormToolTip;
