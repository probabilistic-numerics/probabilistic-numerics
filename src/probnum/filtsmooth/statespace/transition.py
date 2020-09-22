"""Markov transition rules: continuous and discrete."""

import abc
from probnum.random_variables import RandomVariable

__all__ = ["Transition"]


class Transition(abc.ABC):
    """
    Interface for Markov transition rules in discrete or continuous time.
    """

    def __call__(self, arr_or_rv, start=None, stop=None, **kwargs):
        """Depending on the input, either call self.transition_realization() or self.transition_rv()"""
        if isinstance(arr_or_rv, RandomVariable):
            return self.transition_rv(rv=arr_or_rv, start=start, stop=stop, **kwargs)
        return self.transition_realization(real=arr_or_rv, start=start, stop=stop, **kwargs)


    @abc.abstractmethod
    def transition_realization(self, real, start, stop, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def transition_rv(self, rv, start, stop, **kwargs):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def dimension(self):
        raise NotImplementedError
