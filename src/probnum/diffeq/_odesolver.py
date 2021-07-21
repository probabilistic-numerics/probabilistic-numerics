"""ODE solver interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

import numpy as np

from probnum import randvars
from probnum.diffeq import events


class ODESolver(ABC):
    """Interface for ODE solvers in ProbNum."""

    @dataclass
    class State:
        """ODE solver states."""

        t: float
        rv: randvars.RandomVariable
        error_estimate: Optional[np.ndarray] = None

        # The reference state is used for relative error estimation
        reference_state: Optional[np.ndarray] = None

    def __init__(
        self,
        ivp,
        order,
        event_handler: Optional[
            Union[events.EventHandler, List[events.EventHandler]]
        ] = None,
    ):
        self.ivp = ivp
        self.order = order  # e.g.: RK45 has order=5, IBM(q) has order=q
        self.num_steps = 0

        # If the event handlers are a list, the final entry (i.e. bottom entry if thought of as a stack of entries)
        # is the outer-most event handler.
        full_step_implementation = self._perform_full_step
        if event_handler is not None:
            if isinstance(event_handler, events.EventHandler):
                event_handler = [event_handler]

            for handle in event_handler:
                full_step_implementation = handle(full_step_implementation)
        self.perform_full_step = full_step_implementation

    def solve(self, steprule):
        """Solve an IVP.

        Parameters
        ----------
        steprule : :class:`StepRule`
            Step-size selection rule, e.g. constant steps or adaptive steps.
        """
        self.steprule = steprule
        times, rvs = [], []
        for state in self.solution_generator(steprule):
            times.append(state.t)
            rvs.append(state.rv)

        odesol = self.rvlist_to_odesol(times=times, rvs=rvs)
        return self.postprocess(odesol)

    def solution_generator(self, steprule):
        """Generate ODE solver steps."""

        state = self.initialize()
        yield state

        dt = steprule.firststep
        while state.t < self.ivp.tmax:
            state, dt = self.perform_full_step(state, dt, steprule)
            self.num_steps += 1
            yield state

    # "private" because it may be wrapped through an event handler in the constructor.
    def _perform_full_step(self, state, initial_dt, steprule):
        """Perform a full ODE solver step.

        This includes the acceptance/rejection decision as governed by error estimation
        and steprule.
        """
        dt = initial_dt
        step_is_sufficiently_small = False
        while not step_is_sufficiently_small:
            proposed_state = self.attempt_step(state, dt)
            internal_norm = steprule.errorest_to_norm(
                errorest=proposed_state.error_estimate,
                reference_state=proposed_state.reference_state,
            )
            step_is_sufficiently_small = steprule.is_accepted(internal_norm)
            suggested_dt = steprule.suggest(
                dt, internal_norm, localconvrate=self.order + 1
            )
            if step_is_sufficiently_small:
                dt = min(suggested_dt, self.ivp.tmax - proposed_state.t)
            else:
                dt = min(suggested_dt, self.ivp.tmax - state.t)
        self.method_callback(state)
        return proposed_state, dt

    @abstractmethod
    def initialize(self):
        """Returns t0 and y0 (for the solver, which might be different to ivp.y0)"""
        raise NotImplementedError

    @abstractmethod
    def attempt_step(self, state, dt):
        """Compute a step from the current state to the next state with increment dt.

        This does not include the acceptance/rejection decision from the step-size
        selection. Therefore, if dt turns out to be too large, the result of
        attempt_step() will be discarded.
        """
        raise NotImplementedError

    @abstractmethod
    def rvlist_to_odesol(self, times, rvs):
        """Create an ODESolution object."""
        raise NotImplementedError

    def postprocess(self, odesol):
        """Process the ODESolution object before returning."""
        return odesol

    def method_callback(self, state):
        """Optional callback.

        Can be overwritten. Do this as soon as it is clear that the
        current guess is accepted, but before storing it. No return. For
        example: tune hyperparameters (sigma).
        """
        pass
