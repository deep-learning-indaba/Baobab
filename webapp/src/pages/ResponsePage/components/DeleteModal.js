import React, { Component } from 'react'

class DeleteModal extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tags: {}
        }
    };


    handleSubmit() {
        this.props.handleSubmit(this.props.deleteQue);
    }


    render() {
          // Translation
        const t = this.props.t;
        
       return (
        <div className="modal fade" id="exampleModal2" tabIndex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div className="modal-dialog" role="document">
            <div className="modal-content">
                <div className="modal-header">
                    <h5 className="modal-title" id="exampleModalLabel">{t('Delete Tags')}</h5>
                    <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div className="modal-body">
                 { t('Are you sure you want to delete this tag?')}
                </div>
                <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" data-dismiss="modal">{t('Cancel')}</button>
                    <button type="button" data-dismiss="modal" className="btn btn-primary" onClick={(e) => this.handleSubmit()}>{t('Yes')}</button>
                </div>
            </div>
        </div>
    </div>
        )
    }
}

export default DeleteModal