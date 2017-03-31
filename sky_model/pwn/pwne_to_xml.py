"""
Convert PWN to XML format.
"""
import numpy as np
import astropy.units as u
from astropy.table import Table
from gammapy.utils.coordinates import galactic as compute_galactic_coordinates

SOURCE_LIBRARY_TEMPLATE = """\
<?xml version="1.0" standalone="no"?>

<source_library title="CTA 1DC simulated supernova remnants">

{xml_sources}

</source_library>
"""

SOURCE_TEMPLATE = """
 <source name="{source_name}" type="ExtendedSource">
{xml_spectral}
{xml_spatial}
 </source>
"""

SPATIAL_TEMPLATE = """\
    <spatialModel type="RadialGaussian">
        <parameter name="GLON" scale="1.0" value="{glon:.5f}" min="-360" max="360" free="0"/>
        <parameter name="GLAT" scale="1.0" value="{glat:.5f}" min="-90" max="90" free="0"/>
        <parameter name="Sigma" scale="1.0" value="{sigma:.5f}" min="0.01" max="10"  free="1"/>
    </spatialModel>"""


SPECTRUM_TEMPLATE = """\
    <spectrum type="LogParabola">
        <parameter name="Prefactor" scale="1e-20" value="{norm:.3f}"  min="1e-07" max="1000.0" free="1"/>
        <parameter name="Index"     scale="-1"    value="{index:.3f}"  min="0.0"   max="+5.0"   free="1"/>
        <parameter name="Curvature" scale="-1"    value="{curvature:.3f}"  min="-5.0"   max="+5.0"   free="1"/>
        <parameter name="PivotEnergy" scale="1e6"   value="{energy:.1f}" min="0.01"  max="1000.0" free="0"/>
      </spectrum>


"""


# def make_table_spectrum_xml(sed_energy, sed_dnde):
#     xml_spectrum_nodes = ''
#     for energy, dnde in zip(sed_energy, sed_dnde):
#         xml_spectrum_nodes += SPECTRUM_NODE_TEMPLATE.format(
#             energy=energy,
#             dnde=dnde,
#         )
#
#     return SPECTRUM_TEMPLATE.format(xml_spectrum_nodes=xml_spectrum_nodes)


def make_pwn_xml(table):
    remove_or_not0 = 0
    remove_or_not = 0
    remove_or_not_2 = 0
    remove_or_not_3 = 0
    remove_or_not_4 = 0
    remove_or_not_5 = 0
    xml_sources = ''

    #for row in table[:2]:
    for row in table:
        if (row['int_flux_above_1TeV_cu']>10):
            if (remove_or_not0 < 20):
                remove_or_not0+=1
                print('crab: ', row['int_flux_above_1TeV_cu'])
            continue;


        if (row['int_flux_above_1TeV_cu'] > 8 and row['int_flux_above_1TeV_cu'] < 10):
            if (remove_or_not < 3):
                remove_or_not+=1
                print('8-10    ',remove_or_not, row.index, row['int_flux_above_1TeV_cu'])
                continue;

        if (row['int_flux_above_1TeV_cu'] < 8 and row['int_flux_above_1TeV_cu'] > 6):
            if (remove_or_not_2 < 3):
                remove_or_not_2+=1
                print('6-8: ',remove_or_not_2, row.index, row['int_flux_above_1TeV_cu'])
                continue;


        if (row['int_flux_above_1TeV_cu'] < 6 and row['int_flux_above_1TeV_cu'] > 4):
            if (remove_or_not_3 < 1):
                remove_or_not_3 += 1
                print('4-6: ',remove_or_not_3, row.index, row['int_flux_above_1TeV_cu'])
                continue;

        if (row['int_flux_above_1TeV_cu'] < 4 and row['int_flux_above_1TeV_cu'] > 2):
            if (remove_or_not_4 < 6):
                remove_or_not_4 += 1
                print('2-4: ',remove_or_not_4, row.index, row['int_flux_above_1TeV_cu'])
                continue;
        if (row['int_flux_above_1TeV_cu'] < 2 and row['int_flux_above_1TeV_cu'] > 1):
            if (remove_or_not_5 < 9):
                remove_or_not_5 += 1
                print('1-2: ',remove_or_not_5, row.index, row['int_flux_above_1TeV_cu'])
                continue;



        xml_spectral = SPECTRUM_TEMPLATE.format(
            norm=row['spec_norm']/1e-20,
            index=row['spec_alpha'],
            curvature = row['spec_beta'],
            energy = 1.0
            )

        # Arbitrary assumption on width of the  shell
        # TODO: ask Pierre what we should put!
        # Also check if radius is inner or outer!
        #width_fraction = 0
        #radius = u.Quantity(row['size'], 'arcmin').to('deg')
        #width = width_fraction * radius

        xml_spatial = SPATIAL_TEMPLATE.format(
            glon=row['GLON'],
            glat=row['GLAT'],
            sigma=row['sigma']
            )

       # import IPython; IPython.embed();
        source_name='pwn_{}'.format(row.index)
        #print(source_name)

        xml_source = SOURCE_TEMPLATE.format(
             source_name=source_name,
             xml_spectral=xml_spectral,
             xml_spatial=xml_spatial
             )

        xml_sources += xml_source
        #print(xml_sources)

    xml = SOURCE_LIBRARY_TEMPLATE.format(xml_sources=xml_sources)

    #print(xml)
    filename = 'ctadc_skymodel_gps_sources_pwn.xml'
    print('Writing {}'.format(filename))
    with open(filename, 'w') as fh:
         fh.write(xml)


# def read__data():
#     filename = 'ctadc_skymodel_gps_sources_.esv'
#     print('Reading {}'.format(filename))
#     table = Table.read(filename, format='ascii.ecsv')
#
#     distance, glon, glat = compute_galactic_coordinates(
#         x=table['POS_X'].quantity,
#         y=table['POS_Y'].quantity,
#         z=table['POS_Z'].quantity,
#     )
#     table['distance'] = distance
#     table['glat'] = glat
#     table['glon'] = glon
#
#     energy_array = np.array(table.meta['energy_array'])
#     sed_energy = np.tile(energy_array, reps=(len(table), 1))
#     table['sed_energy'] = sed_energy
#
#     # Copy over fluxes into array column
#     sed_dnde = np.empty_like(sed_energy)
#     for col_idx in range(50):
#         sed_dnde[:, col_idx] = table.columns[9 + col_idx]
#
#     table['sed_dnde'] = sed_dnde
#
#     return table


if __name__ == '__main__':
    table = Table.read('ctadc_skymodel_gps_sources_pwn.ecsv', format='ascii.ecsv')
    table.pprint()
    make_pwn_xml(table)
