import os

from openai import OpenAI

from evan.models.events.sabaudia_registrations import SabaudiaRegistration


def generate_short_bio(registration: SabaudiaRegistration) -> str | None:
    """Giving a name, affiliation and a couple of links, generate a short bio."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    system_content = (
        "You are an assistant that likes facts and is helping a group of computer scientists "
        "that will be coming together in a brainstorming event. "
        "You are tasked with generating a short bio for a person. The bios you generate will help attendees "
        "get to know each other better."
    )

    prompt = f"""
Can you generate a short 6-line bio about {registration.name}? No need to mention DBLP or Google Scholar in this bio.
Just read the links and generate a bio based on the information you find there.

- Name: {registration.name}
- Affiliation: {registration.affiliation}
- Personal webiste: {registration.extra_data.get("url_website", "")}
- DBLP: {registration.extra_data.get("url_dblp", "")}
- Google Scholar: {registration.extra_data.get("url_google_scholar", "")}

Make sure you get the gender right!
Please return only the bio."""

    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    try:
        return chat_completion.choices[0].message.content
    except IndexError:
        return None
