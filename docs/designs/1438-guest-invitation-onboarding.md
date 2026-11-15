# Invited guest onboarding — Design Doc

2026-11-15 · Drafted by Claude for #1438

## 1. Summary

Every invited guest gets one link in their invitation email. It opens a public invitation page where they accept or decline. A guest without an account sets their name and password on that page, is logged in, and goes straight on to the registration form. The link stays valid until the event ends. Event admins can see on the Invited Guests page whether each guest is Pending, Accepted or Declined, and can reset a declined invitation, which sends it again.

**Goals**

- One link, one page, from the invitation email to the registration form, for guests with and without an account.
- The link stays valid until the event's end date, so it doesn't run out the way the 24-hour password reset code does.
- Guests can accept or decline, can decline later after accepting, and can add an optional note when declining.
- Admins see each guest's response and note, can filter by it, and can reset a declined invitation, which resends it.
- A declined guest is no longer treated as attending: they can't register and aren't counted as a guest or attendee.

**Non-goals**

- Changing how admins add guests (the add/create form on the Invited Guests page stays as it is, apart from the new column).
- Bulk invite or bulk resend. That would be a separate feature.
- Emailing admins when a guest responds. The list shows the status, and adding an email type later is easy (see Decisions).
- Reworking the guest registration form itself. After accepting, guests use the registration form that exists today (new forms or legacy).
- The unused `webapp/src/pages/onboarding/` page, which no route references. It is left alone.

## 2. Current state

### Invitation flow today

| Step | Existing account | New account |
| --- | --- | --- |
| Admin action | `POST /api/v1/invitedGuest` (`InvitedGuestAPI.post`) | `POST /api/v1/invitedGuest/create` (`CreateUser.post`) creates `AppUser` with a random password and `verified_email=True`, then calls `InvitedGuestAPI.post(send_email=False)` |
| Email | `guest-invitation`: button to `/<event>/registration` | `new-guest` (sensitive): numbered steps: set a password (`/resetPassword?resetToken=<PasswordReset.code>`), log in, open the registration link, update the profile |
| Link lifetime | n/a (login needed) | `PasswordReset.date` = now + **1 day** (`api/app/users/models.py:expiration_date`) |
| Guest response | None. Being on the list counts as attending | None |

### Layers

| Layer | Where | Relevant detail |
| --- | --- | --- |
| Model | `api/app/invitedGuest/models.py` `InvitedGuest` | `id, event_id, user_id, role`, tags via `InvitedGuestTag`. No status, token or timestamps |
| Model | `api/app/users/models.py` `PasswordReset` | `code` uuid, `date` = expiry, 1 day |
| API | `api/app/invitedGuest/api.py` | `InvitedGuestAPI` (get/post/delete), `CreateUser`, `InvitedGuestList` (`/api/v1/invitedGuestList`), `CheckIfInvitedGuest`. **`post` and `CreateUser.post` only check `@auth_required`, with no event-admin check** |
| Repository | `api/app/invitedGuest/repository.py` | `get_for_event_and_user`, `add_invited_guest`, `delete_invited_guest`, tag helpers |
| Event status | `api/app/events/status.py` `get_event_status` | Any `InvitedGuest` row → `EventStatus(invited_guest=role, registration_status=...)`. Served in `api/app/events/api.py:66` as `status.invited_guest` |
| Emails | `api/app/email_template/registry.py`, `views.py` `GuestView` (`role`, `registration_url`), `AccountSetupView` (`set_password_url`, `profile_url`), defaults `api/app/email_template/defaults/{guest-invitation,new-guest}.{en,fr}.md` | `queue_email('guest-invitation', user, event=event, context={'guest': role})` |
| Precedent | `/reference/:token` (`webapp/src/pages/references`) | Existing public, token-addressed page with no login |
| Frontend list | `webapp/src/pages/invitedGuests/components/InvitedGuestComponent.js` | react-table columns: Full Name, Email, Role, Tags, Remove. Filters by name/role/tag. CSV download |
| Frontend status | `webapp/src/components/EventStatus.js` `invitedGuestStatus` | "You have been invited as a X, please proceed to registration" → `/<event>/registration` |
| Service | `webapp/src/services/invitedGuests/invitedGuests.service.js` | `getInvitedGuestList`, `addInvitedGuest`, `createInvitedGuest`, `deleteGuest`, … |
| Auth storage | `webapp/src/services/user/user.service.js` `login` | Stores `user_info` (including `token`) in `localStorage["user"]` |
| Seed | `api/app/utils/seed_agent.py:202` | `claude-guest@baobab.test` is an `InvitedGuest` (role Guest) of `agent-test` |

