process INSTALL_PARSING_ENV {
    input:
    path db_location

    output:
    path "${db_location}", emit: parse_env_check

    script:
    """
    # Create a test to verify installation
    python -c "import pandas; import Bio; print('Parsing environment successfully installed')" > ${db_location}/parse_env_install_check.log
    """
}
