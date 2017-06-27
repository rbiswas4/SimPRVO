"""
- population
- modelflux
"""
from __future__ import absolute_import, print_function
__all__ = ['BaseSimulation']

import abc
from future.utils import with_metaclass



class BaseSimulation(with_metaclass(abc.ABCMeta, object)):
    """
    A class defining all the methods and attributes to any simulation

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
    @abc.abstractproperty
    def randomState(self):
        """
        """
        pass


    @abc.abstractmethod
    def  pair_method(self, obsHistID, objid, maxObsHistID):
        pass


    @abc.abstractproperty
    def pointings(self):
        """
        `pd.DataFrame` of `OpSim` Pointings with at least minimal columns
        of mjd, band, 
        """
        pass

    @abc.abstractproperty
    def lc(self, idx, maxObsHistID=None):
        """

        Parameters
        ----------
        """
        pass

    @abc.abstractmethod
    def write_lc(self, idx, output, method, key=None):
        pass

    @abc.abstractmethod
    def write_photometry(self, output, method, key=None):
        pass

    @abc.abstractmethod
    def write_simulation(self, phot_output, pop_output, method, key=None):
        pass
    
    @abc.abstractmethod
    def write_population(self, output, method, key=None):
        pass