### Code that treats "has an `InvitedGuest` row" as "is attending"

A declined guest must not pass these checks:

| File | Use |
| --- | --- |
| `api/app/events/status.py` `get_event_status` | Guest status, `is_event_attendee` |
| `api/app/forms/lifecycle.py` `_is_eligible_to_register`, `_registration_confirmed` | New-forms registration eligibility and confirmation |
| `api/app/forms/visibility.py` (lines ~46, ~91) | `invited_guest` automatic tag, guest tag visibility |
| `api/app/forms/stats.py` `registration_stats` | Guest counts |
| `api/app/guestRegistrations/api.py:305` | Legacy guest registration form |
| `api/app/attendance/api.py:246` | Indemnity signing eligibility |
| `api/app/attendance/repository.py` (~146, ~230, ~249, ~261) | Check-in list, announcement/guest-list audiences, tag audiences |
| `api/app/documents/recipients.py` (~21, ~32) | Document recipients |
| `api/app/events/repository.py:53` `get_attended_by_user_for_organisation` | "Events attended" |
| `api/app/users/repository.py:75`, `:94` | Excluded from "no application" lists, shown as "Invited Guest" in user lists |

Role lookups that fall back to `'General Attendee'` (`profiles/api.py`, `attendance/api.py` badge/QR, `connections/api.py`, `reporting/api.py`) only display the role, so they stay as they are.

## 3. Design

### Data model

Add to `InvitedGuest`:

```python
class InvitedGuestStatus(str, enum.Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

class InvitedGuest(db.Model):
    ...
    status = db.Column(db.Enum(InvitedGuestStatus, name='invited_guest_status'),
                       nullable=False, default=InvitedGuestStatus.PENDING)
    responded_at = db.Column(db.DateTime(), nullable=True)
    rejection_note = db.Column(db.String(), nullable=True)
    # Bearer token in the invitation link. Unique, uuid4 via make_code.
    invitation_token = db.Column(db.String(255), nullable=False, unique=True, default=make_code)
    # True while the account was created by an admin for this invitation and
    # its owner hasn't chosen a password yet. Gates the account-setup step.
    account_setup_required = db.Column(db.Boolean(), nullable=False, default=False)
    invited_at = db.Column(db.DateTime(), nullable=True)

    @property
    def is_active(self):
        return self.status != InvitedGuestStatus.REJECTED

    def link_expires_at(self):
        """End of the event's last day, or None (no expiry) when the event has no end date."""
```

Repository additions (`api/app/invitedGuest/repository.py`):

```python
get_by_token(token)                  # -> InvitedGuest | None
get_active_for_event_and_user(event_id, user_id)   # status != REJECTED
active_filter()                      # InvitedGuest.status != REJECTED, for joins/subqueries
set_status(invited_guest, status, note=None)       # sets responded_at; clears note unless rejected
reset(invited_guest)                 # -> PENDING, clears note/responded_at, new token
```

All the call sites in the "treats as attending" table switch to the active variants, so **Pending and Accepted guests behave exactly as invited guests do today**, and only Declined guests drop out.

### Status transitions

| From | To | Who | How |
| --- | --- | --- | --- |
| PENDING | ACCEPTED | Guest | Invitation page **Accept**, or submitting the registration form (implicit accept) |
| PENDING / ACCEPTED | REJECTED | Guest | Invitation page or event home **Decline**, optional note |
| REJECTED | PENDING | Event admin | **Reset invitation** on the Invited Guests page. New token, invitation email sent again |
| REJECTED | ACCEPTED | — | Not allowed for the guest. The admin resets first |

