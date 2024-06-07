export const isEventAdmin = (user, event) => {
    if (!user) {
      return false;
    }
    return (
      user.is_admin ||
      (user.roles &&
        user.roles.some(
          r => r.role === "admin" && event && r.event_id === event.id
        ))
    );
  };

  export const isEventResponseViewerOnly = (user, event) => {
    if (!user) {
      return false;
    }
    return (
      //user.is_admin &&
      (user.roles &&
        user.roles.some(
          r => r.role === "response_viewer" && event && r.event_id === event.id
        ))
    );
  };

  export const isEventResponseEditorOnly = (user, event) => {
    if (!user) {
      return false;
    }
    return (
      //user.is_admin &&
      (user.roles &&
        user.roles.some(
          r => r.role === "response_editor" && event && r.event_id === event.id
        ))
    );
  };

  export const isRegistrationAdmin = (user, event) => {
    if (!user) {
      return false;
    }
    return (
      user.is_admin ||
      (user.roles &&
        user.roles.some(
          r =>
            (r.role === "admin" || r.role === "registration-admin") &&
            event &&
            r.event_id === event.id
        ))
    );
  };

  export const isRegistrationVolunteer = (user, event) => {
    if (!user) {
      return false;
    }
    return (
      user.is_admin ||
      (user.roles &&
        user.roles.some(
          r =>
            (r.role === "admin" ||
              r.role === "registration-admin" ||
              r.role === "registration-volunteer") &&
            event &&
            r.event_id === event.id
        ))
    );
  };

  export const isEventReviewer = (user, event) => {
    if (!user) {
      return false;
    }
    return (
      user.roles &&
      user.roles.some(
        r => r.role === "reviewer" && event && r.event_id === event.id
      )
    );
  };