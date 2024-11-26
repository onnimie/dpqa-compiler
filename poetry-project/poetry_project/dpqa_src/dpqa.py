import cirq
import math

from dpqa_src.dpqa_traps import SLMTrap, AODTrap
from dpqa_src.dpqa_plotter import show_current_state
from dpqa_src.dpqa_instructions import Instruction, ActivateAODCol, ActivateAODRow, DeactivateAODCol, DeactivateAODRow, DrawState, Initialize, MoveAODCol, MoveAODRow, RydbergLaser

class DPQA(cirq.Device):

    def __init__(
        self,
        aod_rows,
        aod_cols,
        slm_positions_xy,
        max_dim_x,
        max_dim_y,
        rydberg_radius,
        trap_transfer_radius
    ):
        self.nof_qubits = 0

        self.max_dim_x = max_dim_x
        self.max_dim_y = max_dim_y
        self.rydberg_radius = rydberg_radius
        self.trap_transfer_radius = trap_transfer_radius
        
        self.previous_rydberg_laser_pos = (-1, -1)
        self.previous_rydberg_laser_op = "none"

        self.aod_traps = []  # qubit on row i, col j is aod_qubits[i][j]
        self.slm_traps = [] 
        self.flat_aod_traps = []

        self.aod_rows = aod_rows
        self.aod_cols = aod_cols

        for i in range(aod_rows):
            aod_row = []
            for j in range(aod_cols):
                aod_trap = AODTrap(i, j)
                aod_row.append(aod_trap)
                self.flat_aod_traps.append(aod_trap)
            self.aod_traps.append(aod_row)

        for pos in slm_positions_xy:
            assert(pos[0] >= 0 and pos[0] <= max_dim_x)
            assert(pos[1] >= 0 and pos[1] <= max_dim_y)
            slm_trap = SLMTrap(pos[0], pos[1])
            self.slm_traps.append(slm_trap)
    
    def add_qubits_to_aod_traps(self, qubits, aod_trap_positions_rowcol):
        assert(len(qubits) == len(aod_trap_positions_rowcol))
        for i in range(len(qubits)):
            q = qubits[i]
            aod_trap_pos = aod_trap_positions_rowcol[i]
            aod_trap = self.aod_traps[aod_trap_pos[0]][aod_trap_pos[1]]
            aod_trap.add_qubits(q)
            self.nof_qubits += 1
    
    def add_qubits_to_slm_traps(self, qubits, slm_trap_indices):
        assert(len(qubits) == len(slm_trap_indices))
        for i in range(len(qubits)):
            q = qubits[i]
            slm_trap = self.slm_traps[slm_trap_indices[i]]
            slm_trap.add_qubits(q)
            self.nof_qubits += 1

    def move_aod_row_by(self, aod_row_index, offset):
        aod_row = self.aod_traps[aod_row_index]
        current_y = aod_row[0].get_position_xy()[1]
        new_y = current_y + offset

        assert new_y <= self.max_dim_y and new_y >= -self.max_dim_y

        if offset < 0 and aod_row_index != 0:
            aod_y_below_this = self.aod_traps[aod_row_index - 1][0].get_position_xy()[
                1
            ]
            assert new_y > aod_y_below_this
        if offset > 0 and aod_row_index != self.aod_rows - 1:
            aod_y_below_this = self.aod_traps[aod_row_index + 1][0].get_position_xy()[
                1
            ]
            assert new_y < aod_y_below_this

        for aod_qubit in aod_row:
            aod_qubit.move_trap_by(0, offset)

    def move_aod_col_by(self, aod_col_index, offset):
        aod_col = [aod_row[aod_col_index] for aod_row in self.aod_traps]
        current_x = aod_col[0].get_position_xy()[0]
        new_x = current_x + offset

        assert new_x <= self.max_dim_x and new_x >= -self.max_dim_x

        if offset < 0 and aod_col_index != 0:
            aod_x_left_of_this = self.aod_traps[0][
                aod_col_index - 1
            ].get_position_xy()[0]
            assert new_x > aod_x_left_of_this
        if offset > 0 and aod_col_index != self.aod_cols - 1:
            aod_x_right_of_this = self.aod_traps[0][
                aod_col_index + 1
            ].get_position_xy()[0]
            assert new_x < aod_x_right_of_this

        for aod_qubit in aod_col:
            aod_qubit.move_trap_by(offset, 0)
    

    def activate_aod_row(self, aod_row_index):
        aod_row = self.aod_traps[aod_row_index]
        for aod_trap in aod_row:
            if len(aod_trap.qubits) == 0:
                for slm_trap in self.slm_traps:
                    p1 = aod_trap.get_position_xy()
                    p2 = slm_trap.get_position_xy()
                    if self.distance_between_points(p1, p2) <= self.trap_transfer_radius and len(slm_trap.qubits) > 0:
                        q = slm_trap.remove_qubits()
                        aod_trap.add_qubits(q)
                        break

    
    def activate_aod_col(self, aod_col_index):
        aod_col = [aod_row[aod_col_index] for aod_row in self.aod_traps]
        for aod_trap in aod_col:
            if len(aod_trap.qubits) == 0:
                for slm_trap in self.slm_traps:
                    p1 = aod_trap.get_position_xy()
                    p2 = slm_trap.get_position_xy()
                    if self.distance_between_points(p1, p2) <= self.trap_transfer_radius and len(slm_trap.qubits) > 0:
                        q = slm_trap.remove_qubits()
                        aod_trap.add_qubits(q)
                        break

    def deactivate_aod_row(self, aod_row_index):
        aod_row = self.aod_traps[aod_row_index]
        for aod_trap in aod_row:
            if len(aod_trap.qubits) > 0:
                q = aod_trap.remove_qubits()
                for slm_trap in self.slm_traps:
                    p1 = aod_trap.get_position_xy()
                    p2 = slm_trap.get_position_xy()
                    if self.distance_between_points(p1, p2) < self.trap_transfer_radius and len(slm_trap.qubits) == 0:
                        slm_trap.add_qubits(q)
                        break

    def deactivate_aod_col(self, aod_col_index):
        aod_col = [aod_row[aod_col_index] for aod_row in self.aod_traps]
        for aod_trap in aod_col:
            if len(aod_trap.qubits) > 0:
                q = aod_trap.remove_qubits()
                for slm_trap in self.slm_traps:
                    p1 = aod_trap.get_position_xy()
                    p2 = slm_trap.get_position_xy()
                    if self.distance_between_points(p1, p2) < self.trap_transfer_radius and len(slm_trap.qubits) == 0:
                        slm_trap.add_qubits(q)
                        break

    def distance_between_points(self, p1, p2):
        distance_vector = [p1[0] - p2[0], p1[1] - p2[1]]
        distance = math.sqrt(
            (distance_vector[0] * distance_vector[0])
            + (distance_vector[1] * distance_vector[1])
        )
        return distance
    
    def rydberg_interaction_on_position(self, laser_pos_xy, operation):
        affected_qubits = []
        affected_traps = []
        for trap in (self.flat_aod_traps + self.slm_traps):
            trap_pos = trap.get_position_xy()
            if self.distance_between_points(trap_pos, laser_pos_xy) < self.rydberg_radius:
                for q in trap.qubits:
                    affected_qubits.append(q)
                affected_traps.append(trap)
        
        # do the operation on affected qubits
        self.previous_rydberg_laser_pos = laser_pos_xy
        self.previous_rydberg_laser_op = operation
        if operation == 'SWAP':
            assert(len(affected_qubits) <= 2)
            if len(affected_qubits) == 2:
                q1 = affected_traps[0].remove_qubits()
                q2 = affected_traps[1].remove_qubits()
                affected_traps[0].add_qubits(q2)
                affected_traps[1].add_qubits(q1)

    def clear_movement_vectors(self):
        for aod_trap in self.flat_aod_traps:
            aod_trap.movement_vector = (0,0)

    def execute_instructions(self,
                             instructions,
                             draw_states_between_instructions=True,
                             print_instructions=True):
        indx = 0
        for inst in instructions:
            assert(isinstance(inst, Instruction))
            if isinstance(inst, ActivateAODRow):
                self.activate_aod_row(inst.row_index)
            elif isinstance(inst, ActivateAODCol):
                self.activate_aod_col(inst.col_index)
            elif isinstance(inst, DeactivateAODRow):
                self.deactivate_aod_row(inst.row_index)
            elif isinstance(inst, DeactivateAODCol):
                self.deactivate_aod_col(inst.col_index)
            elif isinstance(inst, RydbergLaser):
                self.rydberg_interaction_on_position(inst.target_pos, inst.operation)
            elif isinstance(inst, MoveAODRow):
                self.move_aod_row_by(inst.row_index, inst.offset)
            elif isinstance(inst, MoveAODCol):
                self.move_aod_col_by(inst.col_index, inst.offset)
            elif isinstance(inst, Initialize):
                self.add_qubits_to_aod_traps(inst.aod_qubits, inst.aod_qubit_positions_rowcol)
                self.add_qubits_to_slm_traps(inst.slm_qubits, inst.slm_trap_indices)
            elif isinstance(inst, DrawState):
                show_current_state(self, draw_movement_lines=True)
            else:
                # unknown instruction
                pass
            if print_instructions:
                print(inst)
            if draw_states_between_instructions:
                show_current_state(self, draw_movement_lines=True, indx=indx)
            indx += 1