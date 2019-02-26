import React, { Component } from 'react';
import logo from '../../images/indaba-logo-dark.png';
import './Home.css';
import { getEvents } from "../../services/events";

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
      this.setState({
        headings: headings,
        rows: response
      })
    });
  }

  render() {
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
                {this.state.rows[rowIndex][fieldNames[cellIndex]]}
              </td>
            )
          })}
        </tr>
      )
    });

    return (
      <div>
        <div >
          <img src={logo} className="Logo" alt="logo" />
        </div>
        <h2 className="Blurb">Welcome to Boabab</h2>
        <table align="center" className="Table">
          <thead>{theadMarkup}</thead>
          <tbody>{tbodyMarkup}</tbody>
        </table>
      </div>
    );
  }
}

export default Home;