When a guest declines after registering, their registration is kept but stops counting, because every check above filters out declined guests (see open question 2).

### Link and expiry

- The link is `{host}/invitation/{invitation_token}`, a top-level public route like `/reference/:token`, since the token identifies the event.
- It is valid until the end of `event.end_date`'s day (server time, the same as other date comparisons). If an event has no `end_date` (journals), the link doesn't expire. After the event ends the page says the invitation has expired and to contact the organisers.
- Resetting creates a new token, so links in older emails stop working.
- **Account setup is one-time.** Choosing a password through the token only works while `account_setup_required` is true. After that, the link can only accept or decline and show status. Otherwise a link that lives for weeks would also be a password reset for the same weeks.

### API

New resource module, `api/app/invitedGuest/invitation_api.py`. Public endpoints use the same organisation-from-host handling as other unauthenticated endpoints (`g.organisation`); a token from another organisation returns 404.

```
GET  /api/v1/guest-invitation?token=<t>
  200 {
    event: {id, key, name, start_date, end_date, is_registration_open,
            registration_url},   # registration_url: '/<key>/forms/<id>' or '/<key>/registration'
    role, status, rejection_note,
    account_setup_required: bool,
    user: {firstname, lastname, user_title, email}   # only when account_setup_required
    expired: bool
  }
  404 unknown token / other organisation

POST /api/v1/guest-invitation/accept
  body {token, firstname?, lastname?, user_title?, password?, policy_agreed?}
  - expired → 410 INVITATION_EXPIRED; rejected → 409 INVITATION_REJECTED
  - if account_setup_required: firstname, lastname, password, policy_agreed required;
    update AppUser, set_password, agree_to_policy, clear flag, status ACCEPTED,
    200 { status, login: user_info(user, roles) }   # frontend stores login → logged in
  - else: status ACCEPTED, 200 { status }           # no login issued (Q1)

POST /api/v1/guest-invitation/reject
  body {token, note?}            # note ≤ 1000 chars
  - expired → 410; account setup is NOT required to decline
  200 { status }

POST /api/v1/invitedGuest/respond          @auth_required (logged-in guest, event home)
  body {event_id, response: 'accept'|'reject', note?}
  - uses the current user's InvitedGuest; 404 if none; same transition rules

POST /api/v1/invitedGuest/reset           @event_admin_required
  body {event_id, invited_guest_id}
  - 409 unless status REJECTED; reset(), re-send invitation email; 200 serialized guest
```

Changes to existing endpoints:

- `InvitedGuestList` and `InvitedGuestAPI.get` add `status`, `responded_at`, `rejection_note`.
- `InvitedGuestAPI.post` and `CreateUser.post` require event admin (or system admin), the same check `InvitedGuestList.get` makes.
- `CreateUser.post` stops creating a `PasswordReset`, sets `account_setup_required=True` and sends `new-guest` with the invitation link.
- `events/api.py` event status adds `invited_guest_status` (`'pending'|'accepted'|'rejected'`) next to `invited_guest`.
- Guest registration submission (new forms `forms/lifecycle.py` submit path, and legacy `GuestRegistrationApi.post`) moves a PENDING guest to ACCEPTED.

Errors are added to `api/app/utils/errors.py`: `INVITATION_NOT_FOUND` (404), `INVITATION_EXPIRED` (410), `INVITATION_REJECTED` (409), `INVITATION_NOT_REJECTED` (409), `INVITATION_ACCOUNT_SETUP_INVALID` (400, missing fields or policy not agreed).

### Emails

- `GuestView` gains `invitation_url`. `values()` takes the `InvitedGuest` rather than the role string, and still accepts a bare role so `guest-removal` (sent after the row is deleted) keeps working, with an empty `invitation_url`.
- `AccountSetupView.set_password_url` is kept so customised `new-guest` templates still render, and it now points at the invitation link. `profile_url` is unchanged.
- The default `guest-invitation` and `new-guest` bodies (en and fr) are rewritten around a single button, **"Respond to invitation"** → `guest.invitation_url`, and mention when the link expires (`event.end_date`). `new-guest` keeps `sensitive=True`: the link is still a credential.
- Reset re-sends `new-guest` if `account_setup_required` is still true, otherwise `guest-invitation`.
- If `registry.py` has a test that renders every type's sample context, it must still pass with the new field.

