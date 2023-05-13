from dataclasses import dataclass


@dataclass
class HotelFields:
    name: str = "Name"
    reviews: str = "Reviews"
    website: str = "Website"
    phone: str = "Phone"
    images: str = "Images"


@dataclass
class Hotel:
    name: str
    reviews: str
    website: str
    phone: str
    images: list[bytes]
