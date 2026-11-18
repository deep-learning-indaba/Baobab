# Profile picture — Design Doc

2026-11-12 · Drafted by Claude for #1433

## 1. Summary

Attendees can upload a profile picture on **My Profile** (`/<event>/app/profile`). Before upload, the browser crops it to a square and shrinks it to 512×512. The picture then appears on **Browse attendees**, on the member profile page and in the other places that already show avatars. Any attendee can report a profile, its picture or its content, to the event's moderators: comms officers and event admins, the same people who moderate the discussion board. Moderators work through a **Reported people** queue where they can remove the picture or dismiss the report.

**Goals**

- A confirmed guest can upload, replace and remove their own profile picture from My Profile.
- Large photos are cropped and resized on the device, so a 12 MB phone photo uploads as a JPEG of roughly 50–100 KB.
- The picture shows on Browse attendees, the member profile page, Connections and Scan & Connect.
- An attendee can report another attendee's profile from that attendee's profile page, choosing "Photo" or "Profile content".
- Comms officers and event admins see open profile reports in a queue, with the reported picture and profile text, and can **remove the photo** or **dismiss** the report.

**Non-goals**

- **In-browser crop or zoom editor.** The picture is centre-cropped automatically. A cropping UI needs a new dependency and is easy to add later.
- **Automatic image scanning or auto-hiding after N reports.** The discussion board has neither, and either one needs a policy decision first.
- **Email or push notifications to moderators.** Discussion reports don't send any either (see Decisions).
- **Per-event pictures.** `member_profile` is global per user ("one identity, many events"), so the picture is the same in every event.
- **Moderators editing a user's headline or about text.** See open question 2.
- **Locking down `GET /api/v1/file`.** It is unauthenticated for every upload (discussion attachments, organisation logos). Profile pictures follow the same model; see Decisions.

## 2. Current state

Most of the plumbing already exists. `member_profile.photo_url` is stored, accepted by `PUT /api/v1/profile` and returned by every profile endpoint, and Browse attendees already renders it. Nothing in the UI ever sets it.

| Layer | Where | Relevant detail |
| --- | --- | --- |
| Model | `api/app/profiles/models.py` `MemberProfile` | One row per user (`user_id` unique, no `event_id`). `photo_url = String(512)`, nullable. `visibility` is `'community'` or `'hidden'`. |
| Profile API | `api/app/profiles/api.py` `ProfileAPI` | `GET/PUT /api/v1/profile`, `@auth_required`, and only your own profile. PUT is partial (`if args[x] is not None`). `photo_url` is accepted as **any string, unvalidated** (~L105). |
| Directory API | `ProfileListAPI` (`/api/v1/profile/list`), `ProfileViewAPI` (`/api/v1/profile/view`) | Both require `attendance_repository.is_confirmed_guest(event_id, me)`. Both return `photo_url` via `_profile_to_dict`. The hidden-profile stub returns `photo_url` too (~L155). |
| Other avatar sources | `api/app/connections/api.py` ~L41/54/80, `api/app/discussion/api.py` `_author_block` ~L52 | Both return `photo_url` from `MemberProfile`. |
| File storage | `api/app/files/api.py` `FileUploadAPI` | `POST /api/v1/file` (multipart, **no auth**) stores the blob under `uuid4().hex`, with the client's content type, up to `FILE_SIZE_LIMIT` (50 MB in compose). It returns `{file_id}`. `GET ?filename=&disposition=inline` proxies the blob and, for inline images, sends `Cache-Control: public, max-age=86400`. Storage comes from `app.utils.storage.get_storage_bucket()`, which tests mock (`app/files/tests.py` `_mock_bucket`). |
| Image helpers | `webapp/src/utils/images.js` `getImage`, `webapp/src/utils/files.js` `getFileURL` | `getImage(value)` resolves a 32-hex file id to the inline file URL, passes absolute URLs through and looks up bundled images. |
| Client resize | `webapp/src/components/Attachments.js` `resizeIfNeeded` (L35–71, not exported) | Uses `createImageBitmap` and a canvas, limits the longest side to 1600 px, re-encodes as JPEG at 0.82 (PNG stays PNG), skips GIF and SVG, has an 8 s timeout and falls back to the original file. No crop. |
| Upload UI pattern | `webapp/src/pages/organisationSettings/components/ImageField.js` | Checks `image/*`, calls `fileService.uploadFile`, gets back a file id and previews it with `getImage`. |
| My Profile | `webapp/src/pages/eventApp/MyProfile.js` | Text fields, interests, links and a visibility checkbox, with one "Save profile" button. No photo control, and the payload has no `photo_url`. |
| Browse attendees | `webapp/src/pages/eventApp/ProfileBrowser.js` ~L103 | `<img src={p.photo_url}>` as a 48 px circle, falling back to the first initial. A raw `src` would break on a file id. |
| Profile page | `webapp/src/pages/eventApp/ViewMemberProfile.js` L59, L73 | Raw `<img src={profile.photo_url}>`. There is no report action. |
| Local avatars | `Connections.js` L7 `Avatar`, `ScanConnect.js` L17 `Avatar` | Two copies of the same component, both using a raw `src`. |
| Discussion reports | `api/app/discussion/models.py` `DiscussionReport`, `api.py` L533–652 | Table `discussion_report`: `message_id`, `event_id`, `reporter_user_id`, `reason`, `status` (`open`/`dismissed`/`actioned`) and `created_at`, unique per (message, reporter). Reporting is idempotent. The queue is `GET /api/v1/discussion/report?event_id=` and dismissal is `POST …/report/<id>/dismiss`. Both are gated by `_is_moderator` = `user.is_comms_officer(event_id)`, which includes event admins and site admins. There are no notifications and no auto-hide. |
| Moderator UI | `webapp/src/pages/eventApp/DiscussionReportsAdmin.js`, route `/<event>/discussionReportsAdmin` (`EventHome.js` ~L983), nav `EventNav.js` ~L121 under "Communications", gated by `isCommsOfficer` | Report cards with Delete and Dismiss buttons. |
| Person reports | `api/app/connections/models.py` `ConnectionReport`, `ConnectionReportAPI` (`POST /api/v1/connection/report`), UI in `ScanConnect.js` ~L140 | Table `connection_report`: `event_id`, `reporter_user_id`, `reported_user_id`, `reason` and `created_at`. There is **no status and no reader**. Nothing lists or resolves these rows, even though the UI says "Thanks — the organising team has been notified." The endpoint doesn't check that the reported user exists or attends the event, and it allows self-reports and duplicates. |

