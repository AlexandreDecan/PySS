from .model import Event
from .interpreter import Interpreter
import random


class Pause:
    """
    A convenience class to represent pause, ie. delay between sent events.

    :param duration: the duration of this pause
    """
    def __init__(self, duration: int):
        self._duration = duration

    @property
    def duration(self):
        """
        The duration of this pause
        """
        return self._duration

    def __repr__(self):
        return 'Pause({})'.format(self.duration)


class Story(list):
    """
    A story is a sequence of ``Event`` and ``Pause``.

    """
    def tell(self, interpreter: Interpreter, *args, **kwargs):
        """
        Tells the whole story to the interpreter.

        :param interpreter: an interpreter instance
        :param *args: additional positional arguments that are passed to ``interpreter.execute``.
        :param **kwargs: additional keywords arguments that are passed to ``interpreter.execute``.
        """
        for item in self:
            if isinstance(item, Event):
                interpreter.send(item)
            elif isinstance(item, Pause):
                interpreter.time += item.duration
            interpreter.execute(*args, **kwargs)

    def __repr__(self):
        return 'Story({})'.format(super().__repr__())


def random_stories(items, length: int=None):
    """
    A generator that returns random stories whose elements come from *items*.
    Parameter *items* can be any iterable containing events and/or pauses.

    :param items: Items to pick from
    :param length: Length of the story, or ``len(items)``
    :return: An infinite Story generator
    """
    while True:
        story = Story()
        for i in range(length):
            story.append(random.choice(items))  # Not random.sample, replacements needed
        yield story


def story_from_trace(trace: list) -> Story:
    """
    Return a story based on the given *trace*, a list of macro steps.
    The story is constructed as follows:
     - the story begins with a *started* event.
     - each time an event is consumed, a *consumed* event is sent.
       the consumed event is available in *event.event*.
     - each time a transition is processed, a *processed* event is sent.
       the source state name and the target state name (if any) are available respectively in
       *event.source* and *event.target*. The event processed by the transition is available in
       *event.event*.
     - each time a state is exited, an *exited* event is sent.
       the name of the state is available in ``event.state``.
     - each time a state is entered, an *entered* event is sent.
       the name of the state is available in ``event.state``.
     - the story ends with a *stopped* event.

    The story does NOT follow the interpretation order.
    *processed* events are sent before *exited* events.

    1. an event is possibly consumed
    2. For each transition:
        a. transition is processed
        b. states are exited
        c. states are entered
        d. statechart is stabilized (states are entered)

    :param trace: a list of ``micro step`` instances
    :return: A story
    """
    story = Story()
    story.append(Event('started'))
    for macrostep in trace:
        if macrostep.event:
            story.append(Event('consumed', {'event': macrostep.event}))
        for microstep in macrostep.steps:
            if microstep.transition:
                story.append(Event('processed', {'source': microstep.transition.from_state,
                                                 'target': microstep.transition.to_state,
                                                 'event': macrostep.event}))
            for state in microstep.exited_states:
                story.append(Event('exited', {'state': state}))
            for state in microstep.entered_states:
                story.append(Event('entered', {'state': state}))
    story.append(Event('stopped'))
    return story