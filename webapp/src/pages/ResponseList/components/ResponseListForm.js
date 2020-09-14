import React, { Component } from 'react';
import '../ResponseList.css';
import { withTranslation } from 'react-i18next';


class ResponseListForm extends Component {

    constructor(props) {
        super(props);
        this.state = {

        }
    }



    render() {
        const t = this.props.t;

        return (
            <div className="container">

                {/**/}
                {/**/}
                {/**/}
                {/**/}
                {/**/}

                {/*CheckBox*/}
                <input class="form-check-input" type="radio" name="exampleRadios" id="exampleRadios1" value="option1" />
                <label class="form-check-label" for="exampleRadios1">
                    Include un-submitted
              </label>

                {/*DropDown*/}
                <div class="dropdown">
                    <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        Dropdown button
                    </button>
                    <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                        <a class="dropdown-item" href="#">Action</a>
                        <a class="dropdown-item" href="#">Another action</a>
                        <a class="dropdown-item" href="#">Something else here</a>
                    </div>
                </div>

            </div>
        )
    }
}

export default withTranslation()(ResponseListForm);