## 3. Design

### Data model

The plan below reuses `connection_report` as the single "reported person" table (open question 1, recommendation A). Add these columns:

```python
# api/app/connections/models.py
class ConnectionReport(db.Model):
    __tablename__ = 'connection_report'
    id, event_id, reporter_user_id, reported_user_id, reason, created_at   # existing
    category = db.Column(db.String(16), nullable=False, server_default='person')
    #   'photo' | 'profile' | 'person'   (Scan & Connect reports are 'person')
    reported_photo_url = db.Column(db.String(512), nullable=True)
    #   snapshot of member_profile.photo_url when reported, so moderators see the
    #   picture that was reported even if the user changes it later
    status = db.Column(db.String(16), nullable=False, server_default='open')
    #   'open' | 'dismissed' | 'actioned'
    resolved_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    resolved_at = db.Column(db.DateTime(), nullable=True)
    __table_args__ = (db.Index('ix_connection_report_event_status', 'event_id', 'status'),)
```

`member_profile` needs no schema change. `photo_url` now holds an uploaded file id (32 lowercase hex characters), as the organisation logo fields do. The column stays named `photo_url` so the four existing serializers and their consumers don't change.

### API

**`PUT /api/v1/profile`** (existing). `photo_url` gets validated:

| Value sent | Result |
| --- | --- |
| key absent / `null` | unchanged (as today) |
| `""` | cleared: stored as `NULL` |
| 32-hex file id | The blob is checked with `storage.get_storage_bucket().blob(id).reload()`. Its `content_type` must be `image/jpeg`, `image/png` or `image/webp`, and its `size` at most `PROFILE_PHOTO_MAX_BYTES = 2 * 1024 * 1024`. If not, the response is 400 `{"message": "Profile photo must be a JPEG, PNG or WebP image under 2 MB", "field": "photo_url"}`. A missing blob also gets a 400. |
| anything else (URLs, paths) | 400 with the same shape |

The server check exists because `POST /api/v1/file` takes any file: without it, someone could skip the client-side resize and put a 50 MB file or an SVG in everyone's attendee list. The check lives in a helper, `validate_profile_photo(file_id)` in `api/app/profiles/repository.py`, so tests can mock the storage call.

**`POST /api/v1/connection/report`** (existing; extended and tightened):

```json
{ "event_id": 7, "reported_user_id": 42, "category": "photo", "reason": "optional, ≤ 1000" }
```

