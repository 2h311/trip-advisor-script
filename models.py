from dataclasses import dataclass


@dataclass
class HotelFields:
    name: str = "Name"
    reviews: str = "Reviews"
    website: str = "Website"
    phone: str = "Phone"
    images: str = "Images"
    location: str = "Location"

@dataclass
class Hotel:
    # this is for data validation
    name: str
    reviews: str
    website: str
    phone: str
    location: str
    images: list[bytes]
