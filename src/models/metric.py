from pydantic import BaseModel, Field


class MagnitudeDistribution(BaseModel):
    micro: int = 0
    minor: int = 0
    light: int = 0
    moderate: int = 0
    strong: int = 0


class MetricOut(BaseModel):
    window: str
    earthquake_count: int
    avg_magnitude: float
    max_magnitude: float
    magnitude_distribution: MagnitudeDistribution = Field(default_factory=MagnitudeDistribution)