### Permissions

| Action | Who |
| --- | --- |
| View invitation, accept, decline via token | Anyone holding the token (public) |
| Set the account password via token | Token holder, only while `account_setup_required` |
| Respond from the event home | The logged-in user the invitation belongs to |
| See status and note, reset | Event admin of the event, or system admin |
| Add or create guests | Event admin or system admin (tightened, see Decisions) |

### Frontend UX

**Invitation page:** `webapp/src/pages/guestInvitation/GuestInvitation.js`, route `<Route exact path="/invitation/:token">` in `App.js` (public, next to `/reference/:token`). It calls the new `guestInvitationService` (`webapp/src/services/invitedGuests/guestInvitation.service.js`).

| State | Shows |
| --- | --- |
| Loading / unknown token | Spinner / "This invitation link is not valid." |
| Expired | "This invitation has expired. Please contact the organisers." |
| Pending, account setup required | Heading "You're invited to {event} as {role}", dates. Form: title, first name, last name (pre-filled), email (read-only), password + confirm, privacy policy checkbox (same wording and link as `createAccount`). Buttons **Accept and continue** and **Decline invitation** |
| Pending, existing account | Same heading. **Accept** and **Decline invitation** |
| Accepted | "You have accepted." **Continue to registration** (if registration is open) and a secondary **Decline invitation** |
| Rejected | "You declined this invitation." Shows the note. "Contact the organisers if you've changed your mind." |

- **Decline** opens a `ConfirmModal` with an optional textarea, "Add a note for the organisers (optional)".
- After **Accept and continue**, the page stores `login` in `localStorage["user"]` the same way `userService.login` does, refreshes the app's user state the way the login page does, and redirects to `event.registration_url`, or to the event home if registration is closed.
- For an existing account, Accept redirects to `event.registration_url`. Logged-out users pass through the existing login redirect.

**Event home status:** `EventStatus.invitedGuestStatus`:

- Pending: "You have been invited as a {role}." with **Accept** and **Decline** (via `/api/v1/invitedGuest/respond`).
- Accepted: the current text and Register button, plus a small **Decline invitation** link.
- Rejected: "You declined your invitation to this event."

**Invited Guests page:** `InvitedGuestComponent.js`:

- New **Response** column with a coloured badge: Pending (grey), Accepted (green), Declined (red). A declined row shows the note in a tooltip/expandable cell, and a **Reset invitation** button that asks for confirmation through `ConfirmModal`, then calls `/reset` and shows a success alert.
- A new **Filter by response** select next to the role filter.
- The CSV download gains Response and Note columns.

### i18n, accessibility and edge cases

- Every new string gets `t()` and en/fr entries in `webapp/public/locales/{en,fr}/translation.json`, for example "Respond to invitation", "Accept and continue", "Decline invitation", "Add a note for the organisers (optional)", "Pending", "Accepted", "Declined", "Reset invitation", "Filter by response", "This invitation has expired. Please contact the organisers.", "This invitation link is not valid."
- Status badges include text, not only colour.
- If the guest is already logged in as a different user when they open the link, the page works from the token alone. After account setup, the stored login is replaced by the guest's.
- A guest accepting twice is idempotent and returns 200.
- When an admin deletes a guest, the token goes with the row, so the link returns 404.
- If an admin creates a guest whose email already has an account, `CreateUser` returns `EMAIL_IN_USE` as today.

## 4. Decisions

