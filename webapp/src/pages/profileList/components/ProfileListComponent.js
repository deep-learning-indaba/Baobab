import React, { Component } from "react";
import { withRouter} from "react-router";
 import ReactTable from 'react-table';
import { profileService} from "../../../services/profilelist";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

class ProfileListComponent extends Component{
    constructor(props){
        super(props);
        this.state = {
            List:[],
            isEmpty:true,
            loading:true,
            error: "",
            Desc_Asc:true
        }
}

 isListEmpty(list){
    return list.length === 0;
 }

 onChangeSorting = ()=>{
    this.setState({Desc_Asc:!this.state.Desc_Asc});
 }
 componentDidMount(){ 
    profileService.getProfilesList(DEFAULT_EVENT_ID)
                    .then(results => {
                        this.setState(
                            {
                                List: results.List,
                                isEmpty: this.isListEmpty(results.List),
                                loading: false,
                                error: results.error
                            });
                    });                
 }
onSubmit=(user_id)=>{
    window.location='/viewprofile/:'+user_id;
}
 render(){
    const {List, isEmpty,loading,error,Desc_Asc} = this.state;
    const loadingStyle = {
        "width": "3rem",
        "height": "3rem"
      }
    const columns = [
                     {id: "user", Header: <div className="list-fullname">Full-Name</div>,
                      accessor:u=>u.lastname+" "+u.firstname+", "+u.user_title,
                      Cell: props => <a href="#" onClick={e=>{e.preventDefault(); this.onSubmit(props.original.user_id)}}>{props.value}</a>,
                      minWidth: 150},
                     {Header:<div className="list-user-category">Category</div>,accessor:"user_category"},
                     {Header:<div className="list-affiliation">Affiliation</div>,accessor:"affiliation"},
                     {Header:<div className="list-department">Department</div>,accessor:"department"},
                     {Header:<div className="list-nationality">Nationality</div>,accessor:"nationality_country"}];
    
    if(loading){
        return (
            <div class="d-flex justify-content-center">
                <div class="spinner-border" style={loadingStyle} role="status">
                    <span class="sr-only">Loading...</span>
                </div>
        </div>
        );
    }

    if (error){
        return <div class="alert alert-danger">{error}</div>
      }
        return (
               <div> 
                {isEmpty ? (
                    <div className="error-message-empty-list">
                        <div className="alert alert-danger">
                            There are currently no user profiles to display!
                        </div>
                     </div>
                ):(
                    <div className="review-padding"> <span className="review-padding">
                     <div className="alert alert-primary table-header">
                        Total Profiles: {List.length}       
                     </div>
                    </span>
                        <ReactTable 
                            data={List}
                            columns={columns}
                            minRows={0}
                            multiSort={true}
                        /> </div>)}
                </div>
        );
}

}

export default withRouter(ProfileListComponent); 