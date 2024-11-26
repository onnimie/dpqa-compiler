import math
import cirq
from dpqa_src.dpqa import DPQA
from dpqa_src.dpqa_instructions import Instruction, ActivateAODCol, ActivateAODRow, DeactivateAODCol, DeactivateAODRow, DrawState, Initialize, MoveAODCol, MoveAODRow, RydbergLaser


def get_grid(start_pos_rowcol, rows, cols):
    grid = []
    for c in range(cols):
        for r in range(rows):
            grid.append((start_pos_rowcol[0] + r,
                         start_pos_rowcol[1] + c))
    return grid

def compile(circuit: cirq.Circuit):

    nof_qubits = len(circuit.all_qubits())

    aod_rows = math.ceil(math.sqrt(nof_qubits))
    aod_cols = math.ceil(math.sqrt(nof_qubits))
    a = aod_rows + math.ceil(aod_rows/2)
    a = a + ((a + 1) % 2)
    b = aod_cols + math.ceil(aod_cols/2)
    b = b + ((b + 1) % 2)
    slm_rows = a
    slm_cols = b

    device = DPQA(
        aod_rows=aod_rows,
        aod_cols=aod_cols,
        slm_positions_xy=get_grid(start_pos_rowcol=(aod_rows, aod_cols),
                                  rows=slm_rows,
                                  cols=slm_cols),
        max_dim_x=aod_cols + slm_cols,
        max_dim_y=aod_rows + slm_rows,
        rydberg_radius=0.3,
        trap_transfer_radius=0.01
)

    compiled_instructions = []
    assert(nof_qubits <= device.aod_cols * device.aod_rows)

    qubit_positions_rowcol = []
    for i in range(nof_qubits):
        row = math.floor(i / device.aod_rows)
        col = i % device.aod_cols
        qubit_positions_rowcol.append((row,col))

    init = Initialize(aod_qubits=cirq.LineQubit.range(nof_qubits),
               aod_qubit_positions_rowcol=qubit_positions_rowcol,
               slm_qubits=[],
               slm_trap_indices=[])
    compiled_instructions.append(init)

    def reverseDir(instr):
        if isinstance(instr, MoveAODCol):
            return MoveAODCol(instr.col_index, -instr.offset)
        else:
            return MoveAODRow(instr.row_index, -instr.offset)

    for moment in circuit:
        for oper in moment.operations:
            if len(oper.qubits) == 2:
                q1 = oper.qubits[0].x
                q2 = oper.qubits[1].x
                (pos1, pos2) = (qubit_positions_rowcol[q1], qubit_positions_rowcol[q2])
                if pos1[0] == pos2[0]: #same row
                    col_diff = pos2[1] - pos1[1]
                    if abs(col_diff) == 1: #neighboring columns
                        compiled_instructions.append(MoveAODCol(pos1[1], 0.8*col_diff))
                        compiled_instructions.append(RydbergLaser((pos2[1], pos2[0]),
                                                                   operation=oper.gate))
                        compiled_instructions.append(MoveAODCol(pos1[1], -0.8*col_diff))
                    else:
                        # same row but not neighbors
                        first_qubit_to_move = 0
                        second_qubit_to_move = 0
                        if pos1[1] > pos2[1]:
                            first_qubit_to_move = q1
                            second_qubit_to_move = q2
                        else:
                            first_qubit_to_move = q2
                            second_qubit_to_move = q1
                        first_qubit_to_move_pos = qubit_positions_rowcol[first_qubit_to_move]
                        second_qubit_to_move_pos = qubit_positions_rowcol[second_qubit_to_move]

                        #target_slm_rowcol = device.slm_traps[math.floor(len(device.slm_traps)/2)].get_position_xy()
                        offset_col_from_second_to_first = first_qubit_to_move_pos[1] - second_qubit_to_move_pos[1]

                        move1_instr = []
                        for row in reversed(range(0, device.aod_rows)):
                            move1_instr.append(MoveAODRow(row, aod_rows))
                        for col in reversed(range(0, device.aod_cols)):
                            move1_instr.append(MoveAODCol(col, aod_cols))
                        
                        move1_reversed_instr = reversed(move1_instr)
                        move1_reversed_dirs_instr = list(map(reverseDir, move1_reversed_instr))
                        
                        compiled_instructions.extend(move1_instr)
                        compiled_instructions.append(DeactivateAODCol(first_qubit_to_move_pos[1]))

                        move2_instr = []
                        for col in reversed(range(0, device.aod_cols)):
                            move2_instr.append(MoveAODCol(col, offset_col_from_second_to_first - 0.2))
                        
                        move2_reversed_instr = reversed(move2_instr)
                        move2_reversed_dirs_instr = list(map(reverseDir, move2_reversed_instr))

                        compiled_instructions.extend(move2_instr)
                        compiled_instructions.append(RydbergLaser((first_qubit_to_move_pos[1] + aod_rows,
                                                                   first_qubit_to_move_pos[0] + aod_cols), oper.gate))
                        compiled_instructions.extend(move2_reversed_dirs_instr)

                        compiled_instructions.append(ActivateAODCol(first_qubit_to_move_pos[1]))
                        compiled_instructions.extend(move1_reversed_dirs_instr)
                        
                elif pos1[1] == pos2[1]: #same col
                    row_diff = pos2[1] - pos1[1]
                    if abs(row_diff) == 1: #neighboring rows
                        compiled_instructions.append(MoveAODRow(pos1[0], 0.8*row_diff))
                        compiled_instructions.append(RydbergLaser((pos2[1], pos2[0]),
                                                                   operation=oper.gate))
                        compiled_instructions.append(MoveAODRow(pos1[0], -0.8*row_diff))
                    else:
                        # same col but not neighbors
                        first_qubit_to_move = 0
                        second_qubit_to_move = 0
                        if pos1[0] > pos2[0]:
                            first_qubit_to_move = q1
                            second_qubit_to_move = q2
                        else:
                            first_qubit_to_move = q2
                            second_qubit_to_move = q1
                        first_qubit_to_move_pos = qubit_positions_rowcol[first_qubit_to_move]
                        second_qubit_to_move_pos = qubit_positions_rowcol[second_qubit_to_move]

                        #target_slm_rowcol = device.slm_traps[math.floor(len(device.slm_traps)/2)].get_position_xy()
                        offset_row_from_second_to_first = first_qubit_to_move_pos[0] - second_qubit_to_move_pos[0]

                        move1_instr = []
                        for row in reversed(range(0, device.aod_rows)):
                            move1_instr.append(MoveAODRow(row, aod_rows))
                        for col in reversed(range(0, device.aod_cols)):
                            move1_instr.append(MoveAODCol(col, aod_cols))
                        
                        move1_reversed_instr = reversed(move1_instr)
                        move1_reversed_dirs_instr = list(map(reverseDir, move1_reversed_instr))
                        
                        compiled_instructions.extend(move1_instr)
                        compiled_instructions.append(DeactivateAODRow(first_qubit_to_move_pos[0]))

                        move2_instr = []
                        for row in reversed(range(0, device.aod_rows)):
                            move2_instr.append(MoveAODRow(row, offset_row_from_second_to_first - 0.2))
                        
                        move2_reversed_instr = reversed(move2_instr)
                        move2_reversed_dirs_instr = list(map(reverseDir, move2_reversed_instr))

                        compiled_instructions.extend(move2_instr)
                        compiled_instructions.append(RydbergLaser((first_qubit_to_move_pos[1] + aod_rows,
                                                                   first_qubit_to_move_pos[0] + aod_cols), oper.gate))
                        compiled_instructions.extend(move2_reversed_dirs_instr)

                        compiled_instructions.append(ActivateAODRow(first_qubit_to_move_pos[0]))
                        compiled_instructions.extend(move1_reversed_dirs_instr)
                else:
                    # aod positions are not neighboring nor on the same row/col
                    target_slm_rowcol = device.slm_traps[math.floor(len(device.slm_traps)/2)].get_position_xy()
                    higher_row = max(pos1[0], pos2[0])
                    first_qubit_to_move = 0
                    second_qubit_to_move = 0
                    if pos1[0] == higher_row:
                        first_qubit_to_move = q1
                        second_qubit_to_move = q2
                    else:
                        first_qubit_to_move = q2
                        second_qubit_to_move = q1
                    first_qubit_to_move_pos = qubit_positions_rowcol[first_qubit_to_move]
                    offset_row_to_target = target_slm_rowcol[0] - higher_row
                    move1_instr = []
                    for upper_row in reversed(range(0, device.aod_rows)):
                        move1_instr.append(MoveAODRow(upper_row, offset_row_to_target))

                    offset_col_to_target = target_slm_rowcol[1] - first_qubit_to_move_pos[1]
                    for upper_col in  reversed(range(0, device.aod_cols)):
                        move1_instr.append(MoveAODCol(upper_col, offset_col_to_target))

                    move1_reversed_instr = reversed(move1_instr)
                    move1_reversed_dirs_instr = list(map(reverseDir, move1_reversed_instr))

                    compiled_instructions.extend(move1_instr)
                    compiled_instructions.append(DeactivateAODRow(higher_row))
                    compiled_instructions.extend(move1_reversed_dirs_instr)

                    second_qubit_to_move_pos = qubit_positions_rowcol[second_qubit_to_move]
                    smaller_row = min(pos1[0], pos2[0])
                    offset_row_to_target = target_slm_rowcol[0] - higher_row
                    move2_instr = []
                    for upper_row in reversed(range(0, device.aod_rows)):
                        move2_instr.append(MoveAODRow(upper_row, offset_row_to_target))
                    
                    offset_col_to_target = target_slm_rowcol[1] - second_qubit_to_move_pos[1]
                    for upper_col in reversed(range(0, device.aod_cols)):
                        move2_instr.append(MoveAODCol(upper_col, offset_col_to_target))
                    
                    move2_instr.append(MoveAODRow(smaller_row, 0.8))
                    
                    move2_reversed_instr = reversed(move2_instr)
                    move2_reversed_dirs_instr = list(map(reverseDir, move2_reversed_instr))

                    compiled_instructions.extend(move2_instr)
                    compiled_instructions.append(RydbergLaser(target_slm_rowcol,
                                                              operation=oper.gate))
                    compiled_instructions.extend(move2_reversed_dirs_instr)
                    compiled_instructions.extend(move1_instr)
                    compiled_instructions.append(ActivateAODRow(higher_row))
                    compiled_instructions.extend(move1_reversed_dirs_instr)

    return (device, compiled_instructions)


