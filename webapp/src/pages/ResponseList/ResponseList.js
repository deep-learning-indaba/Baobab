import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import ResponseListComponent from './components/ResponseListComponent';
import FormResponseListComponent from '../formResponseList/components/FormResponseListComponent';
import FormNotAvailable from '../../components/FormNotAvailable';

class ResponseList extends Component {
    render() {
        const { event, t } = this.props;

        if (event && event.uses_new_forms) {
            if (!event.application_form_id) {
                return <FormNotAvailable message={t('Create the application form in Form Configuration to start receiving applications.')} />;
            }
            return (
                <FormResponseListComponent
                    {...this.props}
                    formId={event.application_form_id}
                />
            );
        }

        return <ResponseListComponent event={event} />;
    }
}

export default withTranslation()(ResponseList);
