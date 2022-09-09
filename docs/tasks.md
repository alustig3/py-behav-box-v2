# Programming tasks in pybehave

## Overview

Behavioral tasks in pybehave are implemented as state machines, the basic elements of which are states and components. To create
a task, the user develops a *task definition file* written in Python in the *py-behav-box-v2/source/Tasks* folder. Task 
definitions are hardware-agnostic and solely program for task logic and timing, interacting with hardware or implementation specific
[Sources]() and [Events](). Pybehave tasks are objects that are all subclasses of the base `Task` class with the ability to 
override functionality as necessary.

## States

At any time the task will be in one of a set of states defined by the user. States are represented as an [enum](https://docs.python.org/3/library/enum.html) 
with each state having a name and a corresponding ID:

    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2

## Components

[Components](components.md) are abstractions that allow the task to communicate with external objects like levers, lights, or even network events
without details of the specific implementation. Every task must declare the names, numbers, and types of each Component by overriding
the `get_components` method. An example for a typical operant task is shown below:

    @staticmethod
    def get_components():
        return {
            'nose_pokes': [BinaryInput, BinaryInput, BinaryInput],
            'nose_poke_lights': [Toggle, Toggle, Toggle],
            'food': [FoodDispenser],
            'house_light': [Toggle]
        }

This task utilizes infrared nose poke sensors, LED and incandescent lights, and a food dispenser that are abstracted as BinaryInputs,
Toggles, and a TimedToggle.

Components will be instantiated as attributes of the Task either as single objects or lists depending on the structure of each
entry in the `get_components` method. The specific [Source]() for these components can be specified using local [Address Files]().
The indicated class type for each object only prescribes a super class; subclasses of the indicated type are also valid.
Components can be accessed in task code as attributes of the task: `self.COMPONENT_NAME`.

## Constants

Many tasks have constants that control task progression without altering underlying logic. For example, there could be a need
for multiple sequences of trial types, different timing as training progresses, or variable completion criteria. Rather than having
to create new task definitions for changes of this sort, they can instead be explicitly defined using the `get_constants` method
and later modified using [Protocols](). An example for the same operant task is shown below:

    def get_constants(self):
        return {
            'max_duration': 90,
            'inter_trial_interval': 7,
            'response_duration': 3,
            'n_random_start': 10,
            'n_random_end': 5,
            'rule_sequence': [0, 1, 0, 2, 0, 1, 0, 2],
            'correct_to_switch': 5,
            'light_sequence': random.sample([True for _ in range(27)] + [False for _ in range(28)], 55)
        }

This task has constants for controlling timing like task or trial durations as well as a default rule sequence. Additionally,
constants need not necessarily be identical every time the task is run but could be generated according to constant rules like the pseudo random `light_sequence`
in this example. Constants can be accessed in task code as attributes of the task: `self.CONSTANT_NAME`.

## Variables

Variables are used to track task features like trial counts, reward counts, or a block number. The default values for variables
should be configured using the `get_variables` method:

    def get_variables(self):
        return {
            'cur_trial': 0,
            'cur_rule': 0,
            'cur_block': 0
        }

It is likely you will see warnings about instance attribute definitions outside `__init__` when using variables; these can be
safely ignored. Constant attributes will already be available when `get_variables` is called and can be used in the method.
Variables can be accessed in task code as attributes of the task: `self.VARIABLE_NAME`.

### Initial State

Every task must define the initial state it will be in by overriding the `init_state` method. Variables and constants are accessible 
as attributes when this method is called should the initial state depend on them. An example override is shown below:

    def init_state(self):
        return self.States.INITIATION

## Changing states

The current state can be changed using the `change_state` method. `change_state` will implicitly log *StateChangeEvents* that
can be handled by external *EventLoggers*. Additional metadata can also be passed to `change_state` if necessary for event
purposes. An example of using `change_state` with metadata is shown below:

    self.change_state(self.States.RESPONSE, {"correct": True})

## Time dependent behavior

Time dependent behavior can be implemented by calling methods from the base `Task` class. All timing should use these methods
to ensure no issues arise due to pausing and resuming the task. The `time_elapsed` method can be used to query the amount
of time that has passed since the task started. The `time_in_state` method can be used to query the amount of time since the
last state change. Both methods will not include any time spent paused.

## Events

Events are used to communicate information from the task to [*EventLogger*]() classes that can complete a variety of roles like
saving task data, communicating with external programs, or sending digital codes for synchronization. Every task has an `events`
attribute that can be appended to and later parsed by various *EventLoggers*.

### Inputs

Inputs are used to communicate event information from Components that provide input to the task.
Like states, inputs are also represented as an enum with each input having a name and a corresponding ID. The example below 
shows how to structure inputs for three possible components with distinction between when the component is entered versus exited:

    class Inputs(Enum):
        FRONT_ENTERED = 2
        FRONT_EXIT = 3
        MIDDLE_ENTERED = 4
        MIDDLE_EXIT = 5
        REAR_ENTERED = 6
        REAR_EXIT = 7

An example of how to log such an Input event is shown below:

    self.events.append(InputEvent(self, self.Inputs.FRONT_ENTERED))

## Task lifetime

Every task begins with an initialization via `init` that will contain any code that should be run when the task is first loaded
but before starting. When the task is started the `start` method is called. Unless stopped using `stop`
or paused using `pause`, the task will continuously call the `main_loop` method until it reaches the completion criteria defined
by the method `is_complete`. All of these methods can be overridden by the task to control behavior over its lifetime.


### start, stop, resume, and pause

Code can be executed when the task starts or stops to ensure certain hardware is enabled/disabled or initialize features 
of the task. Four methods exist for this purpose: `start`, `stop`, `resume`, and `pause`. There is no requirement to override
these methods unless particular behavior is required at these moments. No additional code needs to be written to handle task 
timing when using the `resume`, and `pause` methods.

### main_loop

The `main_loop` method will be repeatedly called while the task is still active and is responsible for implementing all task logic.
`main_loop` is typically composed of a series of `if` statements corresponding to each task state:

    def main_loop(self):
        food_lever = self.food_lever.check()
        pressed = False
        if food_lever == BinaryInput.ENTERED:
            pressed = True
        if self.state == self.States.REWARD_AVAILABLE:
            if pressed:
                self.food.dispense()
                self.change_state(self.States.REWARD_UNAVAILABLE)
        elif self.state == self.States.REWARD_UNAVAILABLE:
            if self.time_in_state() > self.lockout:
                self.change_state(self.States.REWARD_AVAILABLE)

The above example shows how `main_loop` could be used for a bar press-reward task with a timeout period.

### is_complete

The `is_complete` method returns a boolean indicating if the task has finished. This method must be overridden
and will be called alongside `main_loop` to determine if the task is complete.

    def is_complete(self):
        return self.time_elapsed() > self.duration * 60.0

## Task GUIs

All pybehave tasks have GUIs written in [pygame](https://www.pygame.org/) that can be used to monitor task components and variables or control 
task features if necessary. Further details on GUI development are available on the GUI [page]().

# Class reference

The methods detailed below are contained in the `Task` class.

## Configuration methods

### get_components

    get_components()

Returns a dictionary describing all the components used by the task. Each component name is linked to a list of Component types.

*Example override:*

    @staticmethod
    def get_components(): # Define components for a motorized bar press task
        return {
            'food_lever': [BinaryInput],
            'cage_light': [Toggle],
            'food': [FoodDispenser],
            'fan': [Toggle],
            'lever_out': [ByteOutput],
            'food_light': [Toggle],
            'cam': [Video]
        }

### get_constants

    get_constants()

Returns a dictionary describing all the constants used by the task. Constants can be of any type and modified using [Protocols]().

*Example override:*

    def get_constants(self):
        return {
            'duration': 40,             # Task duration
            'reward_lockout_min': 25,   # Minimum time to lockout reward
            'reward_lockout_max': 35    # Maximum time to lockout reward
        }

### get_variables

    get_variables()

Returns a dictionary describing all the variables used by the task. Variables can be of any type.

*Example override:*

    def get_variables(self):
        return {
            'lockout': 0,   # Time to lockout reward for
            'presses': 0    # Number of times the bar has been pressed
        }

## Lifetime methods

### init

    init()

### start

    start()

### stop

    stop()

### resume

    resume()

### pause

    pause()

### is_complete

    is_complete()

## Control and timing methods

### init_state

    init_state(state)

### change_state

    change_state(state, metadata=None)

### time_elapsed

    time_elapsed()

### time_in_state

    time_in_state()