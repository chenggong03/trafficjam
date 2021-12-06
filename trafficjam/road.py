#!/usr/bin/env python
from car import Car
import numpy as np
from car import AutonomousVehicle

'''  '''

class Road:
    ''' Handler for the running of the code. '''

    def __init__(self):
        self.car_list = []
        self.position_update_count = None
        self.car_getting_merged_in_front = None
        self.time_precision = 0.2 # cars and reactions are updated every this second amount.
        self.preparation_time = 0.4 # time allowed for the car behind to prepare for the merging car. # FIXME this should be 0.2.

    def run_simulation(self, total_timesteps, merge_position=None, merge_interval=0):

        # Sort the cars by position
        getPosition = lambda x: x.position
        self.car_list.sort(key=getPosition, reverse=True)
        
        merge_preparation_countdown = -999
        self.position_update_count = int(total_timesteps / self.time_precision) + 1
        for time_index in range(self.position_update_count - 1):
            if merge_interval <= 0:
                self.update_car_positions()
                continue

            # Prepares to merge.
            if time_index * self.time_precision % merge_interval == 0:
                merge_preparation_countdown = self.preparation_time / self.time_precision
                self.update_car_positions(merge_position_prepare_to_merge=merge_position, merging=False)
                # print('prepare to merge', merge_position)

            # Commences merging since preparation is over.
            elif merge_preparation_countdown == 0:
                self.update_car_positions(merge_position_prepare_to_merge=None, merging=True)
                merge_preparation_countdown = -999
        
            else:
                self.update_car_positions()

            if merge_preparation_countdown != -999:
                merge_preparation_countdown -= 1

                

    def add_multiple_cars(self, starting_positions, starting_velocity,
                          car_class=None, **car_kwargs):
        ''' Add several cars to the list.

        Args:
            starting_positions: may be a list or float (for a single car)
            starting_velocity: constant starting velocity for all cars
            car_class: Car like object to use, default to the simple Car class
            **car_kwargs: extra keywords to give to cars
        '''
        if car_class is None:
            car_class = Car

        # Treat a integer as a single length list so we can iterate
        if type(starting_positions) is int:
            starting_positions = [starting_positions,]

        for starting_position in starting_positions:
            self.add_car(
                starting_position=starting_position,
                starting_velocity=starting_velocity,
                car_class=car_class,
                **car_kwargs
            )

    def add_car(self, starting_position, starting_velocity, car_class=None,
                **car_kwargs):
        ''' Add a car to the car list.

        Args:
            starting_velocity
            starting_position 
            car_class: Car like object to use, default to the simple Car class
            **car_kwargs: extra keywords to give to cars
        '''
        if car_class is None:
            car_class = Car

        newCar = car_class(starting_position, starting_velocity, self.time_precision, **car_kwargs)
        self.car_list.append(newCar)


    def update_car_positions(self, merge_position_prepare_to_merge=None, merging=False):
        ''' Move all the cars at the given time step. '''
        car_ahead = None
        num_car = 0
        while num_car < len(self.car_list):
            car = self.car_list[num_car]
            
            if self.car_getting_merged_in_front == car:
                if merging:
                    
                    
                    self.car_getting_merged_in_front = None
                    # Merge a new autonomous vehicle in following the speed of the car ahead.
                    self.car_list.insert(num_car, self.merging_car)
                    # print('merge ahead car', car_ahead.position, car_ahead.velocity)
                    car_ahead = self.car_list[num_car]
                    # print('merging car   ', car_ahead.position, car_ahead.velocity)
                    # print('you got merged', car.position, car.velocity)

                    self.merging_car.update_position(car_ahead)
                    num_car += 1
                    # print('merged')

                else:
                    assert self.merging_car
                    
                    
                    car.update_position(self.merging_car, ghost=True)#, debug=True)

                    self.merging_car.velocity = car_ahead.velocity * 0.9
                    self.merging_car.position = car.position + \
                        (car_ahead.position - car.position) * 0.5 # self.merge_dist_ratio


                    # print('updating---')
                    # print('car      pos', car.position)
                    # print('merg car pos', self.merging_car.position)
                    # print('car_ahea pos', car_ahead.position if car_ahead else None)

                    car_ahead = car
                    num_car += 1
                    continue

            # Tells the car to decelerate to prepare for the merging car in front.
            if merge_position_prepare_to_merge and car_ahead and \
                car_ahead.position > merge_position_prepare_to_merge and \
                car.position <= merge_position_prepare_to_merge:
                # TODO make the merging vehicle either AV or HV based on the AV_percentage.
                self.merging_car = AutonomousVehicle(merge_position_prepare_to_merge, \
                    car_ahead.velocity * 0.9, self.time_precision)
                self.car_getting_merged_in_front = car
                # self.merge_dist_ratio = (merge_position_prepare_to_merge - car.position) / \
                #     (car_ahead.position - car.position)
                self.merge_dist_ratio = 0.5
                # print('merge_dist_ratio', self.merge_dist_ratio)


            car.update_position(car_ahead)
            car_ahead = car
            num_car += 1

    def get_distance_to_next_car(self, car, prev_position):
        ''' Get the distance to the car in front.

        Args:
            car: Car object of the car of interest.
            prev_position: x value of the car in front.

        Returns:
            The distance between the car between the rears of the two cars.
        '''
        # The length of the car is handled by the Car's methods
        distance = prev_position - car.position

        # Sanity checks
        if distance < 0:
            error_string = ('Distance' + str(distance) + ' to next'
                            'car should always be positive')
            raise ValueError(error_string)

        return distance

    def get_history_position_array(self):
        ''' Create a history-position array for all the cars on the road

        Returns:
            The value of x positions of the cars, each row
            represents a different car, each column is a time point in
            the simulation.
        '''
        distance_array = []

        for i, car in enumerate(self.car_list):

            # Pads the stats for the merging vehicles before they merged.
            padded_arr = [-100 - i * 10] * (self.position_update_count - \
                len(car.return_position_array())) + car.return_position_array()
            distance_array.append(padded_arr)
        distance_array = np.vstack(distance_array)
        return distance_array

    def get_history_potential_crashes(self):

        crashes_array = []
        for car in self.car_list:

            # Pads the stats for the merging vehicles before they merged.
            padded_arr = [0] * (self.position_update_count - \
                len(car.return_potential_crashes_history())) + car.return_potential_crashes_history()
            crashes_array.append(padded_arr)

        crashes_array = np.vstack(crashes_array)
        crashes_array = crashes_array.sum(axis = 0)
        return crashes_array

    def get_through_vehicle_count(self, distance):
        return sum([car.position >= distance for car in self.car_list])