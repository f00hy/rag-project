from app.main import main


def test_main_exists():
    """Test that main module can be imported."""
    assert callable(main)


def test_main_runs():
    """Test that main function executes without error."""
    main()
