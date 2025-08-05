"""Custom badges extension for ARES 2025 event."""

from evan.models.registrations import Registration


def get_custom_info(registration: Registration, person_data: dict | None = None) -> list[dict]:
    """Return list of icons to display on the badge.

    For the 3 social events, 3 icons are used if the user has registered for them:
    - Social event 1: `square_reception.svg`
    - Social event 2: `square_boat.svg`
    - Social event 3: `square_dinner.svg`

    An extra camera icon is added to, that users can later strike through.
    - Camera icon: `camera.svg`

    :param registration: The registration to get custom info for.
    :param person_data: Optional data for accompanying person (contains selected_social_events list).
    :returns: List of icon dictionaries with 'filename' and optional styling info.
    """
    icons = []

    if person_data is not None:
        # Handle accompanying person - use their selected social events from extra_data
        selected_social_event_ids = person_data.get("selected_social_events", [])
        # Get all social events for this event
        social_events = registration.event.sessions.filter(is_social_event=True, id__in=selected_social_event_ids)
        session_titles = [session.title.lower() for session in social_events]
    else:
        # Handle main registration - use their registered sessions
        user_sessions = registration.sessions.filter(is_social_event=True)
        session_titles = [session.title.lower() for session in user_sessions]

    # Map session names to icons (these would need to match actual session names in the system)
    # You might need to adjust these based on the actual session names
    if any("reception" in title for title in session_titles):
        icons.append({"filename": "square_reception.svg"})

    if any("boat" in title for title in session_titles):
        icons.append({"filename": "square_boat.svg"})

    if any("dinner" in title for title in session_titles):
        icons.append({"filename": "square_dinner.svg"})

    # Always add camera icon for manual strikethrough
    icons.append({"filename": "camera.svg"})

    return icons
