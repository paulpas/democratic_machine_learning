"""Exception classes for democratic_machine_learning."""


class DemocraticMLException(Exception):
    """Base exception for democratic machine learning system."""


class DataLoadError(DemocraticMLException):
    """Error loading data from source."""


class ModelError(DemocraticMLException):
    """Error in model computation or prediction."""


class ValidationError(DemocraticMLException):
    """Error in data or policy validation."""


class PolicyConflictError(DemocraticMLException):
    """Error when policies conflict with each other."""


class WeightingError(DemocraticMLException):
    """Error in weighting system computation."""
