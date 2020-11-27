import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { NavLink } from "react-router-dom";


class EventKeyModal extends Component {
    constructor(props) {
        super(props);
        this.state = {
            createEventKey: null
        }
    };


    // Set Event Key
    createEventKey(e) {
        this.setState({
            createEventKey: e.target.value
        })
    }


    render() {
        const t = this.props.t;

        return (
            <div className="modal fade" id="eventKeyModal" tabIndex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div className="modal-dialog" role="document">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h5 className="modal-title" id="exampleModalLabel">{t('Create Event Key')}</h5>
                            <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div className="modal-body">
                            <form>
                                <input
                                    placeHolder="enter event key"
                                    onChange={(e) => this.createEventKey(e)}
                                >

                                </input>

                            </form>
                        </div>
                        <div className="modal-footer">
                            <button type="button"
                                className="btn btn-secondary"
                                data-dismiss="modal"
                            >
                                {t('Cancel')}
                            </button>
                            {this.state.createEventKey &&
                                <NavLink
                                    className="event-key-link"
                                    data-dismiss="modal"
                                    to={`/${this.state.createEventKey}/eventConfig`}>{t('Create')}</NavLink>
                            }

                        </div>
                    </div>
                </div>
            </div>
        )
    }


}

export default withTranslation()(EventKeyModal)