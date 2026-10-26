"""Daily soil-water/crop model with an explicitly coupled yield endpoint.

This is a conservative three-layer bucket, not a Richards PDE solver. Calibration
and validation are separate from the legacy national neural checkpoint. Weather
and applied irrigation are explicit daily inputs; no hidden scenario multipliers
or year-as-predictor enter the yield pathway.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import math
from typing import Sequence


@dataclass(frozen=True)
class SoilLayer:
    thickness_mm: float
    field_capacity: float
    wilting_point: float
    saturation: float
    residual: float
    ksat_mm_day: float

    def __post_init__(self):
        if not (self.thickness_mm>0 and 0<=self.residual<self.wilting_point<self.field_capacity<self.saturation<=.8
                and self.ksat_mm_day>=0):
            raise ValueError('Invalid soil-layer hydraulic properties')


@dataclass(frozen=True)
class CropParameters:
    max_lai: float=6.
    gdd_peak: float=900.
    gdd_end: float=1900.
    max_kc: float=1.2
    rue_g_mj_par: float=3.
    harvest_index: float=.45

    def __post_init__(self):
        if not (0<self.max_lai<=12 and 100<self.gdd_peak<self.gdd_end and self.max_kc>0
                and self.rue_g_mj_par>0 and 0<self.harvest_index<1):
            raise ValueError('Invalid crop parameters')


def fao56_reference_et(tmin_c,tmax_c,tmean_c,rh_mean_pct,wind_m_s,solar_mj_m2,doy,
                       latitude_deg=35.186714,elevation_m=1170.,pressure_kpa=None):
    """FAO-56 daily grass reference ET, equations 6-8, 11-13, 21-25, 37-40.

    Mean RH is the available humidity input and is less exact than daily RH
    extrema. Wind is measured at 2 m in the Bushland station. Daily soil heat
    flux is taken as zero. Negative reference evaporation is returned as zero.
    Source: https://www.fao.org/4/X0490E/x0490e08.htm
    """
    values=[tmin_c,tmax_c,tmean_c,rh_mean_pct,wind_m_s,solar_mj_m2,doy]
    if not all(math.isfinite(float(v)) for v in values):raise ValueError('Missing meteorological input')
    if not (tmin_c<=tmax_c and 0<=rh_mean_pct<=100 and wind_m_s>=0 and solar_mj_m2>=0 and 1<=doy<=366):
        raise ValueError('Invalid meteorological input')
    es0=lambda t:.6108*math.exp(17.27*t/(t+237.3))
    es=(es0(tmin_c)+es0(tmax_c))/2
    ea=es*rh_mean_pct/100.
    slope=4098*es0(tmean_c)/(tmean_c+237.3)**2
    pressure=pressure_kpa if pressure_kpa is not None else 101.3*((293-.0065*elevation_m)/293)**5.26
    gamma=.000665*pressure
    phi=math.radians(latitude_deg)
    dr=1+.033*math.cos(2*math.pi*doy/365)
    declination=.409*math.sin(2*math.pi*doy/365-1.39)
    sunset=math.acos(max(-1.,min(1.,-math.tan(phi)*math.tan(declination))))
    ra=(24*60/math.pi)*.0820*dr*(sunset*math.sin(phi)*math.sin(declination)
                                               +math.cos(phi)*math.cos(declination)*math.sin(sunset))
    rso=(.75+2e-5*elevation_m)*ra
    cloud=1.35*min(1.,solar_mj_m2/max(rso,1e-8))-.35
    rnl=4.903e-9*((tmax_c+273.16)**4+(tmin_c+273.16)**4)/2*(.34-.14*math.sqrt(max(ea,0)))*max(.05,cloud)
    rn=.77*solar_mj_m2-rnl
    et=(.408*slope*rn+gamma*(900/(tmean_c+273))*wind_m_s*max(0.,es-ea))/(slope+gamma*(1+.34*wind_m_s))
    return max(0.,et)


def simulate_crop(days:Sequence[dict],soil:Sequence[SoilLayer],parameters:CropParameters,
                  planting_doy:int,initial_theta:Sequence[float]|None=None,irrigation_layer:int=0):
    """Return unrounded states and yield; each daily water step closes algebraically.

    Initial soil observations, when supplied, must precede planting. Callers own
    acquisition dates and train/test exclusions. No observations are assimilated
    after initialization. All output growth derives from simulated LAI, root-zone
    availability and supplied weather, so soil and management can affect yield.
    """
    if len(soil)!=3 or irrigation_layer not in [0,1,2]:raise ValueError('Expected three layers and a valid irrigation layer')
    theta=list(initial_theta) if initial_theta is not None else [s.field_capacity for s in soil]
    if len(theta)!=3 or any(not s.residual<=v<=s.saturation for s,v in zip(soil,theta)):
        raise ValueError('Initial soil water lies outside hydraulic bounds')
    water=[v*s.thickness_mm for v,s in zip(theta,soil)]
    gdd=0.;biomass=0.;records=[];previous_doy=None
    for daily in days:
        doy=int(daily['doy'])
        if previous_doy is not None and doy!=previous_doy+1:raise ValueError('Weather days must be consecutive')
        previous_doy=doy
        for name in ['rain_mm','irrigation_mm','dew_mm','et0_mm','solar_mj_m2','tmean_c','tmax_c']:
            if not math.isfinite(float(daily[name])):raise ValueError(f'Missing daily input {name}')
        if any(daily[name]<0 for name in ['rain_mm','irrigation_mm','dew_mm','et0_mm','solar_mj_m2']):
            raise ValueError('Negative daily forcing')
        before=sum(water)
        water[0]+=daily['rain_mm']+daily['dew_mm']
        water[irrigation_layer]+=daily['irrigation_mm']
        runoff=0.;deep=0.
        for j,s in enumerate(soil):
            overflow=max(0.,water[j]-s.saturation*s.thickness_mm)
            water[j]-=overflow
            if j<2:water[j+1]+=overflow
            else:deep+=overflow
        if doy>=planting_doy:
            gdd+=max(0.,min(30.,daily['tmean_c'])-10.)
            if gdd<=parameters.gdd_peak:
                lai=parameters.max_lai*math.sin(math.pi/2*min(1.,gdd/parameters.gdd_peak))**2
            else:
                lai=parameters.max_lai*max(0.,(parameters.gdd_end-gdd)/(parameters.gdd_end-parameters.gdd_peak))
        else:lai=0.
        cover=1-math.exp(-.6*lai)
        root_depth=min(sum(s.thickness_mm for s in soil),150.+1350.*min(1.,gdd/1100.))
        root_weights=[];top=0.
        for s in soil:
            root_weights.append(max(0.,min(root_depth,top+s.thickness_mm)-top));top+=s.thickness_mm
        root_total=sum(root_weights)
        root_weights=[x/root_total for x in root_weights]
        available=[max(0.,water[j]-s.wilting_point*s.thickness_mm) for j,s in enumerate(soil)]
        stress=sum(weight*min(1.,av/max(1e-8,.5*(s.field_capacity-s.wilting_point)*s.thickness_mm))
                   for weight,av,s in zip(root_weights,available,soil))
        demand=daily['et0_mm']*parameters.max_kc*cover
        transpiration=0.
        for j in range(3):
            uptake=min(available[j],demand*stress*root_weights[j])
            water[j]-=uptake;transpiration+=uptake
        evaporation=min(max(0.,water[0]-soil[0].residual*soil[0].thickness_mm),daily['et0_mm']*.4*(1-cover))
        water[0]-=evaporation
        for j,s in enumerate(soil):
            overflow=max(0.,water[j]-s.saturation*s.thickness_mm)
            drainage=overflow+min(s.ksat_mm_day,max(0.,water[j]-overflow-s.field_capacity*s.thickness_mm)*.8)
            water[j]-=drainage
            if j<2:water[j+1]+=drainage
            else:deep+=drainage
        thermal=max(0.,min(1.,(daily['tmean_c']-5.)/15.))*max(0.,1.-max(0.,daily['tmax_c']-35.)/15.)
        increment=parameters.rue_g_mj_par*.48*daily['solar_mj_m2']*cover*stress*thermal*10.
        biomass+=max(0.,increment)
        after=sum(water);et=transpiration+evaporation
        residual=after-before-(daily['rain_mm']+daily['irrigation_mm']+daily['dew_mm']-et-deep-runoff)
        records.append({'doy':doy,'gdd':gdd,'lai':lai,'biomass_kg_ha':biomass,'root_depth_mm':root_depth,
                        'water_availability_factor':stress,'et_mm':et,'transpiration_mm':transpiration,
                        'evaporation_mm':evaporation,'deep_drainage_mm':deep,'runoff_mm':runoff,
                        'storage_mm':after,'mass_residual_mm':residual,
                        **{f'theta_layer_{j+1}':water[j]/s.thickness_mm for j,s in enumerate(soil)}})
    return {'dry_grain_kg_ha':biomass*parameters.harvest_index,'biomass_kg_ha':biomass,
            'daily_records':records,'parameters':asdict(parameters),
            'model_scope':'calibrated state-coupled bucket prototype; not Richards PINN or operational twin'}
