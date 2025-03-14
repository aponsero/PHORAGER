process INSTALL_PARSING_ENV {
    tag "Installing parsing environment"
    label "conda_install"

    input:
    path db_location
    val conda_only

    output:
    path "${db_location}", emit: parse_env_check

    script:
    """
    # Create a test to verify installation
    python -c "import pandas; import Bio; print('Parsing environment successfully installed')" > ${db_location}/parse_env_install_check.log
    """
}