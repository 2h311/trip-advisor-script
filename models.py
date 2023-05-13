from dataclasses import dataclass


class HotelFields:
    name: str = "Name"
    reviews: str = "Reviews"
    website: str = "Website"
    phone: str = "Phone"
    images: str = "Images"


class Hotel:
    name: str
    reviews: str
    website: str
    phone: str
    images: list[bytes]
