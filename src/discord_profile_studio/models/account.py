from dataclasses import dataclass


@dataclass(slots=True)
class Account:
    label: str = ""
    application_id: str = ""
    user_id: str = ""
    username: str = ""
    token_ref: str = ""
