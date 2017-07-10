"""
Concrete Simulation Classes
"""
from __future__ import absolute_import, print_function
from future.utils import with_metaclass
__all__ = ['BasicSimulation']
import abc
import numpy as np
import pandas as pd
from lsst.sims.photUtils import BandpassDict
from lsst.sims.catUtils.supernovae import SNObject
from .baseSimulations import BaseSimulation
from sndata import LightCurve


class BasicSimulation(BaseSimulation):
    """
    A class for simulated light curves of a variable source. This is
    appropriate for a very basic case where the ingredients are
    - a light curve model
    - a population model
    - pointings and their properties

    Parameters
    ----------
    population :
    model:
    pointings :  `pd.DataFrame` with minimal columns 
    rng : instance of `numpy.random.RandomState`
        random state used to assign scatter to light curves
    maxObsHistID : int, defaults to None
        if None, max(pointings.reset_index().obsHistiD)
    pointingcolumnDict : None
    pruneWithRadius : False
    """
    def __init__(self, rng, rng_obs, pointings, population, model,
                 bandpassDict='lsst', timeRange=(-70., 100.)):
        self._rng = rng
        self._rng_obs = rng_obs
        self._pointings = pointings
        self.model = model
        self.population = population
        self.timeRange = timeRange
        if bandpassDict == 'lsst':
            self.bandPasses = BandpassDict.loadTotalBandpassesFromFiles()
        else:
            self.bandPasses = bandpassDict
        
    @property
    def randomState(self):
        return self._rng
    @property
    def randomObs(self):
        return self._rng_obs
    
    @property
    def pointings(self):
        return self._pointings

    def pair_method(self, obsHistID, objID):
        return '_'.join(map(str, [obsHistID, objID]))

    def modelFlux(self, idx):
        params = self.population.modelParams(idx)
        self.model.setModelParameters(params)

        if self.timeRange is None:
            df = self.pointings.copy()
        else:
            l, h = self.timeRange
            df = self.pointings.query('expMJD < @h and expMJD > @l')

        modelFlux = np.zeros(len(df))
        for i, rowtuple in enumerate(df.iterrows()):
            row = rowtuple[1]
            bp = self.bandPasses[row['filter']]
            modelFlux[i] = self.model.modelFlux(row['expMJD'],
                                                bandpassobj=bp)
        return modelFlux

    def lc(self, idx,
           add_cols=('ModelFlux', 'deviations', 'objID', 'fieldID',
                     'obsHistID', 'fiveSigmaDepth')):
        
        if self.timeRange is None:
            df = self.pointings.copy()
        else:
            l, h = self.timeRange
            df = self.pointings.query('expMJD < @h and expMJD > @l')
        cols = list(LightCurve.requiredColumns.union(set(add_cols)))
        if len(df) == 0 :
            return pd.DataFrame(dict(a=[a]))
        params = self.population.modelParams(idx)
        self.model.setModelParameters(params)
        df['expID'] = list(self.pair_method(idx, obshistid) for obshistid in df.reset_index().obsHistID.values)
        fluxerr = np.zeros(len(df))
        modelFlux = np.zeros(len(df))
        sn = SNObject(30., 40.)
        for i, rowtuple in enumerate(df.iterrows()):
            row = rowtuple[1]
            bp = self.bandPasses[row['filter']]
            modelFlux[i] = self.model.modelFlux(row['expMJD'],
                                                bandpassobj=bp)
            fluxerr[i] = sn.catsimBandFluxError(time=row['expMJD'],
                                                bandpassobject=bp,
                                                fluxinMaggies=modelFlux[i],
                                                m5=row['fiveSigmaDepth'])

        rng = self.randomState
        df['fluxerr'] = fluxerr
        deviations = rng.normal(size=len(df)) 
        df['deviations'] = deviations
        df['zp'] = 0.
        df['ModelFlux'] = modelFlux
        df['flux'] = df['ModelFlux'] + df['deviations'] * df['fluxerr']
        df['zpsys'] = 'ab'
        df['objID'] = idx
        lc = df.reset_index().set_index('expID')

        lc = lc[cols]
        return LightCurve(lc, bandNameDict=dict((x, 'lsst' + x) for x in list('ugrizy') ))

    def write_population(self, fname, key='0'):
        self.population.paramsTable.to_hdf(fname, key=key)

    def write_lc(self, idx, fname, key='0', format='table',
                 append=True):
        lc = self.lc(idx)
        lc.lightCurve.to_hdf(fname, mode='a', key=key,
                             format=format, append=append)
                                
    def write_photometry(self, fname, method='hdf', key='0',
                         format='table', append=True):
	"""
	write tables of light curves in the simulation

	Parameters
	----------
	fname : string,  mandatory
	    output filename to which the photometry table 
	method : {'hdf'}
	format : {'table'}
	append : {True|False}
	    If False, clobber filename
	"""
        for idx in self.population.idxvalues:
            self.write_lc(idx, fname, key, format=format,
                          append=append)

    def write_simulation(self, population_fname, photometry_fname,
                         pop_key='0', phot_key='0'):
        self.write_population(population_fname, key=pop_key)
        self.write_photometry(photometry_fname, key=phot_key, format='table', append=True)