- `category` is optional and defaults to `'person'`, so `ScanConnect.js` keeps working unchanged. Any other value returns 400.
- The reporter must be a confirmed guest (as today, `NOT_A_GUEST`).
- **New checks:** `reported_user_id != me` (400 otherwise). The reported user must be a confirmed guest of `event_id` (404 `USER_NOT_FOUND` otherwise).
- **Idempotent:** if the reporter already has an *open* report on this user, event and category, the response is 200 with `{"id", "status": "reported"}` and no new row is created. Otherwise a row is created and the response is 201 with the same body. `reported_photo_url` is snapshotted from the profile.
- Emits engagement event `'profile_reported'` with `{reported_user_id, category}` (best effort, like discussion's `_emit`).

**`GET /api/v1/connection/report?event_id=`** (new, moderator). Returns open reports, oldest first:

```json
[{
  "report_id": 12, "category": "photo", "reason": "…", "created_at": "2026-11-12T10:00:00Z",
  "reporter":  { "user_id": 5,  "firstname": "…", "lastname": "…", "photo_url": "…" },
  "reported":  { "user_id": 42, "firstname": "…", "lastname": "…", "photo_url": "<current>",
                 "headline": "…", "about": "…", "visibility": "community" },
  "reported_photo_url": "<snapshot>",
  "photo_changed": true
}]
```

`photo_changed` is true when the snapshot differs from the current `photo_url`. The UI then shows both pictures.

**`POST /api/v1/connection/report/<id>/dismiss`** `{event_id}` (new, moderator). Sets `status='dismissed'`, `resolved_by_user_id` and `resolved_at`. It returns 404 if the report belongs to a different event.

**`POST /api/v1/connection/report/<id>/remove-photo`** `{event_id}` (new, moderator):

- Sets the reported user's `member_profile.photo_url = NULL`.
- Marks **every open `photo` report** on that user in this event as `actioned`, because one removal answers them all. `profile` and `person` reports stay open.
- Emits `'profile_photo_moderated'`.
- Returns 200 `{"actioned_report_ids": [...]}`.
- Returns 404 for a report from another event.
- If the user has no photo any more, it still resolves the reports and returns 200, so it is idempotent.

All three moderator endpoints use the same check as discussion: `user_repository.get_by_id(me).is_comms_officer(event_id)`. Because `discussion/api.py` already has a private `_is_moderator`, add a public `is_event_moderator(user_id, event_id)` to `app/utils/auth.py` and have both modules use it.

### Permissions

| Action | Who |
| --- | --- |
| Upload, change or remove own picture | Any logged-in user, through their own profile (as today). In practice only confirmed guests reach My Profile. |
| See pictures in the directory or on profiles | Confirmed guests of the event (unchanged) |
| Report a profile | Confirmed guest of the event, about another confirmed guest of the same event, never themselves |
| View the queue, dismiss, remove a photo | Comms officer or event admin of that event, or a site admin (`is_comms_officer`) |

Removing a photo clears the user's single global picture, so the change shows in every event they attend. See open question 2.

### Frontend UX

**Shared image utility.** Move `resizeIfNeeded` out of `Attachments.js` into `webapp/src/utils/imageResize.js`:

```js
export function resizeImage(file, { maxDimension, squareCrop = false, quality = 0.82,
                                    skipBelowBytes = 0, timeoutMs = 8000 }) → Promise<File>
```

`Attachments.js` calls it with `{ maxDimension: 1600, skipBelowBytes: 1.5 MB }`, which behaves exactly as today. For profile pictures, `squareCrop: true` centre-crops to the shorter side, then scales to `maxDimension: 512`. The output is always JPEG at 0.85, because an avatar needs no alpha and PNGs of photos are large. Transparent PNGs get painted onto a white background first.

The fallback differs for avatars. If the resize fails or times out, for example on HEIC in a browser that can't decode it, the profile picker reports an error ("We couldn't process this image. Try a JPEG or PNG.") instead of uploading the original. The server would reject the original anyway if it is over 2 MB or the wrong type.

**Shared `Avatar` component.** Add `webapp/src/components/Avatar.js`:

```jsx
<Avatar photoUrl={p.photo_url} firstname={p.firstname} lastname={p.lastname} size="sm|md|lg|xl" />
```

It resolves the source through `getImage(photoUrl)` and falls back to initials when there is no picture or the image fails to load (`onError`). The sizes are 32, 48, 80 and 96 px, all `rounded-full object-cover`. It replaces the local `Avatar` functions in `Connections.js` and `ScanConnect.js` and the inline `<img>`/initial blocks in `ProfileBrowser.js` and `ViewMemberProfile.js`.

**My Profile** (`MyProfile.js`). Add a "Profile photo" section at the top of the form card:

- An `xl` `Avatar` preview, then an **Upload photo** button (**Change photo** once a picture is set), a **Remove** link while a photo is set, and the hint "Square photos work best. We'll resize large images for you."
- A hidden `<input type="file" accept="image/jpeg,image/png,image/webp,image/heic">` (HEIC is listed so iOS offers the camera roll; it converts where the browser can decode it).
- On select, the flow is `resizeImage(…, { squareCrop: true, maxDimension: 512 })`, then `fileService.uploadFile`, then `profileService.updateMyProfile({ event_id, photo_url: fileId })`. The picture **saves immediately** without waiting for "Save profile" (see Decisions). A spinner shows over the avatar while this runs.
- Remove asks `window.confirm(t('Remove your profile photo?'))`, then sends PUT `{ photo_url: '' }`.
- Errors (bad type, resize failure, upload error, server 400) show inline under the photo controls, not in the page-level alert.
- `handleSave` doesn't send `photo_url`. Because the PUT is partial, saving the text fields can never undo a photo change.

**Browse attendees** (`ProfileBrowser.js`). Use `Avatar size="md"`. The layout stays the same.

**Member profile** (`ViewMemberProfile.js`):

- Use `Avatar`.
- Below the cards on someone else's profile (`profile.user_id !== props.user.id`), add a muted **Report profile** text button. It is hidden on your own profile.
- It opens an inline panel styled like `ScanConnect.js` ~L140:
  - a radio group "What's the problem?" with *Photo* (only when the profile has a photo) and *Profile content*;
  - an optional reason textarea (maxLength 1000);
  - **Send report** and **Cancel** buttons.
- On success, the panel is replaced by "Thanks. The event's moderators will review this."

**Moderator queue.** Add a page `webapp/src/pages/eventApp/ProfileReportsAdmin.js` at route `/<event>/profileReportsAdmin`, and a nav link **Reported people** under "Communications" in `EventNav.js`, gated by `isCommsOfficer` beside "Reported messages". It follows the layout of `DiscussionReportsAdmin.js`. Each card shows:

- the category badge (Photo / Profile content / Person), the reporter, the time (`formatInEventTz`) and the reason;
- the reported person: an `lg` avatar of the **reported** picture, plus "Current photo" when `photo_changed`. Also their name, headline and the first 300 characters of the about text, with a link to their profile page;
- **Remove photo** (shown when the current photo is set, with a confirm) and **Dismiss**.

The page shows "Access denied" on 403, like the discussion queue.

**Services.** In `webapp/src/services/eventApp/connection.service.js`:

- extend `report(eventId, userId, reason, category)`;
- add `listReports(eventId)`, `dismissReport(eventId, reportId)` and `removePhoto(eventId, reportId)`.

### i18n, accessibility and edge cases

- **New `en`/`fr` keys:** `Profile photo`, `Upload photo`, `Change photo`, `Remove`, `Remove your profile photo?`, `Square photos work best. We'll resize large images for you.`, `We couldn't process this image. Try a JPEG or PNG.`, `Photo upload failed.`, `Report profile`, `What's the problem?`, `Photo`, `Profile content`, `Person`, `Thanks. The event's moderators will review this.`, `Reported people`, `No reported people.`, `Current photo`, `Remove photo`, `Remove this photo?`, `View profile`.
- **Reused keys:** `Send report`, `Cancel`, `Reason`, `Reported by`, `Dismiss`, `Access denied` and `Optional: describe the issue`.
- **Alt text:** the avatar `alt` is `""` where the name sits beside it (lists and cards). On My Profile and in the moderator queue it is `t('Profile photo of {{name}}')`. The file input has an accessible label, and the visible button triggers it.
- **Animated GIF / SVG.** They aren't offered in `accept`. If one is picked anyway, the client rejects it, and the server rejects the content type.
- **Broken or removed blob.** `Avatar` falls back to initials on `onError`.
- **Old picture blobs.** Replacing or removing a picture leaves the previous blob in GCS. Discussion attachments and logos behave the same way, and nothing references the old blob afterwards. Its id was only ever shown to confirmed guests.
- **Hidden profiles.** `ProfileViewAPI` returns the picture on the hidden-profile stub today. This design leaves that alone; it is noted below.
- **A reported user leaves the event** (invitation removed). Their reports stay in the queue, and the profile link may show "not a guest". The moderator can still dismiss or remove the photo.

## 4. Decisions

- **Reuse `member_profile.photo_url` and store a file id**: the column and every serializer already exist. It is the same convention as the organisation logos, and `getImage` already resolves it.
- **Reject URLs in `photo_url`**: no UI sets one today, so there are no rows to migrate (verify in prod before deploy, see section 8). Allowing URLs would let users hotlink external images that skip both the size limit and moderation snapshots.
- **Validate type and size on the server**: `POST /api/v1/file` takes anything, and client-side resizing can be bypassed.
- **512×512 square JPEG at 0.85**: it is sharp at the largest display size (96 px at 3× DPR is 288 px) with room to spare, and is typically under 100 KB.
- **Automatic centre crop, no crop UI**: there are no new dependencies, and most uploads are portraits where a centre crop works.
- **The picture saves immediately on upload**: users expect avatar pickers to apply right away, and a picture that vanishes because they didn't press "Save profile" is a common complaint. The partial PUT makes this safe.
- **Moderators are comms officers plus event admins**: the same group as the discussion board, so there is no new role to assign.
- **No moderator notifications**: discussion reports don't notify anyone either. The queue in the sidebar is the workflow. Notifications can be added for both queues together later.
- **The report button is on the profile page, not the directory cards**: each card is a single `<Link>`, and a menu on it would compete with the navigation. Reports are rare, so one click deeper is fine.
- **One removal resolves all open photo reports on that user**: otherwise moderators would have to dismiss duplicates by hand.
- **`GET /api/v1/file` stays unauthenticated**: changing it affects every upload in the app. Picture ids are uuid4 and only shown to confirmed guests. That is the same exposure as discussion images.

## 5. Open questions

1. **Where should profile reports live?**
   - A: Extend `connection_report` (add `category`, `status`, the photo snapshot and resolution columns) and build one **Reported people** queue. Reports from Scan & Connect, which are currently written and never read, then reach moderators too, which makes "the organising team has been notified" true. The existing rows start as `open` and appear in the queue once on deploy.
   - B: A new `profile_report` table and a separate queue, leaving `connection_report` as it is. The models are cleaner, but there are two "report a person" mechanisms and the Scan & Connect reports stay invisible.
   - Recommendation: **A**. It reuses what exists and fixes the dead end in Scan & Connect. The cost is a table name that's slightly off and a one-off batch of old reports in the queue.

2. **What can a moderator do beyond removing the photo?** The picture and profile are global, but moderators are per event.
   - A: Only **Remove photo** (global) and **Dismiss**. For abusive profile text, the moderator contacts the person or an admin. It is the smallest scope, but a "Profile content" report has no in-app action.
   - B: Also **Hide from this event's directory**, a new `member_profile_event_hide(event_id, user_id, hidden_by_user_id, created_at)` table. `list_community` skips hidden users and `ProfileViewAPI` returns the hidden stub for that event. Also add an "Unhide" action on a "Hidden profiles" tab in the queue. This costs one more table, two endpoints and a tab, but moderators get a tool for text abuse without touching other events.
   - C: Like A, but **Remove photo** only hides the picture within the reporting event. That is consistent per-event scoping, but it needs per-event photo state, and a removed abusive picture would still show at the user's other events.
   - Recommendation: **A** for this issue, with B as a follow-up if text abuse turns out to be a real problem. Removing a picture globally is reasonable, because an image abusive enough to remove at one event is not wanted at others.

3. **Should a moderator's photo removal be visible to the user?**
   - A: Silent. The picture just disappears, and the user can upload another one.
   - B: Record `photo_removed_at` on `member_profile` and show a notice on My Profile: "A moderator removed your photo. Please choose a picture that follows the event's code of conduct." The notice clears on the next upload. This costs one column and a few lines of UI.
   - Recommendation: **B**. Without it, users see their picture vanish with no explanation and are likely to re-upload the same one.

## 6. Implementation plan

The plan follows the recommendations: 1A, 2A and 3B. If 3A is chosen, drop the `photo_removed_at` parts of Tasks 1, 3 and 6.

### Task 1: Profile photo validation on `PUT /api/v1/profile`

- **Depends on:** none
- **Files:** `api/app/profiles/api.py`, `api/app/profiles/repository.py`, `api/app/profiles/models.py`, `api/migrations/versions/<rev>_profile_photo_removed_at.py`, `api/app/profiles/tests.py`
- **Change:**
  - Add `validate_profile_photo(file_id)` in `repository.py`. It returns an error string or `None`, and checks the 32-hex format, that the blob exists (`storage.get_storage_bucket().blob(id).reload()`; catch `google.api_core.exceptions.NotFound`), `content_type in ('image/jpeg', 'image/png', 'image/webp')` and `size <= PROFILE_PHOTO_MAX_BYTES` (2 MB, a module constant).
  - In `ProfileAPI.put`, `""` stores `NULL`, and anything else must pass validation or the response is 400 `{"message", "field": "photo_url"}`.
  - Add the nullable column `photo_removed_at = db.Column(db.DateTime())` to `MemberProfile`, with a migration whose `down_revision` is the current `flask db heads`.
  - When `photo_url` is set to a valid id, set `photo_removed_at = None`.
  - Add `photo_removed_at` (ISO string or null) to the `ProfileAPI.get`/`put` response only, not to the list or view responses.
- **Acceptance criteria:**
  - PUT with a valid image id stores it and returns it.
  - `""` clears it.
  - A URL, a non-hex string, a missing blob, a PDF blob and a 3 MB blob each return 400 and leave the stored value unchanged.
  - A PUT without `photo_url` leaves it unchanged.
- **Tests:** mock `app.profiles.repository.storage.get_storage_bucket` as `app/files/tests.py` does. Cover:
  - valid jpeg;
  - clear;
  - URL rejected;
  - bad format rejected;
  - NotFound rejected;
  - wrong type rejected;
  - too large rejected;
  - omitted key unchanged;
  - upload resets `photo_removed_at`.
  - Verify the migration with `flask db upgrade`.

### Task 2: Profile reports: model, report endpoint and moderator helper

- **Depends on:** none
- **Files:** `api/app/connections/models.py`, `api/app/connections/repository.py`, `api/app/connections/api.py`, `api/app/utils/auth.py`, `api/app/discussion/api.py`, `api/migrations/versions/<rev>_connection_report_moderation.py`, `api/app/connections/tests.py`
- **Change:**
  - Add the `category`, `reported_photo_url`, `status`, `resolved_by_user_id` and `resolved_at` columns and the `(event_id, status)` index to `ConnectionReport`, using `server_default` so existing rows become `'person'`/`'open'`. Write the migration (chain it after Task 1's if both are on the branch; check `flask db heads`).
  - Extend `ConnectionReportAPI.post` as described in section 3 "API":
    - an optional `category` (`photo` | `profile` | `person`, default `person`, otherwise 400);
    - reject self-reports with 400;
    - the reported user must be a confirmed guest of the event, otherwise 404 `USER_NOT_FOUND`;
    - snapshot `reported_photo_url` from `MemberProfile`;
    - an idempotent 200 when the same reporter has an open report on the same user, event and category; otherwise 201 with `{"id", "status": "reported"}`;
    - emit `'profile_reported'` best-effort.
  - Add `is_event_moderator(user_id, event_id)` to `app/utils/auth.py` (it loads the user and returns `is_comms_officer(event_id)`). Make `discussion/api.py::_is_moderator` delegate to it.
- **Acceptance criteria:**
  - Old-style requests with no category still return 201 with `status: reported`.
  - The new validations behave as specified.
  - Existing discussion tests pass unchanged.
- **Tests:**
  - report with category photo, which snapshots the photo;
  - default category;
  - invalid category gives 400;
  - self-report gives 400;
  - reported user not at the event gives 404;
  - reporter not a guest gives NOT_A_GUEST;
  - a duplicate open report gives 200 with the same id;
  - re-reporting after dismissal creates a new row;
  - run `app/discussion` tests.

### Task 3: Moderator queue endpoints

- **Depends on:** Task 1, Task 2
- **Files:** `api/app/connections/api.py`, `api/app/connections/repository.py`, `api/app/routes.py`, `api/app/connections/tests.py`
- **Change:**
  - Add `GET` to the resource at `/api/v1/connection/report` (the queue, open reports oldest first, in the JSON shape in section 3).
  - Add `ConnectionReportDismissAPI` at `/api/v1/connection/report/<int:report_id>/dismiss` and `ConnectionReportRemovePhotoAPI` at `/api/v1/connection/report/<int:report_id>/remove-photo`.
  - All three require `is_event_moderator`, otherwise `FORBIDDEN`. A report from another event returns 404.
  - Remove-photo sets `photo_url = NULL` and `photo_removed_at = now`, marks all open `photo` reports for that (event, reported user) as `actioned` with the resolver and time, emits `'profile_photo_moderated'`, and returns `{"actioned_report_ids"}`.
- **Acceptance criteria:**
  - A comms officer and an event admin both get the queue.
  - A confirmed guest without the role gets 403 on all three endpoints.
  - Dismissed and actioned reports leave the queue.
  - `photo_changed` is correct.
  - Remove-photo leaves `profile` and `person` reports open.
- **Tests:**
  - queue as comms officer;
  - queue as event admin;
  - queue as a guest gives 403;
  - dismiss;
  - dismiss from another event gives 404;
  - remove-photo clears the photo, sets `photo_removed_at` and actions only open photo reports;
  - remove-photo when the photo is already gone still returns 200;
  - `photo_changed` true and false.

### Task 4: Shared image resize utility and `Avatar` component

- **Depends on:** none
- **Files:** `webapp/src/utils/imageResize.js` (new), `webapp/src/components/Attachments.js`, `webapp/src/components/Avatar.js` (new), `webapp/src/pages/eventApp/ProfileBrowser.js`, `webapp/src/pages/eventApp/ViewMemberProfile.js`, `webapp/src/pages/eventApp/Connections.js`, `webapp/src/pages/eventApp/ScanConnect.js`
- **Change:**
  - Extract `resizeImage(file, options)` as described in section 3 "Frontend UX", with `squareCrop`, a white background for JPEG output, and a `rejectOnFailure` option (avatars pass `true`, attachments keep the fall-back-to-original behaviour). `Attachments.js` uses it with its current constants.
  - Add `Avatar` with `getImage` resolution, an initials fallback, `onError` fallback and sizes `sm|md|lg|xl`. Replace the avatar rendering in the four pages.
- **Acceptance criteria:**
  - `pnpm run build` passes.
  - Discussion image attachments still upload and resize as before.
  - A profile whose `photo_url` is a file id renders on Browse attendees, the profile page, Connections and Scan & Connect.
  - A null or broken id shows initials.
- **Verification:** scenarios 2 and 3.

### Task 5: Upload, change and remove on My Profile

- **Depends on:** Task 1, Task 4
- **Files:** `webapp/src/pages/eventApp/MyProfile.js`, `webapp/public/locales/{en,fr}/translation.json`
- **Change:**
  - Add the "Profile photo" section described in section 3: preview, upload or change button, remove, and the hint.
  - The upload path is `resizeImage({ squareCrop: true, maxDimension: 512, quality: 0.85, rejectOnFailure: true })`, then `fileService.uploadFile`, then `profileService.updateMyProfile({ event_id, photo_url })`, with a spinner and inline errors.
  - Remove sends `photo_url: ''` after a confirm.
  - When `profile.photo_removed_at` is set and there is no photo, show the notice "A moderator removed your photo. Please choose a picture that follows the event's code of conduct." (an amber info box above the controls).
  - Add all new strings to `en` and `fr`.
- **Acceptance criteria:**
  - A 4000×3000 JPEG uploads as a 512×512 JPEG under 200 KB (check the request in the network log).
  - The photo persists after a reload without pressing "Save profile".
  - Pressing "Save profile" afterwards doesn't clear it.
  - Remove clears it.
  - A PDF renamed to `.jpg` shows the inline error.
- **Verification:** scenarios 1, 2 and 6.

### Task 6: Report profile UI and moderator queue page

- **Depends on:** Task 3, Task 4
- **Files:** `webapp/src/pages/eventApp/ViewMemberProfile.js`, `webapp/src/pages/eventApp/ProfileReportsAdmin.js` (new), `webapp/src/pages/eventHome/EventHome.js`, `webapp/src/components/EventNav.js`, `webapp/src/services/eventApp/connection.service.js`, `webapp/public/locales/{en,fr}/translation.json`
- **Change:**
  - Add the Report profile panel to `ViewMemberProfile` (not on your own profile; the *Photo* option only when the profile has a photo).
  - Extend the service as in section 3 "Services".
  - Add the `ProfileReportsAdmin` page and route `/<event>/profileReportsAdmin` beside `discussionReportsAdmin` in `EventHome.js`.
  - Add the "Reported people" link under "Communications" in `EventNav.js`.
  - Cards show the category, reporter, time, reason, the reported (and current) photo, headline, an about excerpt and a profile link, with Remove photo (confirm) and Dismiss. The list reloads after each action.
- **Acceptance criteria:**
  - A guest can report another guest's photo or profile and sees the thanks message.
  - There is no report button on your own profile.
  - The comms officer or event admin sees the report with the right picture and can remove the photo or dismiss it.
  - A plain guest doesn't see the nav link, and the page shows "Access denied".
  - `pnpm run build` passes.
- **Verification:** scenarios 4, 5, 6 and 7.

## 7. Verification scenarios

**Extra data needed.** The seed has one confirmed guest (`claude-guest`), but reporting needs two attendees. Before scenario 3, make `claude-event-admin` a confirmed guest of `agent-test` by inserting an `invited_guest` row for them (role `Speaker`) through psql, and delete it afterwards. They then have both the moderator role and a directory entry. Scenarios 4–6 use them as the reported user and `claude-guest` as the reporter.

Test images: a large JPEG (≥ 3000 px wide, ≥ 3 MB, which can be generated with Python and Pillow on the runner or any canvas script) and a PDF renamed to `photo.jpg`.

| # | Role | Start at | Steps | Expected |
| --- | --- | --- | --- | --- |
| 1 | `guest` | `/agent-test/app/profile` | Click Upload photo and choose the large JPEG. Wait for the spinner. Reload. | The avatar preview shows the picture. The upload request's file is image/jpeg, 512×512 and under 200 KB. The picture persists after the reload. |
| 2 | `guest` | `/agent-test/app/profile` | After scenario 1, edit the headline and click Save profile. Reload. Click Remove and confirm. | The picture survives Save profile. After Remove, the preview shows initials and stays that way after a reload. Upload again before scenario 3. |
| 3 | `event-admin` (made a guest, see above) | `/agent-test/app/community` | Find Claude Guest. Open their profile. | Their picture shows on the card (48 px circle) and on the profile page (96 px). Claude EventAdmin's card shows initials. |
| 4 | `event-admin` | Upload a picture on `/agent-test/app/profile`, then log in as `guest` and open `/agent-test/app/profile/<event-admin id>` | Click Report profile, choose Photo, enter a reason and click Send report. Then open your own profile page. | The thanks message appears. Your own profile page has no Report profile button. |
| 5 | `event-admin` | Sidebar → Communications → Reported people | Look at the report from scenario 4. Click Remove photo and confirm. | The card shows Photo, Claude Guest as reporter, the reason and the reported picture. After removal the queue is empty. `/agent-test/app/community` shows initials for Claude EventAdmin. |
| 6 | `event-admin` | `/agent-test/app/profile` | Open My Profile after scenario 5. Upload a new picture. | The "A moderator removed your photo…" notice shows before the upload and disappears after it. |
| 7 | `guest` (no comms role) | `/agent-test/profileReportsAdmin` | Open the URL directly. Check the sidebar. | "Access denied". The sidebar has no "Reported people" link. |
| 8 | `guest` | `/agent-test/app/profile` | Upload `photo.jpg`, which is really a PDF. | The inline error "We couldn't process this image…" appears and the photo is unchanged. |

None of the scenarios depend on email, Google Docs or Stripe.

## 8. Migration and rollout

- **Two additive migrations:**
  - `member_profile.photo_removed_at` (nullable);
  - `connection_report`: `category` (server default `'person'`), `reported_photo_url`, `status` (server default `'open'`), `resolved_by_user_id` and `resolved_at`, plus the `(event_id, status)` index.
  - There are no backfills beyond the server defaults.
- **Before deploying, check prod for non-file-id photo URLs:** `SELECT count(*) FROM member_profile WHERE photo_url IS NOT NULL AND photo_url !~ '^[0-9a-f]{32}$';`. Any such rows still render, because `getImage` passes URLs through. The new validation only blocks *setting* new URLs, so no data change is needed, but it is worth knowing.
- **Under 1A, existing Scan & Connect reports will appear in each event's Reported people queue as open `person` reports** the first time moderators open it. Mention this in the release note.

## Noticed, not fixed

These are outside this issue's scope and are recorded here so they aren't lost:

- `_profile_to_dict` includes `email`, so `GET /api/v1/profile/list` sends every attendee's email address to every other attendee, including people who didn't connect with them.
- The hidden-profile stub (`ProfileViewAPI` ~L155) and `connections/api.py` still return `photo_url` for users who hid their profile.
- `POST`/`GET /api/v1/file` have no authentication.
