// Include all subworkflows
include { install_genome } from './install_genome'
include { install_prophage } from './install_prophage'
include { install_annotation } from './install_annotation'

// Main installation workflow
workflow install {
    main:
        // Set default installation mode if not provided
        install_mode = params.install_mode ? params.install_mode : 'all'
        
        if (install_mode == 'all' || install_mode == 'genome') {
            install_genome()
        }
        
        if (install_mode == 'all' || install_mode == 'prophage') {
            install_prophage()
        }
        
        if (install_mode == 'all' || install_mode == 'annotation') {
            install_annotation()
        }
}
