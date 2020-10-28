import React, { Component } from 'react'

class Form extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tags: {}
        }
    };

    handleSubmit(event) {
        console.log(event.target.value)
    }


    handleChange(event, label) {
        const { tags } = this.state;
        let addTags = tags;

        if (!addTags.length) {
            addTags[label] = {value: event.target.value, label: label}
        }
        else {
            addTags.forEach(val => {
                if (val.label !== label) {
                    addTags[label] = {value: event.target.value, label: label}
                }
                if (val.label == label) {
                    addTags[label].value = event.target.value
                }
            })
        }

      

        this.setState({
            tags: addTags
        })

    }


    renderTagModal() {
        if (this.props.eventDetails) {
            let inputs = this.props.eventDetails.event.map(val => {
                return <div className="new-tag-inputs">
                    <label>{val}</label>
                    <input onChange={(e) => this.handleChange(e, val)}></input>
                </div>
            });

            return (
                <div class="modal fade" id="exampleModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div class="modal-dialog" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="exampleModalLabel">Add Tags</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                <form>
                                    {inputs}
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                                <input onClick={(e) => this.handleSubmit(e)} type="submit" value="Submit" />
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
    }

    render() {
        const modal = this.renderTagModal()

        return (
            <div>
                {modal}
            </div>
        )
    }
}

export default Form