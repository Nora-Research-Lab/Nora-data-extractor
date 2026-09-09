from app.services.dataset_registry import DatasetRegistry
from app.services.format_recommender import recommended_format, available_formats


def test_registry_loads_example_datasets():
    reg = DatasetRegistry("backend/data/datasets_registry.json")
    ids = {d.id for d in reg.list()}
    assert {"global_dem", "geology", "rivers", "mineral_occurrences"}.issubset(ids)


def test_recommended_format_by_kind():
    reg = DatasetRegistry("backend/data/datasets_registry.json")
    dem = reg.get("global_dem")
    geology = reg.get("geology")
    assert recommended_format(dem) == "COG"
    assert recommended_format(geology) == "GeoPackage"


def test_available_formats_marks_recommendation():
    reg = DatasetRegistry("backend/data/datasets_registry.json")
    opts = available_formats(reg.get("mineral_occurrences"))
    assert any(o["recommended"] for o in opts)
    assert any(o["format"] == "CSV" for o in opts)
