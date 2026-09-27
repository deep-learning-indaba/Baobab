import i18n from 'i18next';
import { userService } from '../services/user';

// Switches the site's interface language, saves it as the signed-in user's
// preferred language (the request interceptor sends i18n.language with the
// profile update), then reloads so every loaded translation is refreshed.
export function changeSiteLanguage(lang) {
  return i18n.changeLanguage(lang).then(() => {
    const currentUser = JSON.parse(localStorage.getItem("user"));
    if (currentUser) {
      userService.get().then(result => {
        userService.update({
          email: result.email,
          firstName: result.firstname,
          lastName: result.lastname,
          title: result.user_title
        });
      });
    }
    window.location.reload(true);
  });
}
