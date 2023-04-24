import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import ResponseListComponent from './components/ResponseListComponent'


class ResponseList extends Component {

    render() {
        return <ResponseListComponent event={this.props.event} />
    }
}

export default withTranslation()(ResponseList);
