from simulation import Simulation, SimulationParams


def main():

    hcdsb_schedule = [
        '1A', '2A', '1A', '1B', '2B',
        '1A', '2A', '1B', '1B', '2B',
        '1A', '2A', '2A', '1B', '2B',
        '1A', '2A', '2B', '1B', '2B',
    ]

    hdsb_schedule = [
        '1A', '1A', '1A', '1B', '1B',
        '2A', '2A', '2A', '2B', '2B',
        '1A', '1A', '1A', '1B', '1B',
        '2A', '2A', '2B', '2B', '2B',
        '1A', '1A', '1B', '1B', '1B',
    ]

    two_week_schedule = [
        '1A', '1A', '1A', '1B', '1B',
        '1A', '1A', '1B', '1B', '1B',
        '2A', '2A', '2A', '2B', '2B',
        '2A', '2A', '2B', '2B', '2B',
    ]

    params_dict = {
        'total_students': 1200,
        'students_per_class': 15,
        'cohort_switches': 20,
        'class_size_fudge': 1.1,
        'class_assignment_retry': 150,
        'outside_grade_probability': {
            9: 0.0,
            10: 0.033333,
            11: 0.066666,
            12: 0.066666
        },
        'iterations': 20,
        'percentage_in_class': 0.75,
        'max_degree': 12,
        'schedule': two_week_schedule
    }

    config = SimulationParams(**params_dict)
    sim = Simulation(config)
    sim.simulate()
    sim.output_results()


if __name__ == '__main__':
    main()
