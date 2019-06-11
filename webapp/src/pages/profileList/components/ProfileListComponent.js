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
            error: ""
        }
}

 isListEmpty(list){

    return list.length === 0;
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
    console.log(user_id)
    window.location='/viewprofile/:'+user_id;
}
 render(){
    const {List, isEmpty,loading,error} = this.state;
    const loadingStyle = {
        "width": "3rem",
        "height": "3rem"
      }
    const columns = [{Header:<div className="list-number">#</div> ,accessor:"response_id", Cell: props => <span className="number">{props.value}</span>},
                     {id: "user", Header: <div className="list-fullname">Full-Name</div>,
                      accessor:u => <div className="">{u.user_title+" "+ u.firstname+" "+u.lastname}</div>,
                      Cell: props => <span onClick={()=>this.onSubmit(props.original.user_id)}>{props.value}</span>},
                     {Header:<div className="list-user-category">Category</div>,accessor:"user_category"},
                     {Header:<div className="list-affiliation">Affiliation</div>,accessor:"affiliation"},
                     {Header:<div className="list-department">Department</div>,accessor:"department"},
                     {Header:<div className="list-nationality">Nationality</div>,accessor:"nationality_country"},
                     {Header:<div className="list-disability">Disability</div>,accessor:"user_disability"},
                     {Header:<div className="list-language">Language</div>,accessor:"user_primaryLanguage"},];
    
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
                        /> </div>)}
                </div>
        );
}

}

export default withRouter(ProfileListComponent); 