def compile_overlapping_traps(circuit: cirq.Circuit):
    nof_qubits = len(circuit.all_qubits())

    aod_rows = math.ceil(math.sqrt(nof_qubits))
    aod_cols = math.ceil(math.sqrt(nof_qubits))
    slm_rows = aod_rows
    slm_cols = aod_cols

    device = DPQA(
        aod_rows=aod_rows,
        aod_cols=aod_cols,
        slm_positions_xy=get_grid(start_pos_rowcol=(0,0),
                                  rows=slm_rows,
                                  cols=slm_cols),
        max_dim_x=aod_cols + 1,
        max_dim_y=aod_rows + 1,
        rydberg_radius=0.3,
        trap_transfer_radius=0.01
)

    compiled_instructions = []
    assert(nof_qubits <= device.aod_cols * device.aod_rows)

    qubit_positions_rowcol = []
    for i in range(nof_qubits):
        row = math.floor(i / device.aod_rows)
        col = i % device.aod_cols
        qubit_positions_rowcol.append((row,col))

    init = Initialize(aod_qubits=[],
               aod_qubit_positions_rowcol=[],
               slm_qubits=cirq.LineQubit.range(nof_qubits),
               slm_trap_indices=range(nof_qubits))
    compiled_instructions.append(init)

    def reverseInstruction(instr):
        if isinstance(instr, MoveAODCol):
            return MoveAODCol(instr.col_index, -instr.offset)
        elif isinstance(instr, MoveAODRow):
            return MoveAODRow(instr.row_index, -instr.offset)
        elif isinstance(instr, ActivateAODCol):
            return DeactivateAODCol(instr.col_index)
        elif isinstance(instr, DeactivateAODCol):
            return ActivateAODCol(instr.col_index)
        elif isinstance(instr, ActivateAODRow):
            return DeactivateAODRow(instr.row_index)
        else:
            assert(isinstance(instr, DeactivateAODRow))
            return ActivateAODRow(instr.row_index)
    
    def sign(n):
        if n >= 0:
            return 1
        else:
            return -1

    for moment in circuit:
        for oper in moment.operations:
            if len(oper.qubits) == 2:
                q1 = oper.qubits[0].x
                q2 = oper.qubits[1].x
                (pos1, pos2) = (qubit_positions_rowcol[q1], qubit_positions_rowcol[q2])
 
                row_diff = pos2[0] - pos1[0]
                col_diff = pos2[1] - pos1[1]

                row_diff_sign = sign(row_diff)
                col_diff_sign = sign(col_diff)

                row_offset = row_diff_sign*0.2
                col_offset = col_diff_sign*0.2
                if pos1[0] == pos2[0]:
                    row_offset = 0
                if pos1[1] == pos2[1]:
                    col_offset = 0

                move_instr = []

                for row in range(pos1[0], pos2[0], row_diff_sign):
                    move_instr.append(ActivateAODRow(row))
                
                for col in range(pos1[1], pos2[1], col_diff_sign):
                    move_instr.append(ActivateAODCol(col))

                counter = 0
                for row in reversed(range(pos1[0], pos2[0] + row_diff_sign, row_diff_sign)):
                    this_row_diff = pos2[0] - row
                    if row != pos1[0]:
                        offset = this_row_diff + row_diff_sign*(0.99 - counter*0.01)
                        if offset != 0:
                            move_instr.append(MoveAODRow(row, offset))
                    else:
                        offset = row_diff - row_offset
                        if offset != 0:
                            move_instr.append(MoveAODRow(row, offset))
                    counter += 1
                
                counter = 0
                for col in reversed(range(pos1[1], pos2[1] + col_diff_sign, col_diff_sign)):
                    this_col_diff = pos2[1] - col
                    if col != pos1[1]:
                        offset = this_col_diff + col_diff_sign*(0.99 - counter*0.01)
                        if offset != 0:
                            move_instr.append(MoveAODCol(col, offset))
                    else:
                        offset = col_diff - col_offset
                        if offset != 0:
                            move_instr.append(MoveAODCol(col, offset))
                    counter += 1
                
                reversed_instructions = list(map(reverseInstruction, reversed(move_instr)))
                compiled_instructions.extend(move_instr)
                compiled_instructions.append(RydbergLaser((pos2[1], pos2[0]),
                                                operation=oper.gate))
                compiled_instructions.extend(reversed_instructions)
                    

    return (device, compiled_instructions)