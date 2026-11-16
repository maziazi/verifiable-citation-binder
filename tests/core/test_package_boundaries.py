def test_tier_packages_are_importable() -> None:
    import vcb.adjudicate
    import vcb.core
    import vcb.surface

    assert vcb.core is not None
    assert vcb.adjudicate is not None
    assert vcb.surface is not None
