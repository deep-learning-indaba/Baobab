import React from "react";
import { Link } from "react-router-dom";

export const columns = [
  {
    Header: " ",
    accessor: "review_response_id",
    Cell: row => {
      return <Link to={"review/" + row.row.review_response_id}>
        <i className="fa fa-edit"></i></Link>
    },
    filterable: false
  }, 
  {
    Header: "Submitted Timestamp",
    accessor: "submitted_timestamp",
    filterable: false
  }
];
