import React, { Component } from "react";

class Loading extends Component {

    render() {
        const loadingStyle = {
            width: "3rem",
            height: "3rem"
          };

        return (
            <div className="d-flex justify-content-center">
                <div className="spinner-border"
                    style={loadingStyle}
                    role="status">
                    <span className="sr-only">Loading...</span>
                </div>
            </div>
        );
    }

}

export default Loading;
