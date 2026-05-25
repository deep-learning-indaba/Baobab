import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import Modal from './Modal';

class TagSelectorDialog extends Component {
    selectTag = (tag) => {
        this.props.selectTag(tag);
    }

    render() {
        const { t, tags, visible, onCancel, onSelectTag } = this.props;

        return (
            <Modal visible={visible} onClickBackdrop={onCancel}>
                <div className="border-b border-border/50 pb-3">
                    <h5 className="text-lg font-bold text-foreground">{t('Select A Tag')}</h5>
                </div>
                <div className="py-4">
                    <div className="flex flex-wrap gap-2">
                        {tags.map(tag => 
                            <button 
                                key={"tag_" + tag.id} 
                                className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm cursor-pointer" 
                                onClick={() => onSelectTag(tag)}
                            >
                                {tag.name}
                            </button>    
                        )}
                    </div>
                </div>
                <div className="flex justify-end border-t border-border/50 pt-3">
                    <button 
                        type="button" 
                        className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 cursor-pointer" 
                        onClick={onCancel}
                    >
                        {t('Close')}
                    </button>
                </div>
            </Modal>
        );
    }
}

export default withTranslation()(TagSelectorDialog);