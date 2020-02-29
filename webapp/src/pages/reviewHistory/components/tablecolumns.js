import React from "react";
import { Link } from "react-router-dom";

export const columns = [
  {
    Header: " ",
    accessor: "review_response_id",
    Cell: row => {
      return <Link to={"/review/" + row.row.review_response_id}>
        <i className="fa fa-edit"></i></Link>
    },
    filterable: false
  }, {
    Header: "Submitted Timestamp",
    accessor: "submitted_timestamp",
    filterable: false
  }, {
    Header: "Nationality",
    accessor: "nationality_country",
    filterable: false
  }, {
    Header: "Country of Residence",
    accessor: "residence_country",
    filterable: false
  }, {
    Header: "Affiliation",
    accessor: "affiliation",
    filterable: false
  }, {
    Header: "Department",
    accessor: "department",
    filterable: false
  }, {
    Header: "User Category",
    accessor: "user_category"
  }, {
    Header: "Final Verdict",
    accessor: "final_verdict"
  }
];
