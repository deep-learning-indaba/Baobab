import React, { Component } from "react";
import "./ViewProfile.css";
import ViewProfileComponent from "./components/ViewProfileComponent";

export default class ViewProfile extends Component {
    constructor(props){
        super(props);
    }

    render() {
        return (
            <ViewProfileComponent></ViewProfileComponent>
        );
    }
}