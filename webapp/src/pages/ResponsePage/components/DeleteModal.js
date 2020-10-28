import React, { Component } from 'react'

class DeleteModal extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tags: {}
        }
    };


    handleSubmit() {
        this.props.handleSubmit(this.props.deleteQue)
    }

    render() {
       return (
        <div class="modal fade" id="exampleModal2" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="exampleModalLabel">Delete Tags</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                  Are you sure you want to delete this tag?
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                    <button type="button" data-dismiss="modal" class="btn btn-primary" onClick={(e) => this.handleSubmit()}>Yes</button>
                </div>
            </div>
        </div>
    </div>
        )
    }
}

export default DeleteModal