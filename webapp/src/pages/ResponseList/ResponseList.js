import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import ResponseListForm from './components/ResponseListForm'


class ResponseList extends Component {

    render() {
        return <ResponseListForm event={this.props.event} />
    }
}

export default withTranslation()(ResponseList);
