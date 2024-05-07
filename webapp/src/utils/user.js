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

  export const isEventReadOnly = (user, event) => {
    if (!user) {
      return false;
    }
    return (
      user.is_read_only ||
      (user.roles &&
        user.roles.some(
          r => r.role === "read_only" && event && r.event_id === event.id
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