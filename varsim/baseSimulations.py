"""
- population
- modelflux
"""
from __future__ import absolute_import, print_function
import abc
from future.utils import with_metaclass


__all__ = ['BasePopulation', 'BaseModel', 'BaseSimulation']


class BasePopulation(with_metaclass(abc.ABCMeta, object)):
    """
    The base class used describing the population of objects of interest. This
    population is defined in terms of model parameters, and each object in the
    population is specified by a unique index idx. The model parameters for an
    object is obtained as a dictionary using the method modelparams, and the
    positions of all objects is obtained using he property positions. How these
    are obtained (eg. from a statistical model, or read from a database or list
    is an implementation question. Instances of this class are guaranteed to have
    the modelparams method, and a `positions` property
    """

    @abc.abstractmethod
    def modelparams(self, idx):
        """
        dictionary of model parameter names and parameters
        """
        pass

    @abc.abstractproperty
    def idxvalues(self):
        pass

    @abc.abstractproperty
    def hasPositions(self):
        """
        bool which is true if a sequence exists
        """
        pass

    @abc.abstractproperty
    def positions(self):
        """
        Designed to be an array of idx, ra, dec (degrees)
        """
        pass

class BaseModel(with_metaclass(abc.ABCMeta, object)):
    """
    class to represent a model
    """
    @abc.abstractmethod
    def setModelParameters(self, **params):
        pass

    @abc.abstractproperty
    def minMjd(self):
        pass

    @abc.abstractproperty
    def maxMjd(self):
        pass

    @abc.abstractmethod
    def modelFlux(self, mjd, bandpass, bandpassobj):
        """
        method to calculate the bandpass flux as a function of mjd, and either
        the bandpass or the bandpassobj
        """
        pass

class BaseSimulation(with_metaclass(abc.ABCMeta, object)):
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
