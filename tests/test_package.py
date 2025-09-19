from lf2x import DEFAULT_OUTPUT_DIR, LF2XSettings, __version__


def test_public_api_exports() -> None:
    assert isinstance(__version__, str)
    assert DEFAULT_OUTPUT_DIR.name == "dist"
    settings = LF2XSettings()
    assert settings.output_dir == DEFAULT_OUTPUT_DIR
    assert settings.config_file is None