- **Status lives on `InvitedGuest`, not a new table**: one row per guest per event already exists, and history isn't needed.
- **Use a dedicated `invitation_token`, not `PasswordReset`**: the expiry rule (event end) and scope (one invitation) differ from password reset, and the 1-day reset expiry stays as it is.
- **Pending guests keep today's behaviour** (can register, count as guests). Only Declined guests drop out, so nothing changes for guests who never click the link.
- **Registering counts as accepting**: guests who go straight to registration (e.g. via the event page) don't have to accept separately.
- **Account setup via the token is one-time**: a link that lives until the event ends must not double as a password reset.
- **Reset creates a new token**: links in older emails stop working.
- **Declined guests can't re-accept on their own**: the issue gives the admin reset as the way back. Re-accepting would be a small change to add later.
- **Admins aren't emailed when a guest responds**: the list shows status and can be filtered. A `guest-response` email type is easy to add later.
- **Add/create guest endpoints get an event-admin check**: they're touched anyway, and today any logged-in user can add guests to any event.
- **The link doesn't expire for events without an end date**: there's no date to expire on, and admins can still delete the guest.
- **Existing rows are backfilled** (see Migration): guests with a registration become ACCEPTED, everyone else PENDING.

## 5. Open questions

1. **Can someone with an existing account accept or decline from the link without logging in?**
   - A: Yes. The token (sent only to their email) is enough to change their own invitation status, but it doesn't log them in. Continuing to registration goes through the normal login. *Fewest steps, and no login bypass.*
   - B: No. Existing-account guests must log in first, then accept or decline. *Slightly safer if an email is forwarded, but one more step and more support emails.*
   - C: Yes, and the token also logs them in. *Smoothest, but makes a weeks-long emailed link a login credential.*
   - Recommendation: **A**.

2. **What happens to a guest's registration when they decline after registering?**
   - A: Keep the registration response as it is. It stops counting because the guest is declined. If the admin resets and the guest accepts again, the registration comes back. *Simple, nothing lost.*
   - B: Withdraw the new-forms registration response (`FormResponse.is_withdrawn = True`), so it disappears from registration lists and exports. *Cleaner lists, but a reset guest must re-register, and legacy `GuestRegistration` has no withdraw flag.*
   - Recommendation: **A**, with registration lists and exports filtering out declined guests. This needs checking in `forms/stats.py` and the registration response list during implementation.

3. **Should pending guests be treated as attending (registration, guest-list announcements, document recipients, check-in)?**
   - A: Yes, as today. Only declined guests are excluded.
   - B: No, only accepted guests count. *Stricter, but every existing guest who never clicks the new link silently drops out of announcements and documents, and registration needs an extra accept step.*
   - Recommendation: **A**. The backfill and "registering counts as accepting" make B mostly unnecessary.

## 6. Implementation plan

### Task 1: Invitation status model, migration and active-guest filtering

- **Depends on:** none
- **Files:** `api/app/invitedGuest/models.py`, `api/app/invitedGuest/repository.py`, `api/migrations/versions/<rev>_invited_guest_status.py`, and the call sites listed under "Code that treats an `InvitedGuest` row as attending": `api/app/events/status.py`, `api/app/forms/lifecycle.py`, `api/app/forms/visibility.py`, `api/app/forms/stats.py`, `api/app/guestRegistrations/api.py`, `api/app/attendance/api.py`, `api/app/attendance/repository.py`, `api/app/documents/recipients.py`, `api/app/events/repository.py`, `api/app/users/repository.py`, `api/app/utils/testing.py`
- **Change:** Add `InvitedGuestStatus` and the columns from §3 Data model, plus `is_active` and `link_expires_at()`. Add the repository helpers `get_by_token`, `get_active_for_event_and_user`, `active_filter`, `set_status`, `reset`. Switch each listed call site so declined guests are excluded. `get_event_status` returns non-guest status for a declined guest (falls through to the application/offer path), and `EventStatus` gains `invited_guest_status`, which `events/api.py` serialises. Migration: add the columns, give each existing row a uuid token, set status ACCEPTED where a `guest_registration` row or a submitted new-forms registration exists for that user/event, otherwise PENDING, then add NOT NULL and unique constraints. Copy the revision format from an existing file and take `down_revision` from `flask db heads`. `testing.add_invited_guest` gains an optional `status`.
- **Acceptance criteria:**
  - `flask db upgrade` succeeds on the dev DB, and every existing row has a token and a status.
  - A REJECTED guest: `get_event_status` has no `invited_guest`; can't create a registration form response (403); isn't in the attendance guest list, the guest-list audience, document recipients, registration guest stats or attended events.
  - PENDING and ACCEPTED guests behave as before in all of the above.
