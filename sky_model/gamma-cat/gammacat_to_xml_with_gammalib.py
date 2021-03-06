"""
Convert Gamma-cat to model XML format.

Use Gammalib for now to make sure the XML format is OK.
"""
import logging
import gammalib
from gammapy.catalog import SourceCatalogGammaCat
from gammapy.catalog.gammacat import NoDataAvailableError

logging.basicConfig(level='INFO')
log = logging.getLogger(__name__)


def gammacat_source_to_gammalib_model(source):
    log.debug(source)
    if source.data['spec_type'] == 'none':
        # log.error('spec_type is none!')
        raise NoDataAvailableError('spec_type is none!')

    gammapy_spectral = source.spectral_model
    log.debug(gammapy_spectral)
    gammalib_spectral = gammacat_source_to_gammalib_model_spectral(gammapy_spectral)

    gammapy_spatial = source.spatial_model()
    log.debug(gammapy_spatial)
    gammalib_spatial = gammacat_source_to_gammalib_model_spatial(gammapy_spatial)

    gammalib_model = gammalib.GModelSky(gammalib_spatial, gammalib_spectral)
    gammalib_model.name(source.name)
    return gammalib_model


def gammacat_source_to_gammalib_model_spatial(gammapy_spatial):
    pos = gammalib.GSkyDir()

    kind = gammapy_spatial.__class__.__name__
    if kind == 'Delta2D':
        pos.lb_deg(gammapy_spatial.x_0.value, gammapy_spatial.y_0.value)
        gammalib_spatial = gammalib.GModelSpatialPointSource(pos)
    elif kind == 'Gaussian2D':
        # TODO: use gammalib.GModelSpatialEllipticalGauss
        pos.lb_deg(gammapy_spatial.x_mean.value, gammapy_spatial.y_mean.value)
        sigma = gammapy_spatial.x_stddev.value
        gammalib_spatial = gammalib.GModelSpatialRadialGauss(pos, sigma)
    elif kind == 'Shell2D':
        pos.lb_deg(gammapy_spatial.x_0.value, gammapy_spatial.y_0.value)
        radius = gammapy_spatial.r_in.value  # TODO: is this inner or outer radius?
        width = gammapy_spatial.width.value
        gammalib_spatial = gammalib.GModelSpatialRadialShell(pos, radius, width)
    else:
        raise NotImplementedError('Not supported: {}'.format(kind))

    return gammalib_spatial


def gammacat_source_to_gammalib_model_spectral(gammapy_spectral):
    kind = gammapy_spectral.__class__.__name__
    if kind == 'PowerLaw':
        prefactor = gammapy_spectral.parameters['amplitude'].quantity.to('cm-2 s-1 MeV-1').value
        index = - gammapy_spectral.parameters['index'].value
        pivot = gammalib.GEnergy(gammapy_spectral.parameters['reference'].quantity.to('MeV').value, 'MeV')
        gammalib_spectral = gammalib.GModelSpectralPlaw(prefactor, index, pivot)
        gammalib_spectral['Prefactor'].scale(1e-20)
        gammalib_spectral['Index'].scale(-1)
        gammalib_spectral['PivotEnergy'].scale(1e6)
    elif kind == 'PowerLaw2':
        flux = gammapy_spectral.parameters['amplitude'].quantity.to('cm-2 s-1').value
        index = - gammapy_spectral.parameters['index'].value
        emin = gammalib.GEnergy(gammapy_spectral.parameters['emin'].quantity.to('MeV').value, 'MeV')
        emax = gammalib.GEnergy(gammapy_spectral.parameters['emax'].quantity.to('MeV').value, 'MeV')
        gammalib_spectral = gammalib.GModelSpectralPlawPhotonFlux(flux, index, emin, emax)
        gammalib_spectral['PhotonFlux'].scale(1e-12)
        gammalib_spectral['Index'].scale(-1)
        gammalib_spectral['LowerLimit'].scale(1e6)
        gammalib_spectral['UpperLimit'].scale(1e6)
    elif kind == 'ExponentialCutoffPowerLaw':
        prefactor = gammapy_spectral.parameters['amplitude'].quantity.to('cm-2 s-1 MeV-1').value
        index = - gammapy_spectral.parameters['index'].value
        pivot = gammalib.GEnergy(gammapy_spectral.parameters['reference'].quantity.to('MeV').value, 'MeV')
        cutoff = gammalib.GEnergy(1. / gammapy_spectral.parameters['lambda_'].quantity.to('MeV-1').value, 'MeV')
        gammalib_spectral = gammalib.GModelSpectralExpPlaw(prefactor, index, pivot, cutoff)
        gammalib_spectral['Prefactor'].scale(1e-20)
        gammalib_spectral['Index'].scale(-1)
        gammalib_spectral['CutoffEnergy'].scale(1e6)
        gammalib_spectral['PivotEnergy'].scale(1e6)
    else:
        raise NotImplementedError('Not supported: {}'.format(kind))

    return gammalib_spectral


SOURCES_REMOVE = [
    # Sources in image_sources/ctadc_skymodel_gps_sources_images.xml
    'Westerlund 1',
    # 'Puppis A',  # Not a source in gamma-cat anyways
    'Vela X',
    'Vela Junior',
    'RX J1713.7-3946',
    'W28'  # a.k.a. "HESS J1801-233"
    'HESS J1800-240A',
    'HESS J1800-240B',

    # Sources in binaries/ctadc_skymodel_gps_sources_binaries.xml
    'LS 5039',
    'PSR B1259-63',
    'HESS J1832-093',
    'LS I +61 303',
    'HESS J0632+057',
    'HESS J1018-589 A',

    # Sources in pulsars list
    'Crab pulsar',

    # Sources we don't need for misc reasons
    'Galactic Centre ridge',  # not a source
    'Arc source',  # no good TeV measurement available
    'Geminga',  # no good TeV measurement available
]

SOURCES_KEEP = [
    'HESS J1943+213',
]


def skip_source(source):
    txt = '{} (gammacat source_id={})'.format(source.name, source.data['source_id'])
    if source.name in SOURCES_KEEP:
        return False

    if source.name in SOURCES_REMOVE:
        # log.debug('Skipped source that belongs to THE OTHERS: {}'.format(txt))
        return True

    if source.data['where'] == 'egal':
        # log.debug('Skipped EGAL source: {}'.format(txt))
        return True

    # log.debug('Keeping source: {}'.format(txt))
    return False


def gammacat_to_xml_gammalib():
    cat = SourceCatalogGammaCat()
    log.info('Number of sources in gamma-cat: {}'.format(len(cat.table)))

    models = gammalib.GModels()
    for source_idx in range(len(cat.table)):
        # For debugging
        # if source_idx > 1: break

        source = cat[source_idx]
        if skip_source(source):
            continue

        try:
            model = gammacat_source_to_gammalib_model(source)
            # import IPython; IPython.embed()
            # print(model)
            models.append(model)
        except NoDataAvailableError:
            txt = '{} (gammacat source_id={})'.format(source.name, source.data['source_id'])
            log.error('MISSING DATA: {}'.format(txt))
            pass

    log.info('Number of sources in XML file: {}'.format(len(models)))

    filename = 'ctadc_skymodel_gps_sources_gamma-cat2.xml'
    print('Writing {}'.format(filename))
    models.save(filename)


if __name__ == '__main__':
    gammacat_to_xml_gammalib()
