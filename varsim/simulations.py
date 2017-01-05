"""
Concrete Simulation Classes
"""
from __future__ import absolute_import, print_function
import abc
from future.utils import with_metaclass
import numpy as np
import pandas as pd
from lsst.sims.photUtils import BandpassDict
from lsst.sims.catUtils.supernovae import SNObject
from .baseSimulations import BaseSimulation

__all__ = ['BasicSimulation']


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
    def __init__(self, population, model, pointings, rng, maxObsHistID,
                 pointingColumnDict, pruneWithRadius):

        self.model = model
        self.population = population
        self._pointings = pointings
        self._rng = rng
        self.maxObsHistID = maxObsHistID
        self.pointingColumnDict = pointingColumnDict
        self.pruneWithRadius = pruneWithRadius
        self.bandPasses = BandpassDict.loadTotalBandpassesFromFiles()

    @property
    def randomState(self):
        return self._rng

    def  pair_method(self, obsHistID, objid, maxObsHistID):
        return objid * maxObsHistID + obsHistID


    @property
    def pointings(self):
        """
        `pd.DataFrame` of `OpSim` Pointings with at least minimal columns
        """
        return self._pointings

    def lc(self, idx, maxObsHistID=None):
        """

        Parameters
        ----------
        """
        if maxObsHistID is None:
            maxObsHistID = self.maxObsHistID

        # obtain the model parameters from the population
        paramDict = self.population.modelparams(idx)
        self.model.setModelParameters(**paramDict)
        myra = paramDict['ra']
        mydec = paramDict['dec']
        
        timeRange = (self.model.minMjd, self.model.maxMjd)
        if None not in timeRange:
            queryTime = 'expMJD < {1} and expMJD > {0}'.format(timeRange[0], timeRange[1])
            df = self.pointings.copy().query(queryTime)
        else:
            df = self.pointings.copy()
        if self.pruneWithRadius:
            raise ValueError('Not implemented')
        numObs = len(self.pointings)
        modelFlux = np.zeros(numObs)
        fluxerr = np.zeros(numObs)

        sn = SNObject(myra, mydec)


        for i, rowtuple in enumerate(df.iterrows()):
            row = rowtuple[1]
            # print(row['expMJD'], row['filter'], row['fiveSigmaDepth'])
            bp = self.bandPasses[row['filter']]
            modelFlux[i] = self.model.modelFlux(row['expMJD'],
                                                bandpassobj=bp)
            fluxerr[i] = sn.catsimBandFluxError(time=row['expMJD'],
                                                bandpassobject=bp,
                                                fluxinMaggies=modelFlux[i],
                                                m5=row['fiveSigmaDepth'])

        
        rng = self.randomState
        df.reset_index(inplace=True)
        df['objid'] = np.ones(numObs)*np.int(idx)
        df['objid'] = df.objid.astype(np.int)
        df['fluxerr'] = fluxerr
        deviations = rng.normal(size=len(df)) 
        df['deviations'] = deviations
        df['zp'] = 0.
        df['ModelFlux'] = modelFlux
        df['flux'] = df['ModelFlux'] + df['deviations'] * df['fluxerr']
        df['zpsys']= 'ab'
        df['pid'] = self.pair_method(df.objid, df.obsHistID, self.maxObsHistID)
        df['pid'] = df.pid.astype(np.int)
        lc = df[['pid', 'obsHistID', 'objid', 'expMJD', 'filter', 'ModelFlux', 'fieldID', 'flux',
                 'fluxerr', 'deviations', 'zp', 'zpsys']]
        lc.set_index('pid', inplace=True)
        return lc

    def write_lc(self, idx, output, method, clobber=False, key=None, append=False,
                 format='t'):
        lc = self.lc(idx)

        mode = 'a'
        if clobber:
            mode = 'w'
        if key is None:
            key='{}'.format(idx)
        if method == 'hdf':
            lc.to_hdf(output, mode=mode, key=key, append=append, format=format)
        elif method == 'csv':
            lc.to_csv(output, mode=mode)
        else:
            raise ValueError('method not implemented yet')

    def write_population(self, output, method, clobber=False, key=None, format='t',
                         get_dataframe=False):
        mode = 'a'
        if clobber:
            mode = 'w'
        if key is None:
            key='population'
        append=not(clobber)
        idxvalues = list(idx for idx in self.population.idxvalues)
        l = list(self.population.modelparams(idx) for idx in self.population.idxvalues) 
        df = pd.DataFrame(l, index=idxvalues)
        if method is None:
            pass
        elif method=='hdf':
            df.to_hdf(output, mode=mode, append=append, clobber=clobber, key=key, format='t')
        else:
            raise ValueError('method not implemented')
        if get_dataframe:
            return df

    def write_photometry(self, output, method, clobber=False, key=None, format='t'):

        for idx in self.population.idxvalues:
            print('writing {0}, {1}, {2}'.format(idx, clobber, key))
            append=not(clobber)
            self.write_lc(idx, output, method, clobber, key=key,
                          append=append, format=format)
            clobber = False

    def write_simulation(self, phot_output, pop_output, method, clobber=False,
                         key=None, format='t'):
        """
        """
        self.write_photometry(phot_output, method, clobber=clobber, key=key, format=format) 
        self.write_population(pop_output, method, clobber=clobber, key=key, format=format)


