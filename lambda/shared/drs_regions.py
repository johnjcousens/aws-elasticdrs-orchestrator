"""
DRS Regions - Centralized list of AWS regions where DRS is available.

All Lambda functions should import DRS_REGIONS from this module to ensure
consistency and single-point updates when AWS adds new regions.

Source: https://docs.aws.amazon.com/drs/latest/userguide/supported-regions.html
"""

# All AWS regions where Elastic Disaster Recovery (DRS) is available
# Last updated: February 2026
DRS_REGIONS = [
    # US
    "us-east-1",       # N. Virginia
    "us-east-2",       # Ohio
    "us-west-1",       # N. California
    "us-west-2",       # Oregon
    # Europe
    "eu-west-1",       # Ireland
    "eu-west-2",       # London
    "eu-west-3",       # Paris
    "eu-central-1",    # Frankfurt
    "eu-central-2",    # Zurich
    "eu-north-1",      # Stockholm
    "eu-south-1",      # Milan
    "eu-south-2",      # Spain
    # Asia Pacific
    "ap-east-1",       # Hong Kong
    "ap-south-1",      # Mumbai
    "ap-south-2",      # Hyderabad
    "ap-southeast-1",  # Singapore
    "ap-southeast-2",  # Sydney
    "ap-southeast-3",  # Jakarta
    "ap-southeast-4",  # Melbourne
    "ap-northeast-1",  # Tokyo
    "ap-northeast-2",  # Seoul
    "ap-northeast-3",  # Osaka
    # Middle East
    "me-south-1",      # Bahrain
    "me-central-1",    # UAE
    # Africa
    "af-south-1",      # Cape Town
    # Israel
    "il-central-1",    # Tel Aviv
    # Americas
    "ca-central-1",    # Canada
    "sa-east-1",       # São Paulo
]

# GovCloud regions (require separate AWS accounts)
DRS_GOVCLOUD_REGIONS = [
    "us-gov-west-1",   # GovCloud (US-West)
    "us-gov-east-1",   # GovCloud (US-East)
]


def is_valid_drs_region(region: str) -> bool:
    """Check if a region supports AWS DRS."""
    return region in DRS_REGIONS or region in DRS_GOVCLOUD_REGIONS
