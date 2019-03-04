import React, { Component } from 'react';
import logo from '../../images/indaba-logo-dark.png';
import './Home.css';
import { getEvents } from "../../services/events";
import { NavLink } from "react-router-dom";

const headings = ["Event", "Start date", "End date", "Status"];
const fieldNames = ["description", "start_date", "end_date", "status"];

class Home extends Component {


  constructor(props) {
    super(props);

    this.state = {
      headings: headings,
      rows: []
    }
  }

  componentDidMount() {
    getEvents().then(response => {
      if (response) {
        this.setState({
          headings: headings,
          rows: response
        })
      }
    });
  }

  render() {

    let table = (<div></div>)

    if (this.state.rows && this.state.rows.length > 0) {
      const theadMarkup = (
        <tr>
          {this.state.headings.map((_cell, cellIndex) => {
            return (
              <th className="Cell">
                {this.state.headings[cellIndex]}
              </th>
            )
          })}
        </tr>
      );

      const tbodyMarkup = this.state.rows.map((_row, rowIndex) => {
        return (
          <tr>
            {fieldNames.map((_cell, cellIndex) => {
              return (
                <td className="Cell">
                  {
                    this.state.rows[rowIndex][fieldNames[cellIndex]] === "Apply now" ?
                      <NavLink to="/applicationForm">Apply now</NavLink> :
                      this.state.rows[rowIndex][fieldNames[cellIndex]]
                  }
                </td>
              )
            })}
          </tr>
        )
      });

      table = this.state.rows ? (
        <table align="center" className="Table">
          <thead>{theadMarkup}</thead>
          <tbody>{tbodyMarkup}</tbody>
        </table>
      ) : (<div></div>)
    }

    return (
      <div>
        <div >
          <img src={logo} className="Logo" alt="logo" />
        </div>
        <h2 className="Blurb">Welcome to Baobab</h2>
        {table}
      </div>
    );
  }
}

export default Home;
