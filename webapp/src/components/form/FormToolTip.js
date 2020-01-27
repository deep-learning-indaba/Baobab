import React from "react";
import ReactToolTip from "react-tooltip";
class FormToolTip extends React.Component {
  render() {
    const hasDescription = this.props.description;
    let tooltip;

    if (hasDescription) {
      tooltip = (
        <div>
          <i class="fas fa-question-circle fa-lg" data-tip={this.props.description} />
          <ReactToolTip type="info" place="right" effect="solid" />
        </div>
      );
    } else {
      tooltip = <div />;
    }
    return tooltip;
  }
}

export default FormToolTip;
