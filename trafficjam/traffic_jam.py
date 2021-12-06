#!/usr/bin/env python

from road import Road
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from car import AutonomousVehicle, HumanVehicle, Car
import random

''' Main script to run the traffic jam simulation. '''

n_cars = 70
n_timesteps = 100
# starting_space = 100
starting_velocity = 0

def simple_run(n_timesteps):
    ''' Run the simulation for a given number of timesteps.

    Args:
        n_timesteps: number of steps to take in the simulation

    Returns:
        history_position_array: An array containing the positions of all the
        cars with time.
    '''
    road = Road()

    # Populate the road with cars
    road.add_multiple_cars(starting_positions, starting_velocity)
    road.run_simulation(n_timesteps)
    history_position_array = road.get_history_position_array()
    return history_position_array

def peturb_traffic(starting_positions, time_breakdown, slow_car_num=3):
    '''Allow the simulation to run for a given number of steps before suddenly
    slowing one car and resuming the simulation.

    Args:
        starting_positions: List of starting_position to pass to ``road.add_multiple_cars``
        n_timesteps_before: How many steps to run before the car is slowed
        n_timesteps_slowed: How many steps the car goes at a reduced speed
        n_timesteps_after: How many steps to record after the car has recovered
        slow_car_num: the index of the car to slow, starting at the front of the road

    Returns:
        An array containing the positions of all the cars with time.
    '''

    n_timesteps_before, n_timesteps_slowed, n_timesteps_after = time_breakdown
    road = Road()

    # Add the cars and allow them to run for a while
    road.add_multiple_cars(starting_positions, starting_velocity, car_class=AutonomousVehicle)
    road.run_simulation(n_timesteps_before)

    # Slow a car in the middle of pack
    slowed_car = road.car_list[slow_car_num]
    slowed_car.max_velocity = 20
    slowed_car.velocity = 20

    # Resume the simulation
    road.run_simulation(n_timesteps_slowed)

    # Allow the car to recover
    slowed_car.max_velocity = 60
    road.run_simulation(n_timesteps_after)

    # Measure throughput for the first 5000 meters.
    print('Throughput', road.get_through_vehicle_count(5000) / sum(time_breakdown))

    history_position_array = road.get_history_position_array()
    history_potential_crashes = road.get_history_potential_crashes()
    return history_position_array, history_potential_crashes


def simulate_AV_HV_mix(starting_positions, AV_percentage):
    '''Simulate with what percentage of AV on the road and what throughput is.
    '''
    
    assert AV_percentage >= 0 and AV_percentage <= 1
    AV_car_indices = random.sample(range(len(starting_positions)),
                                  int(AV_percentage * len(starting_positions)))

    road = Road()

    # Add the cars and allow them to run for a while
    for i, starting_position in enumerate(starting_positions):
        car_class = AutonomousVehicle if i in AV_car_indices else HumanVehicle
        road.add_car(starting_position, starting_velocity, car_class)

    road.run_simulation(100)


    # Measure throughput for the first 5000 meters.
    print('AV_percentage', AV_percentage, 'Throughput', road.get_through_vehicle_count(1000))

    history_position_array = road.get_history_position_array()
    history_potential_crashes = road.get_history_potential_crashes()
    return history_position_array, history_potential_crashes

def run_simulation_mix():

    for perc in range(0, 101, 10):
        perc = perc / 100
        starting_space = 1
        starting_positions = np.arange(n_cars)*starting_space
        history_position_array, history_potential_crashes = simulate_AV_HV_mix(starting_positions, perc)
        save_name = '../data/mix/history_positions_' + str(perc) + '.csv'
        save_dataframe(history_position_array, save_name)
        save_name = '../data/mix/history_crashes_' + str(perc) + '.csv'
        save_dataframe(history_potential_crashes, save_name)



def simulate_AV_HV_mix_merging(starting_positions, AV_percentage, merging_car_count):
    '''Simulate with what percentage of AV on the road and what throughput is.
    '''
    
    assert AV_percentage >= 0 and AV_percentage <= 1
    AV_car_indices = random.sample(range(len(starting_positions)),
                                  int(AV_percentage * len(starting_positions)))

    road = Road()

    # Add the cars and allow them to run for a while
    for i, starting_position in enumerate(starting_positions):
        car_class = AutonomousVehicle if i in AV_car_indices else HumanVehicle
        road.add_car(starting_position, starting_velocity, car_class)

    total_time = 100
    merge_position = 200
    # FIXME This is still an estmiate

    merge_interval = 0
    if merging_car_count > 0:
        merge_interval = (total_time - merge_position / Car(1,2,3).max_velocity) // merging_car_count
    road.run_simulation(total_time, merge_position = merge_position, merge_interval=merge_interval)

    history_position_array = road.get_history_position_array()
    history_potential_crashes = road.get_history_potential_crashes()

    # Measure throughput for the first 5000 meters.
    # print('AV_percentage', AV_percentage, '\tThroughput', road.get_through_vehicle_count(1000), \
    #     '\tTotal Crashes', history_potential_crashes[-1])
    return history_position_array, history_potential_crashes, \
        road.get_through_vehicle_count(1000), history_potential_crashes[-1]

def run_simulation_mix_merging():

    merging_car_counts = [20]#, 15, 10, 5, 1, 0]
    for merging_car_count in merging_car_counts:
        print()
        print('merging_car_count', merging_car_count)
        for perc in range(0, 101, 10):
            perc = perc / 100
            starting_space = 1
            starting_positions = np.arange(n_cars)*starting_space

            throughputs, crashes = [], []
            num_trials = 10
            for _ in range(num_trials):
                history_position_array, history_potential_crashes, throughput, crash = \
                    simulate_AV_HV_mix_merging(starting_positions, perc, merging_car_count)

                throughputs.append(throughput)
                crashes.append(crash)

            throughputs.sort()
            throughputs = throughputs[int(len(throughputs) * 0.1) : int(len(throughputs) * 0.9)]
            crashes.sort()
            crashes = crashes[int(len(crashes) * 0.1) : int(len(crashes) * 0.9)]
            print('AV_percentage', perc, '\tThroughput', sum(throughputs) / len(throughputs), \
                '\tHard Stops', sum(crashes) / len(crashes))
            save_name = '../data/mix/history_positions_' + str(perc) + '.csv'
            save_dataframe(history_position_array, save_name)
            save_name = '../data/mix/history_crashes_' + str(perc) + '.csv'
            save_dataframe(history_potential_crashes, save_name)



def save_dataframe(data, save_location='../data/simpleDistanceHistory.csv'):
    ''' Write the position array to file as a csv. '''
    distance_dataframe = pd.DataFrame(data)
    distance_dataframe.to_csv(save_location)

def start_space_sweep(minimum_space, maximum_space, interval):
    ''' Run the simulation for several different starting positions.

    Args:
       minimum_space: The smallest starting distance between cars
       maximum_space: The largest starting distance between the cars
       interval: The size of the steps to take between these two extremes
    '''
    for starting_space in [80, 200, 211, 212, 400]: # range(80, 81): # range(80, 240+1, 20):
        starting_positions = np.arange(n_cars)*starting_space
        history_position_array, history_potential_crashes = peturb_traffic(starting_positions, [50, 40, 250])
        save_name = '../data/history_positions_' + str(starting_space) + '.csv'
        save_dataframe(history_position_array, save_name)
        save_name = '../data/history_crashes_' + str(starting_space) + '.csv'
        save_dataframe(history_potential_crashes, save_name)

if __name__ == '__main__':
    # start_space_sweep(30, 250, 250)

    run_simulation_mix_merging()
    # run_simulation_mix()