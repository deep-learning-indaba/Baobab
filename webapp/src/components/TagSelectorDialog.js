import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import Modal from 'react-bootstrap4-modal';

class TagSelectorDialog extends Component {
    selectTag = (tag) => {
        this.props.selectTag(tag);
    }

    render() {
        const { t, tags, visible, onCancel, onSelectTag } = this.props;

        return (
        <Modal visible={visible} onClickBackdrop={onCancel} className="tag-selector">
            <div className="modal-header">
                <h5 className="modal-title">{t('Select A Tag')}</h5>
            </div>
            <div className="modal-body">
                <div class="d-flex flex-wrap">
                    {tags.map(tag => 
                        <button key={"tag_" + tag.id} className="tag-btn btn btn-primary" onClick={() => onSelectTag(tag)}>{tag.name}</button>    
                    )}
                </div>
            </div>
            <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onCancel}>{t('Close')}</button>
            </div>
        </Modal>
        );
    }
}

export default withTranslation()(TagSelectorDialog);