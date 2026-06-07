import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import ResponseListComponent from './components/ResponseListComponent';
import FormResponseListComponent from '../formResponseList/components/FormResponseListComponent';

class ResponseList extends Component {
    render() {
        const { event } = this.props;
        const applicationFormId = event && event.application_form_id;

        if (applicationFormId) {
            return (
                <FormResponseListComponent
                    {...this.props}
                    formId={applicationFormId}
                />
            );
        }

        return <ResponseListComponent event={event} />;
    }
}

export default withTranslation()(ResponseList);
