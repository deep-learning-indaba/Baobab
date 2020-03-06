import React, { Component } from "react";

export default class Loading extends Component {

    render() {
        const loadingStyle = {
            width: "3rem",
            height: "3rem"
          };

        return (
            <div class="d-flex justify-content-center">
                <div class="spinner-border"
                    style={loadingStyle}
                    role="status">
                    <span class="sr-only">Loading...</span>
                </div>
            </div>
        );
    }

}