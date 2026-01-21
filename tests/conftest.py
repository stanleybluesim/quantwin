import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"jsonschema\.RefResolver is deprecated.*",
)
