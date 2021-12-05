#!/usr/bin/env python

from collections import deque

''' Container for the car. '''

class Car:
    """Definition of the Car class. Here Car can take several arguments
    during initialization.

    Args:
        starting_position (`float`): Starting position of the car
        starting_velocity (`float`): Starting velocity of the car
        braking_rate (`float`): Rate of retardation  (braking rate) of the car
        acceleration_rate (`float`): Rate of acceleration of the car
        max_velocity (`float`): Maximum velocity that the car can reach up to
        length (`float`): Length of a car
        stop_space (`float`): Space that the car must have between the car in the front before colliding
        save_dist (`float`): A safe distance the car wants to have with the car in front

    Attributes:
        position_history (`list`): History of all position that this car has traveled

    """
    def __init__(self, starting_position, starting_velocity, time_precision, braking_rate = 4.5, 
                acceleration_rate = 3, max_velocity = 26.8, length = 4,
                safe_dist = 100, can_speed_up_func = None, reaction_time = 0):
        self.position_history   = [starting_position]
        self.position           = starting_position
        self.velocity           = starting_velocity
        self.braking_rate       = braking_rate # m/s^2
        self.acceleration_rate  = acceleration_rate # m/s^2
        self.max_velocity       = max_velocity # m/s
        self.length             = length # meters
        self.safe_dist          = safe_dist # meters
        self.can_speed_up_func   = can_speed_up_func
        self.time_precision     = time_precision
        self.dist_history       = deque()
        self.reaction_time      = reaction_time
        self.is_reacting        = False
        self.potential_crashes_history = [0]

    def increase_speed(self, time_step):
        self.velocity += self.acceleration_rate * time_step
        if self.velocity > self.max_velocity:
            self.velocity = self.max_velocity

    def decrease_speed(self, time_step):
        self.velocity -= self.braking_rate * time_step
        if self.velocity < 0:
            self.velocity = 0

    def update_position(self, next_car):
        '''Get the new position of the car after a single time step of time_precision, based on the
        position of the car in front.

        Update the position history of the car.

        Args:
            position_of_next_car: distance to the next car

        Returns:
            The position of the car after the next time step

        '''

        position_of_next_car = next_car.position if next_car else 1e6
        
        # FIXME this is bad practice based on the assumption that every car
        # has the same length, and also it is hardcoding not object oriented.
        dist = position_of_next_car - self.position - self.length
        assert(len(self.dist_history) <= self.reaction_time / self.time_precision)
        self.dist_history.append(dist)
        if not self.is_reacting and len(self.dist_history) > self.reaction_time / self.time_precision:
            self.is_reacting = True

        # Notes down potential crashes, and automatically stops the car.
        self.potential_crashes_history.append(self.potential_crashes_history[-1])
        self.stopped = True
        if dist < 0:

            # This is an abrupt stop, otherwise it is just waiting
            if self.velocity != 0:
                self.potential_crashes_history[-1] += 1
                self.velocity = 0
                # FIXME this is bad practice based on the assumption that every car
                # has the same length, and also it is hardcoding not object oriented.
                self.position = position_of_next_car - self.length

            self.dist_history.popleft()
            

        elif self.is_reacting:

            # Reacts to the distance with a delay.
            dist = self.dist_history.popleft()
            speed_up = None
            if self.can_speed_up_func:
                speed_up = self.can_speed_up_func(dist, next_car)
            else:
                speed_up = dist > self.safe_dist

            if not speed_up:
                self.decrease_speed(time_step = self.time_precision)
            else:
                self.increase_speed(time_step = self.time_precision)

        self.position += self.velocity * self.time_precision
        self.position_history.append(self.position)
        return self.position

    def return_position_array(self):
        ''' Give history of the array for plotting.

        Returns:
            Return an array of positions for each time point in the simulation.
        '''
        return self.position_history

    def return_potential_crashes_history(self):
        return self.potential_crashes_history

class AutonomousVehicle(Car):
    def __init__(self, starting_position, starting_velocity, time_precision):

        def can_speed_up_func(dist, next_car):

            if not next_car:
                return True
            d0 = 3.048
            relative_velocity = self.velocity - next_car.velocity + \
                next_car.braking_rate * next_car.reaction_time
            following_distance = d0 + relative_velocity * self.reaction_time + \
                relative_velocity / 2 * (relative_velocity / self.braking_rate)

            if isinstance(next_car, AutonomousVehicle):
                return dist > following_distance * 0.4
            
            return dist > following_distance

        super().__init__(starting_position, starting_velocity, time_precision,
                    can_speed_up_func=can_speed_up_func, reaction_time = 0.2)

class HumanVehicle(Car):
    
    def __init__(self, starting_position, starting_velocity, time_precision):
        def can_speed_up_func(dist, next_car):
            if not next_car:
                return True

            d0 = 1.524
            relative_velocity = self.velocity - next_car.velocity + \
                next_car.braking_rate * next_car.reaction_time
            following_distance = d0 + relative_velocity * self.reaction_time + \
                relative_velocity / 2 * (relative_velocity / self.braking_rate)

            return dist > following_distance

        super().__init__(starting_position, starting_velocity, time_precision,
                    can_speed_up_func=can_speed_up_func, reaction_time = 0.5)