- **Tests:** in `api/app/invitedGuest/tests.py` (or a new `tests_status.py`): parametrised over the three statuses for event status, `_is_eligible_to_register`, the attendance audience, document recipients and `link_expires_at` (with end date, without end date). The existing suites for those modules still pass.

### Task 2: Public invitation endpoints and guest/admin response endpoints

- **Depends on:** Task 1
- **Files:** `api/app/invitedGuest/invitation_api.py` (new), `api/app/invitedGuest/api.py`, `api/app/routes.py`, `api/app/utils/errors.py`, `api/app/forms/lifecycle.py` (implicit accept on registration submit), `api/app/guestRegistrations/api.py` (same for legacy)
- **Change:** Implement `GET /api/v1/guest-invitation`, `POST /api/v1/guest-invitation/accept`, `POST /api/v1/guest-invitation/reject`, `POST /api/v1/invitedGuest/respond` and `POST /api/v1/invitedGuest/reset` exactly as in §3 API (reset's email is added in Task 3; here it only resets). Add `status`, `responded_at` and `rejection_note` to `InvitedGuestList` and `InvitedGuestAPI.get`. Add the event-admin check to `InvitedGuestAPI.post` and `CreateUser.post`. Submitting a guest registration moves PENDING to ACCEPTED.
- **Acceptance criteria:**
  - Unknown token, or a token from another organisation → 404. A token after the event's end date → 410 on accept and reject, and `expired: true` on GET.
  - Accept with `account_setup_required` and valid fields sets the name and password, clears the flag, and returns a `login` with a token that authenticates. A second accept with a password changes nothing about the password.
  - Accept without setup required returns no `login`.
  - Reject stores the note and works from PENDING and ACCEPTED. Accept on REJECTED → 409.
  - `/respond` acts only on the current user's own invitation. `/reset` is event-admin only, 409 unless REJECTED, and changes the token.
  - A non-admin calling `POST /api/v1/invitedGuest` or `/invitedGuest/create` gets 403.
- **Tests:** one test class per endpoint, covering the happy path, expired, wrong organisation, invalid transition, missing setup fields/policy and permissions (guest, other user, event admin, system admin). Plus implicit accept on registration submit for new forms and legacy. Capture ids before requests (see `.claude/CLAUDE.md`).

### Task 3: Invitation emails use the single link

- **Depends on:** Task 2
- **Files:** `api/app/email_template/views.py` (`GuestView`, `AccountSetupView`), `api/app/email_template/registry.py` (descriptions), `api/app/email_template/defaults/{guest-invitation,new-guest}.{en,fr}.md`, `api/app/invitedGuest/api.py` (callers pass the `InvitedGuest`; `CreateUser` drops `PasswordReset`, sets `account_setup_required=True`), `invitation_api.py` (reset re-sends)
- **Change:** As in §3 Emails.
- **Acceptance criteria:**
  - Inviting an existing user queues `guest-invitation` whose body contains `/invitation/<token>`.
  - Creating a guest queues `new-guest` with the same link and no `resetPassword` link, and creates no `PasswordReset` row.
  - Reset re-sends the right type with the new token.
  - `guest-removal` still renders.
  - The email template preview and sample tests pass.
- **Tests:** assert on the queued outbox rows for invite, create and reset, and render all four guest templates with sample context.

### Task 4: Public invitation page

- **Depends on:** Task 2 (Task 3 to receive real links)
- **Files:** `webapp/src/pages/guestInvitation/{index.js,GuestInvitation.js,GuestInvitation.css}` (new), `webapp/src/services/invitedGuests/guestInvitation.service.js` (new), `webapp/src/App.js`, `webapp/public/locales/{en,fr}/translation.json`
- **Change:** The page and its states from §3 Frontend UX, including the decline modal with an optional note, account setup, storing the login and redirecting to registration.
- **Acceptance criteria:** `pnpm run build` passes. Every state in the table renders. Accept-and-continue lands logged in on the registration form.
- **Verification:** scenarios 1, 2, 3, 6

### Task 5: Event home response controls and Invited Guests admin column

- **Depends on:** Task 2
- **Files:** `webapp/src/components/EventStatus.js`, `webapp/src/services/invitedGuests/invitedGuests.service.js` (`respond`, `resetInvitation`), `webapp/src/pages/invitedGuests/components/InvitedGuestComponent.js`, `webapp/src/pages/invitedGuests/InvitedGuests.css`, `webapp/public/locales/{en,fr}/translation.json`
- **Change:** The event home pending/accepted/rejected states with Accept/Decline. On the Invited Guests page: the Response column and badge, the note display, Reset invitation with confirmation, the response filter, and the CSV columns.
- **Acceptance criteria:** `pnpm run build` passes. The admin sees the correct badge per guest, filters by response, and resets a declined guest, whose badge returns to Pending.
- **Verification:** scenarios 4, 5, 7

## 7. Verification scenarios

The seed has `claude-guest@baobab.test` as a guest of `agent-test`. Scenarios 1–3 also need a guest **created** through the admin page (new account), whose invitation token is read from the dev DB (`select invitation_token from invited_guest ...`) because email delivery isn't available. Scenarios that depend on the email only check that the outbox row exists and contains the link.

| # | Role | Start at | Steps | Expected |
| --- | --- | --- | --- | --- |
| 1 | Event admin, then logged out | `/agent-test/invitedGuests` | Create a guest with a new email. Log out. Open `/invitation/<token>`. Edit the first name, set a password, tick the policy, click **Accept and continue** | Lands logged in as the new guest on the `agent-test` registration form. Admin list shows Accepted |
| 2 | New guest from 1, logged out | `/invitation/<same token>` | Reopen the link | Shows Accepted with **Continue to registration** and **Decline**. No password form |
| 3 | Anonymous | `/invitation/<token>` of a fresh pending guest | Click **Decline invitation**, enter the note "Clashes with another conference", confirm | Shows Declined with the note. The admin list shows the Declined badge and the note |
| 4 | Guest (`claude-guest`) | `/agent-test` | Event home shows Pending with Accept/Decline. Click **Accept**, then **Decline invitation** with no note | Status card changes to Accepted, then to "You declined…". Opening `/agent-test/registration` is refused |
| 5 | Event admin | `/agent-test/invitedGuests` | Filter by Declined. Click **Reset invitation** on the guest from 4 and confirm | Badge shows Pending. The outbox has a new `guest-invitation` row. The old token returns "not valid" |
| 6 | Anonymous | `/invitation/<token>` after setting the event's `end_date` in the past in the dev DB (revert afterwards) | Open the link | "This invitation has expired…", with no buttons |
| 7 | Applicant (not admin) | `/agent-test/invitedGuests` and direct API `POST /api/v1/invitedGuest/reset` | Try to view the page and reset | Page denied or hidden. API returns 403 |

## 8. Migration and rollout

- One Alembic migration (Task 1): add the columns nullable, backfill the token (uuid per row), status (ACCEPTED if registered, otherwise PENDING), `account_setup_required = false` and `invited_at = NULL`, then set NOT NULL and add the unique index on `invitation_token`, and create the `invited_guest_status` enum type. The downgrade drops the columns and the type.
- Existing guests created before this change have `account_setup_required = false`, so their new link can't set a password. Those who never set one can still use **Forgot password**, as today.
- Emails already sent keep their old links, which work as before. `PasswordReset` and `/resetPassword` are unchanged.
- Event-level customised `guest-invitation`/`new-guest` templates keep rendering. They only pick up the single link if they use `account.set_password_url` (now pointing at it) or are updated to `guest.invitation_url`. The release notes should tell admins this.
