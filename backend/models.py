
"""
RoomSync AI - Pydantic Models
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=4)


class UserLogin(BaseModel):
    name: str
    password: str


class AdminLogin(BaseModel):
    email: str
    password: str


class PreferencesInput(BaseModel):
    sleep: int = Field(..., ge=0, le=2)
    cleanliness: int = Field(..., ge=1, le=5)
    noise: int = Field(..., ge=1, le=5)
    smoking: int = Field(..., ge=0, le=2)
    guests: int = Field(..., ge=0, le=3)
    social: int = Field(..., ge=1, le=5)
    cooking: int = Field(..., ge=0, le=3)


class PersonalityInput(BaseModel):
    introvert_extrovert: int = Field(..., ge=1, le=5)
    conflict_style: int = Field(..., ge=0, le=2)
    routine_level: int = Field(..., ge=1, le=5)
    sharing_level: int = Field(..., ge=1, le=5)


class UserProfileInput(BaseModel):
    user_id: int
    age: int = Field(..., ge=16, le=100)
    profession: str = Field(..., max_length=100)
    gender: str = Field(..., max_length=20)
    preferences: PreferencesInput
    personality: PersonalityInput


class ScenarioResponseItem(BaseModel):
    scenario_id: str
    selected_option: int = Field(..., ge=0, le=10)


class ScenarioProfileInput(BaseModel):
    user_id: int
    age: int = Field(..., ge=16, le=100)
    profession: str = Field(..., max_length=100)
    gender: str = Field(..., max_length=20)
    responses: List[ScenarioResponseItem]


class CompatibilityRequest(BaseModel):
    user1_id: int
    user2_id: int


class ScenarioOptionInput(BaseModel):
    text: str
    emoji: Optional[str] = None
    traits: Dict[str, int]


class ScenarioCreateInput(BaseModel):
    slug: str
    title: str
    question: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    options: List[ScenarioOptionInput]


class WeightsUpdateInput(BaseModel):
    cleanliness: float = Field(..., ge=0.1, le=5.0)
    sleep: float = Field(..., ge=0.1, le=5.0)
    personality: float = Field(..., ge=0.1, le=5.0)
    trait: float = Field(..., ge=0.1, le=5.0)


class RoomLifestylePreferenceInput(BaseModel):
    cleanliness: int = Field(..., ge=1, le=5)
    sleep: int = Field(..., ge=0, le=2)
    noise: int = Field(..., ge=1, le=5)
    social: int = Field(..., ge=1, le=5)
    smoking: int = Field(..., ge=0, le=2)
    guests: int = Field(default=1, ge=0, le=3)
    cooking: int = Field(default=1, ge=0, le=3)


class RoomPostCreateInput(BaseModel):
    user_id: int
    title: str = Field(..., max_length=150)
    description: str = Field(..., max_length=2000)
    rent: float = Field(..., gt=0)
    location: str = Field(..., max_length=255)
    gender_preference: Optional[str] = Field(default="Any", max_length=50)
    lifestyle_preference: RoomLifestylePreferenceInput
    personality_preference: Optional[PersonalityInput] = None
    image_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)


class RoommateRequestInput(BaseModel):
    requester_user_id: int
    message: Optional[str] = Field(default="Interested in this room post.", max_length=255)
