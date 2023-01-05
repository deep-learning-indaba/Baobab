import React, { Component } from "react";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';

class Onboarding extends Component {
    constructor(props) {
    }

}


export default withRouter(withTranslation()(Onboarding));