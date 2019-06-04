import React, { Component } from "react";
import "./ProfileList.css";
import ProfileListComponent from "./components/ProfileListComponent.js";

export default class ProfileList extends Component {
    constructor(props){
        super(props);
    }

    render(){
     return (
        <ProfileListComponent></ProfileListComponent>
     );
    }

}