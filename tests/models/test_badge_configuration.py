"""
Tests for badge configuration.
"""

import pytest
from pydantic import ValidationError
from pydantic_extra_types.color import Color

from evan.models.documents.badges import BadgesConfig, get_validated_badges_configuration


class TestBadgeConfig:
    """Test badge color configuration."""

    def test_default_badge_config(self):
        """Test that default configuration is valid."""
        config = BadgesConfig()

        assert config.default.as_hex() == "#2563eb"
        assert config.guest.as_hex() == "#059669"
        assert config.fee_colors == {}
        assert config.sort_by == "first_name"
        assert config.group_by == "none"

    def test_custom_badge_colors(self):
        """Test custom badge color configuration."""
        config = BadgesConfig(
            default=Color("#ff5733"),
            guest=Color("#33ff57"),
            fee_colors={"vip": Color("#ff0000"), "student": Color("#0000ff")},
        )

        assert config.default.original() == "#ff5733"
        assert config.guest.original() == "#33ff57"
        assert config.fee_colors["vip"].original() == "#ff0000"
        assert config.fee_colors["student"].original() == "#0000ff"

    def test_invalid_hex_color_format(self):
        """Test validation of invalid hex color formats."""
        with pytest.raises(ValidationError):
            BadgesConfig(default="not-a-color")

        with pytest.raises(ValidationError):
            BadgesConfig(default="#gggggg")

        with pytest.raises(ValidationError):
            BadgesConfig(default="#12345")

    def test_short_hex_color_expansion(self):
        """Test that 3-digit hex colors are accepted."""
        config = BadgesConfig(default="#f0a")
        # The color will keep its original format but be equivalent to the expanded version
        assert config.default.original() == "#f0a"
        # Check that it represents the right color by converting to RGB
        assert config.default.as_rgb_tuple() == (255, 0, 170)

    def test_fee_colors_validation(self):
        """Test validation of fee-specific colors."""
        config = BadgesConfig(fee_colors={"vip": Color("#ffcc00"), "student": Color("#0000ff")})
        assert config.fee_colors["vip"].original() == "#ffcc00"
        assert config.fee_colors["student"].original() == "#0000ff"

    def test_fee_colors_invalid_format(self):
        """Test that invalid fee colors are rejected."""
        with pytest.raises(ValidationError):
            BadgesConfig(fee_colors={"vip": "not-a-color"})

    def test_color_names_accepted(self):
        """Test that color names are accepted by Pydantic's Color type."""
        config = BadgesConfig(default=Color("red"), guest=Color("blue"))
        # Color names get converted to their named representation
        assert config.default.as_named() == "red"
        assert config.guest.as_named() == "blue"

    def test_filter_valid_fee_types(self):
        """Test filtering fee colors to only include valid fee types."""
        config = BadgesConfig(
            fee_colors={"vip": Color("#ffcc00"), "student": Color("#0000ff"), "invalid": Color("#ff0000")}
        )

        # Filter to only include valid fee types
        filtered_config = config.filter_valid_fee_types(["vip", "standard"])

        # Only valid fee types should remain
        assert len(filtered_config.fee_colors) == 1
        assert "vip" in filtered_config.fee_colors
        assert "student" not in filtered_config.fee_colors
        assert "invalid" not in filtered_config.fee_colors
        assert filtered_config.fee_colors["vip"].original() == "#ffcc00"

        # Other properties should remain unchanged
        assert filtered_config.default == config.default
        assert filtered_config.guest == config.guest

    def test_filter_valid_fee_types_empty(self):
        """Test filtering with no valid fee types."""
        config = BadgesConfig(fee_colors={"vip": Color("#ffcc00"), "student": Color("#0000ff")})

        filtered_config = config.filter_valid_fee_types([])

        assert len(filtered_config.fee_colors) == 0
        assert filtered_config.default == config.default
        assert filtered_config.guest == config.guest

    def test_get_validated_badges_configuration_with_filtering(self):
        """Test get_validated_badges_configuration with fee type filtering."""
        config_data = {
            "default": "#ff5733",
            "guest": "#33ff57",
            "fee_colors": {
                "student": "#2ecc71",
                "faculty": "#f39c12",
                "invalid_fee": "#9b59b6",
            },
        }

        # Test without filtering (should include all fee colors)
        result_unfiltered = get_validated_badges_configuration(config_data)
        assert "invalid_fee" in result_unfiltered["fee_colors"]
        assert len(result_unfiltered["fee_colors"]) == 3

        # Test with filtering (should exclude invalid fee types)
        valid_fee_types = ["student", "faculty"]
        result_filtered = get_validated_badges_configuration(config_data, valid_fee_types)

        assert result_filtered["default"] == "#ff5733"
        assert result_filtered["guest"] == "#33ff57"
        assert "student" in result_filtered["fee_colors"]
        assert "faculty" in result_filtered["fee_colors"]
        assert "invalid_fee" not in result_filtered["fee_colors"]
        assert len(result_filtered["fee_colors"]) == 2

    def test_custom_sort_by_configuration(self):
        """Test custom sort_by field configuration."""
        config = BadgesConfig(sort_by="last_name")
        assert config.sort_by == "last_name"

        config = BadgesConfig(sort_by="first_name")
        assert config.sort_by == "first_name"

    def test_invalid_sort_by_configuration(self):
        """Test that invalid sort_by values are rejected."""
        with pytest.raises(ValidationError):
            BadgesConfig(sort_by="invalid_sort")

    def test_custom_group_by_configuration(self):
        """Test custom group_by field configuration."""
        config = BadgesConfig(group_by="fee")
        assert config.group_by == "fee"

        config = BadgesConfig(group_by="none")
        assert config.group_by == "none"

    def test_invalid_group_by_configuration(self):
        """Test that invalid group_by values are rejected."""
        with pytest.raises(ValidationError):
            BadgesConfig(group_by="invalid_group")

    def test_get_validated_badges_configuration_with_sort_and_group(self):
        """Test get_validated_badges_configuration includes sort_by and group_by fields."""
        config_data = {"default": "#ff5733", "guest": "#33ff57", "sort_by": "last_name", "group_by": "fee"}

        result = get_validated_badges_configuration(config_data)

        assert result["default"] == "#ff5733"
        assert result["guest"] == "#33ff57"
        assert result["sort_by"] == "last_name"
        assert result["group_by"] == "fee"

    def test_get_validated_badges_configuration_with_defaults(self):
        """Test that default values are included when sort_by and group_by are not provided."""
        config_data = {
            "default": "#ff5733",
            "guest": "#33ff57",
        }

        result = get_validated_badges_configuration(config_data)

        assert result["sort_by"] == "first_name"  # default value
        assert result["group_by"] == "none"  # default value
