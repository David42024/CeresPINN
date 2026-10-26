import math
import pytest
from backend.coupled_crop import SoilLayer,CropParameters,simulate_crop,fao56_reference_et


def layers():
    return [SoilLayer(d,.33,.18,.46,.05,k) for d,k in [(300,10),(300,2),(900,1)]]


def forcing(irrigation=0):
    return [dict(doy=i,tmean_c=25.,tmax_c=32.,solar_mj_m2=23.,et0_mm=6.,
                 rain_mm=500. if i==160 else 0.,irrigation_mm=irrigation,dew_mm=0.) for i in range(120,301)]


def test_conservation_and_soil_bounds_under_extreme_storm():
    soil=layers();r=simulate_crop(forcing(8),soil,CropParameters(),120,irrigation_layer=1)
    assert max(abs(d['mass_residual_mm']) for d in r['daily_records'])<1e-10
    for d in r['daily_records']:
        for j,s in enumerate(soil,1):assert s.residual-1e-12<=d[f'theta_layer_{j}']<=s.saturation+1e-12
        assert min(d['et_mm'],d['deep_drainage_mm'],d['biomass_kg_ha'])>=0


def test_water_and_growth_are_coupled_to_yield():
    dry=forcing();wet=forcing(8)
    for d in dry+wet:d['rain_mm']=0.
    a=simulate_crop(dry,layers(),CropParameters(),120)
    b=simulate_crop(wet,layers(),CropParameters(),120)
    assert b['dry_grain_kg_ha']>a['dry_grain_kg_ha']
    assert b['dry_grain_kg_ha']==b['biomass_kg_ha']*.45


def test_fao56_matches_published_cabinda_example():
    # FAO-56 ch4 Figure18 January monthly example; daily G=0 approximation.
    et=fao56_reference_et(22.8,29.6,26.2,81,78/86.4,15.7,15,latitude_deg=-5.33,elevation_m=20)
    assert et==pytest.approx(3.4,abs=.15)


def test_missing_days_and_inputs_are_rejected():
    days=forcing();days.pop(3)
    with pytest.raises(ValueError,match='consecutive'):simulate_crop(days,layers(),CropParameters(),120)
    days=forcing();days[0]['irrigation_mm']=math.nan
    with pytest.raises(ValueError,match='Missing'):simulate_crop(days,layers(),CropParameters(),120)
