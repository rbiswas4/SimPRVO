"""
Concrete Simulation Classes
"""
from __future__ import absolute_import, print_function
import abc
from future.utils import with_metaclass
import numpy as np
from lsst.sims.photUtils import BandpassDict
from lsst.sims.catUtils.supernovae import SNObject
from .baseSimulations import BaseSimulation

__all__ = ['BasicSimulation']


class BasicSimulation(BaseSimulation):
    """
    A class defining all the inputs for a simulation
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
        self.rng = rng
        self.maxObsHistID = maxObsHistID
        self.pointingColumnDict = pointingColumnDict
        self.pruneWithRadius = pruneWithRadius
        self.bandPasses = BandpassDict.loadTotalBandpassesFromFiles()

    @property
    def randomState(self):
        return self._rng

    def  pair_method(obsHistID, objid, maxObsHistID):
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
            queryTime = 'expMJD < {1} and expMJD > {0}'.format(timeRange)
            df = self.pointings.copy().query(queryTime)
        else:
            df = self.pointings.copy()
        if self.pruneWithRadius:
            raise ValueError('Not implemented')
        numObs = len(pointings)
        modelFlux = np.zeros(numObs)
        fluxerr = np.zeros(numObs)

        sn = SNObject(ra, dec)
        for i, rowtuple in enumerate(df.iterrows()):
            row = rowtuple[1]
            # print(row['expMJD'], row['filter'], row['fiveSigmaDepth'])
            bp = self.bandPasses[row['filter']]
            modelFlux[i] = self.model.modelFlux(row['expMJD'],
                                                bandpassobject=bp)
            fluxerr[i] = sn.catsimBandFluxError(time=row['expMJD'],
                                                band=None,
                                                bandpassobject=bp,
                                                fluxinMaggies=modelFlux[i],
                                                m5=row['fiveSigmaDepth'])

        
        rng = self.randomState
        df = df.reset_index(inplace=True)
        df['objid'] = idx
        df['fluxerr'] = fluxerr
        deviations = rng.normal(size=len(df)) 
        df['deviations'] = deviations
        df['zp'] = 0.
        df['ModelFlux'] = modelFlux
        df['flux'] = df['ModelFlux'] + df['deviations'] * df['fluxerr']
        df['zpsys']= 'ab'
        df['pid'] = self.pair_method(df.objid, df.obsHistID, self.maxObsHistID)
        lc = df[['objid', 'expMJD', 'filter', 'ModelFlux', 'fieldID', 'flux',
                 'fluxerr', 'deviation', 'zp', 'zpsys', 'fieldID']]
        return lc
        





