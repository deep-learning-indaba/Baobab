import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import ResponseListForm from './components/ResponseListForm'


class ResponseList extends Component {

    constructor(props) {
        super(props);
        this.state = {

        }
    }

   

    render() {
        const t = this.props.t;

        return (
            <ResponseListForm />
            )
    }
}

export default withTranslation()(ResponseList);
