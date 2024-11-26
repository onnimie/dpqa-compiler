import matplotlib.pyplot as plt
import numpy as np

def getx(trap):
    return trap.get_position_xy()[0]


def gety(trap):
    return trap.get_position_xy()[1]

def trap_is_occupied(trap):
    return len(trap.qubits) > 0

def trap_is_unoccupied(trap):
    return not trap_is_occupied(trap)


def show_current_state(dpqa_dev, draw_movement_lines=True, indx=0):
    all_aod_traps = dpqa_dev.flat_aod_traps
    all_slm_traps = dpqa_dev.slm_traps

    occupied_aod_traps = list(filter(trap_is_occupied, all_aod_traps))
    x_aod_occupied = list(map(getx, occupied_aod_traps))
    y_aod_occupied = list(map(gety, occupied_aod_traps))

    unoccupied_aod_traps = list(filter(trap_is_unoccupied, all_aod_traps))
    x_aod_unoccupied = list(map(getx, unoccupied_aod_traps))
    y_aod_unoccupied = list(map(gety, unoccupied_aod_traps))

    occupied_slm_traps = list(filter(trap_is_occupied, all_slm_traps))
    x_slm_occupied = list(map(getx, occupied_slm_traps))
    y_slm_occupied = list(map(gety, occupied_slm_traps))

    unoccupied_slm_traps = list(filter(trap_is_unoccupied, all_slm_traps))
    x_slm_unoccupied = list(map(getx, unoccupied_slm_traps))
    y_slm_unoccupied = list(map(gety, unoccupied_slm_traps))

    sizes_aod_occupied = len(occupied_aod_traps) * [30]
    color_aod_occupied = 'red'
    sizes_aod_unoccupied = len(unoccupied_aod_traps) * [30]
    color_aod_unoccupied = 'red'
    alpha_aod_unoccupied = 0.2

    sizes_slm_occupied = len(occupied_slm_traps) * [80]
    color_slm_occupied = 'blue'
    sizes_slm_unoccupied = len(unoccupied_slm_traps) * [80]
    color_slm_unoccupied = 'blue'
    alpha_slm_unoccupied = 0.2

    fig, ax = plt.subplots()

    if draw_movement_lines:
        for aod_trap in all_aod_traps:
            mov_vec = aod_trap.movement_vector
            if mov_vec != (0,0):
                end_x, end_y = aod_trap.get_position_xy()
                start_x, start_y = (end_x - mov_vec[0],
                                    end_y - mov_vec[1])
                ax.plot([start_x, end_x], [start_y, end_y],
                        linestyle='dashed',
                        alpha=0.7,
                        color='orange')
                
    dpqa_dev.clear_movement_vectors()

    if dpqa_dev.previous_rydberg_laser_pos != (-1, -1):
        laser_pos = dpqa_dev.previous_rydberg_laser_pos
        operation = dpqa_dev.previous_rydberg_laser_op
        circle = plt.Circle(xy=(laser_pos),
                            radius=dpqa_dev.rydberg_radius + 0.1,
                            color='green',
                            fill=False,
                            alpha=0.6)
        ax.add_patch(circle)
    dpqa_dev.previous_rydberg_laser_pos = (-1, -1)
        

    #ax.scatter(x_slm_occupied, y_slm_occupied, s=sizes_slm_occupied, color = color_slm_occupied)
    #ax.scatter(x_slm_unoccupied, y_slm_unoccupied, s=sizes_slm_unoccupied, color = color_slm_unoccupied, alpha = alpha_slm_unoccupied)
    #ax.scatter(x_aod_occupied, y_aod_occupied, s=sizes_aod_occupied, color = color_aod_occupied)
    #ax.scatter(x_aod_unoccupied, y_aod_unoccupied, s=sizes_aod_unoccupied, color = color_aod_unoccupied, alpha = alpha_aod_unoccupied)

    slm_trap_rad = 0.20
    aod_trap_rad = 0.15

    for i in range(len(occupied_slm_traps)):
        pos = (x_slm_occupied[i], y_slm_occupied[i])
        circle = plt.Circle(xy=pos,
                            radius=slm_trap_rad,
                            color = color_slm_occupied)
        ax.add_patch(circle)
        #print(str(occupied_slm_traps[i].qubits))
        ax.annotate(str(occupied_slm_traps[i].qubits[0].x),
                    xy=pos,
                    fontsize=10,
                    ha="center",
                    va="center",
                    color="white")
    
    for i in range(len(unoccupied_slm_traps)):
        pos = (x_slm_unoccupied[i], y_slm_unoccupied[i])
        circle = plt.Circle(xy=pos,
                            radius=slm_trap_rad,
                            alpha=alpha_slm_unoccupied,
                            color = color_slm_unoccupied)
        ax.add_patch(circle)
    
    for i in range(len(occupied_aod_traps)):
        pos = (x_aod_occupied[i], y_aod_occupied[i])
        circle = plt.Circle(xy=pos,
                            radius=aod_trap_rad,
                            color = color_aod_occupied)
        ax.add_patch(circle)
        ax.annotate(str(occupied_aod_traps[i].qubits[0].x),
                    xy=pos,
                    fontsize=10,
                    ha="center",
                    va="center")
    
    for i in range(len(unoccupied_aod_traps)):
        pos = (x_aod_unoccupied[i], y_aod_unoccupied[i])
        circle = plt.Circle(xy=pos,
                            radius=aod_trap_rad,
                            alpha=alpha_aod_unoccupied,
                            color = color_aod_unoccupied)
        ax.add_patch(circle)
    

    ax.set(xlim=(-1, dpqa_dev.max_dim_x), xticks=np.arange(0, dpqa_dev.max_dim_x), ylim=(-1, dpqa_dev.max_dim_y), yticks=np.arange(0, dpqa_dev.max_dim_y))
    ax.set_aspect('equal')
    #ax.autoscale_view()

    #plt.savefig(f'compiler_better_{indx}')
    plt.show()

