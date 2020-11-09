import React, { Component } from 'react'

// TODO: Need to add validation - can't add a duplicate tag name and can't leave a language blank

class Form extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tagTranslations: {}
        }
    };


    handleSubmit() {
        const { tagTranslations } = this.state;
        this.props.postTag(tagTranslations);
        // clear inout fields
        Array.from(document.querySelectorAll("input")).forEach(
            input => (input.value = "")
          );
  
        this.setState({
            tagTranslations: {}
        });
    }


    handleChange(event, label) {
        const { tagTranslations } = this.state;
    
        if (event.target.value) {
            tagTranslations[label] = event.target.value;
        }
        else {
           delete tagTranslations[label];
        };
      
        this.setState({
            tagTranslations: tagTranslations
        });
    }


    renderTagModal() {
          // Translation
        const t = this.props.t; 
        
        if (this.props.eventLanguages) {
            let inputs = this.props.eventLanguages.map(val => {
                return <div id="myInputs" key={val} className="new-tag-inputs">
                    <label>{val}</label>
                    <input key={val} onChange={(e) => this.handleChange(e, val)}></input>
                </div>
            });
            
            return (
                <div className="modal fade" id="newTagModal" tabIndex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
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
                                    onClick={(e) => this.handleSubmit()}
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
        const modal = this.renderTagModal()
        return (
            <div>
                {modal}
            </div>
        )
    }
}

export default Form