import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { NavLink } from "react-router-dom";
import {
    Button,
    TextField,
    DialogTitle,
    Dialog,
    Typography
} from '@material-ui/core';



class EventKeyModal extends Component {
    constructor(props) {
        super(props);
        this.state = {
            createdEventKey: null,
            open: false
        }
    };


    // Handle Dialogue Close
    closeDialogue() {
        this.setState({
            open: false
        })
    }

    // Open Dialogue
    openDialogue() {
        this.setState({
            open: true
        })
    }


    // Set Event Key
    createEventKey(e) {

        console.log(e.target.value)
        this.setState({
            createdEventKey: e.target.value
        })
    }


    render() {
        const t = this.props.t;

        const {
            open,
            createdEventKey
        } = this.state;

        // Dialogue Style
        const style = {
            padding: "50px"
        }

        return (
            <div>

                {/* Create Event Pop Up */}
                <Dialog onClose={(e) => this.closeDialogue()} aria-labelledby="simple-dialog-title" open={open}>
                    <DialogTitle className="event-pop-up" id="simple-dialog-title">Set backup account</DialogTitle>
                    <TextField onChange={(e) => this.createEventKey(e)} id="standard-basic" label="Create Event Key" />

                    {createdEventKey &&
                        <div className="event-key-link">
                            <NavLink
                                data-dismiss="modal"
                                to={`${createdEventKey}/eventConfig`}>{t('Create')}</NavLink>
                        </div>
                    }

                </Dialog>


                {/* Create Event Button */}
                <div className="card add-event" onClick={(e) => this.openDialogue()}>
                    <p>Add Event</p>
                </div>

            </div>
        )
    }


}

export default withTranslation()(EventKeyModal)