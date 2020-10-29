import React, { Component } from 'react'

class Form extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tags: {}
        }
    };


    handleSubmit() {
        const { tags } = this.state;
        this.props.postTag(tags);

        this.setState({
            tags: {}
        })
    }


    handleChange(event, label) {
        const { tags } = this.state;
        let addTags = tags;
    
        if (event.target.value) {
            addTags[label] = { headline: event.target.value, id: label }
        }
        else {
           delete addTags[label]
        };
      
        this.setState({
            tags: addTags
        })
    }


    renderTagModal() {
          // Translation
        const t = this.props.t; 
        
        if (this.props.eventLanguages) {
            let inputs = this.props.eventLanguages.map(val => {
                return <div key={val} className="new-tag-inputs">
                    <label>{val}</label>
                    <input key={val} onChange={(e) => this.handleChange(e, val)}></input>
                </div>
            });

            return (
                <div className="modal fade" id="exampleModal" tabIndex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div className="modal-dialog" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title" id="exampleModalLabel">{t('Add Tags')}</h5>
                                <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div className="modal-body">
                                <form>
                                    {inputs}
                                </form>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" data-dismiss="modal">{t('Cancel')}</button>
                                <button type="button" data-dismiss="modal" className="btn btn-primary" onClick={(e) => this.handleSubmit()}>{t('Save')}</button>
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