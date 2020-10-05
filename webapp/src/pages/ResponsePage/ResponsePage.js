
import React, { Component } from 'react'
import ReactTable from 'react-table';
import { NavLink } from 'react-router-dom';
import "react-table/react-table.css";
import { withTranslation } from 'react-i18next';
import './ResponsePage.css'
import { applicationFormService } from '../../services/applicationForm/applicationForm.service'
import { fetchResponse } from '../../services/ResponsePage/ResponsePage'

class ResponsePage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            applicationForm: null,
        }
    };

    componentDidMount() {
        this.fetchForm()
        this.fetchData()
    }

    // Fetch Form
    fetchForm() {
        applicationFormService.getForEvent(this.props.event.id).then(response => {
            this.setState({
                applicationForm: response.formSpec
            }, console.log(response.formSpec))
        })
    }

    // Fetch Data
    fetchData() {
        let params = {
            id: this.props.match.params.id,
            eventKey: this.props.match.params.eventKey,
        }

        fetchResponse(params).then(response => {
            this.setState({
                applicationData: response
            })
        })
    }

    generateCols() {
        let colFormat = [];
        // Find the row with greatest col count and assign the col values to React Table
        let newColumns = Object.keys(this.state.applicationForm)


        function widthCalc(colItem) {
            if (colItem.includes('question')) {
                return 200
            }

            if (colItem.includes('user') || colItem.includes('Review') || colItem.includes('date')) {
                return 180
            }
            else {
                return 100
            }
        }

        let col = newColumns;
        console.log(col)
        colFormat = col.map(val => ({ id: val, Header: val, accessor: val, className: "myCol", width: widthCalc(val) }))
        console.log(colFormat)
        return colFormat
    }

    goBack(){
        this.props.history.goBack();
    }


    render() {


        const { applicationForm } = this.state

        let columns = applicationForm ? this.generateCols() : console.log("no form data");

        return (
            <div className="table-wrapper">

                <h2>Response Page</h2>
                <div className="heading-back-btn">
                    <h4>{this.props.match.params.eventKey}</h4>
                 <button class="btn btn-primary" onClick={((e) => this.goBack(e))}>Back</button>
                </div>
               
                {/* Response Table */}
                {applicationForm &&
                    <ReactTable
                        className="ReactTable"
                        //  data={responseTable ? responseTable : []}
                        columns={columns}
                        minRows={0}
                    />
                }
            </div>
        )
    }
}

export default withTranslation()(ResponsePage);


