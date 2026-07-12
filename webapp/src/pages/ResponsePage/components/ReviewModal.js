import React, { Component } from 'react';
import Modal from '../../../components/Modal';


class ReviewModal extends Component {
    constructor(props) {
        super(props);
        this.state = {
            selectedReviewer: null
        }
    };

    handlePost(reviewers) {
        this.props.handlePost(reviewers);
        this.setState({ selectedReviewer: null });
        this.props.onClose();
    }

    handleSelect(reviewer) {
        this.setState({ selectedReviewer: reviewer });
    };

    render() {
        const { selectedReviewer } = this.state;
        const { reviewers, t, visible, onClose } = this.props;

        if (!this.props.event) return null;

        return (
            <Modal visible={visible} onClickBackdrop={onClose}>
                <div className="modal-header-row">
                    <h5 className="modal-heading">{t('Reviewers')}</h5>
                    <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close">
                        &times;
                    </button>
                </div>

                <div className="modal-body-content">
                    {reviewers && reviewers.map(val => (
                        <button
                            onClick={() => this.handleSelect(val)}
                            className={selectedReviewer === val ? "review-select active" : "review-select"}
                            key={val.reviewer_user_id}
                        >
                            <label>{val.user_title} {val.firstname} {val.lastname}</label>
                            <div className="reviewer-email">{val.email}</div>
                            <div>
                                <p>{t('Reviews Allocated')}: {val.reviews_allocated}</p>
                                <p>{t('Reviews Completed')}: {val.reviews_completed}</p>
                            </div>
                        </button>
                    ))}
                    {!reviewers && <span>{t("There are no more reviewers available")}</span>}
                </div>

                <div className="modal-footer-row">
                    <button type="button" className="btn btn-secondary" onClick={onClose}>
                        {t('Cancel')}
                    </button>
                    <button
                        type="button"
                        className="btn btn-primary"
                        onClick={() => this.handlePost(selectedReviewer)}
                    >
                        {t('Assign')}
                    </button>
                </div>
            </Modal>
        );
    };
};

export default ReviewModal;
