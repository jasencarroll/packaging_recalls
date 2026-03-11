"""Tests for the recall analytics endpoints."""


def test_kpis(client):
    """KPI endpoint returns expected fields with correct types."""
    response = client.get("/api/recalls/kpis")
    assert response.status_code == 200
    data = response.json()

    assert "total_recalls" in data
    assert "avg_cost_impact" in data
    assert "class_i_percent" in data
    assert "total_cost_impact" in data

    # 5 sample rows
    assert data["total_recalls"] == 5
    # Two Class I out of 5 => 40.0%
    assert data["class_i_percent"] == 40.0
    assert data["total_cost_impact"] == 500000 + 250000 + 100000 + 350000 + 800000


def test_classification(client):
    """Classification endpoint returns distribution and cost stats."""
    response = client.get("/api/recalls/classification")
    assert response.status_code == 200
    data = response.json()

    assert "distribution" in data
    assert "cost_by_class" in data

    # Check that all three classes appear in distribution
    classes = {item["class"] for item in data["distribution"]}
    assert classes == {"I", "II", "III"}

    # Sum of counts should equal total rows
    total = sum(item["count"] for item in data["distribution"])
    assert total == 5

    # cost_by_class entries should have box-plot fields
    for entry in data["cost_by_class"]:
        for key in ("class", "min", "q1", "median", "q3", "max"):
            assert key in entry


def test_defects(client):
    """Defects endpoint returns top defects with unpacked 'other' and risk levels."""
    response = client.get("/api/recalls/defects")
    assert response.status_code == 200
    data = response.json()

    assert "top_defects" in data
    assert "risk_levels" in data

    defect_names = [d["defect"] for d in data["top_defects"]]

    # The three "other" rows should be reclassified:
    #   D-003: "contamination from foreign substance" -> Contamination
    #   D-004: "Manufacturing process deviation" -> Manufacturing Defect
    #   D-005: "Stability data ... degradation" -> Stability/Degradation
    assert "Contamination" in defect_names
    assert "Manufacturing Defect" in defect_names
    assert "Stability/Degradation" in defect_names
    # "other" should no longer appear
    assert "other" not in defect_names


def test_timeline(client):
    """Timeline endpoint returns monthly and annual data."""
    response = client.get("/api/recalls/timeline")
    assert response.status_code == 200
    data = response.json()

    assert "monthly" in data
    assert "annual_by_class" in data
    assert len(data["monthly"]) > 0
    assert len(data["annual_by_class"]) > 0

    # Annual entries should have class breakdown keys
    for entry in data["annual_by_class"]:
        assert "year" in entry
        assert "class_i" in entry
        assert "class_ii" in entry
        assert "class_iii" in entry


def test_insights(client):
    """Insights endpoint returns complete BI summary."""
    response = client.get("/api/recalls/insights")
    assert response.status_code == 200
    data = response.json()

    expected_keys = {
        "total_recalls",
        "class_i_count",
        "avg_resolution_days",
        "most_common_defect",
        "total_cost_impact",
        "top_defects",
        "cost_by_defect",
        "labeling_count",
        "quality_count",
        "packaging_count",
    }
    assert expected_keys.issubset(data.keys())
    assert data["total_recalls"] == 5
    assert data["class_i_count"] == 2


def test_table_pagination(client):
    """Table endpoint returns paginated results."""
    response = client.get("/api/recalls/table?page=1&limit=2")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["pages"] == 3
    assert len(data["records"]) == 2


def test_table_filter_by_class(client):
    """Table endpoint filters by classification."""
    response = client.get("/api/recalls/table?class=I")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    for record in data["records"]:
        assert record["classification_clean"] == "I"


def test_table_filter_by_year(client):
    """Table endpoint filters by year."""
    response = client.get("/api/recalls/table?year=2023")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
