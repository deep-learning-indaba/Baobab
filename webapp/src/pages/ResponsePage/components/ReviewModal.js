import React, { Component } from 'react';
import { reviewService } from '../../../services/reviews/review.service';

class ReviewModal extends Component {
    constructor(props) {
        super(props);
        this.state = {
          
        }
    };


    renderReviewers() {
        reviewService.getReviewAssignments(this.props.event.id).then(response => {
            console.log(response)
        })
    }



    renderModal() {
          // Translation
        const t = this.props.t; 
        
        if (this.props.event) {
            return (
                <div className="modal fade" id="exampleModalReview" tabIndex="-1" role="dialog" aria-labelledby="exampleModalReview" aria-hidden="true">
                    <div className="modal-dialog" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title" id="exampleModalLabel">{t('Reviewers')}</h5>
                                <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div className="modal-body">

                            </div>
                            <div className="modal-footer">
                                <button type="button"
                                    className="btn btn-secondary"
                                    data-dismiss="modal"
                                >
                                    {t('Cancel')}
                                </button>
                                <button
                                    type="button"
                                    data-dismiss="modal"
                                    className="btn btn-primary"
                                    onClick={(e) => this.renderReviewers(e)}
                                >
                                    {t('Save')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
    }


    render() {
        const modal = this.renderModal()
        return (
            <div>
                {modal}
            </div>
        )
    }
}

export default ReviewModal