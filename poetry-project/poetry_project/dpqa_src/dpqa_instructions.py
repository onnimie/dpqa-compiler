class Instruction:
    def __str__(self):
        return "description of the instruction"

class ActivateAODRow(Instruction):
    def __init__(self, row_index):
        self.row_index = row_index
    def __str__(self):
        return f"activate row {self.row_index}"

class ActivateAODCol(Instruction):
    def __init__(self, col_index):
        self.col_index = col_index
    def __str__(self):
        return f"activate col {self.col_index}"

class DeactivateAODRow(Instruction):
    def __init__(self, row_index):
        self.row_index = row_index
    def __str__(self):
        return f"deactivate row {self.row_index}"

class DeactivateAODCol(Instruction):
    def __init__(self, col_index):
        self.col_index = col_index
    def __str__(self):
        return f"deactivate col {self.col_index}"

class RydbergLaser(Instruction):
    def __init__(self, target_pos_xy, operation):
        self.target_pos = target_pos_xy
        self.operation = operation
    def __str__(self):
        return f"operation {self.operation} at pos {self.target_pos}"

class MoveAODRow(Instruction):
    def __init__(self, row_index, offset):
        self.row_index = row_index
        self.offset = offset
    def __str__(self):
        return f"move row {self.row_index} by {self.offset}"

class MoveAODCol(Instruction):
    def __init__(self, col_index, offset):
        self.col_index = col_index
        self.offset = offset
    def __str__(self):
        return f"move col {self.col_index} by {self.offset}"

class Initialize(Instruction):
    def __init__(self, aod_qubits, aod_qubit_positions_rowcol, slm_qubits, slm_trap_indices):
        assert(len(list(aod_qubits)) == len(list(aod_qubit_positions_rowcol)))
        assert(len(list(slm_qubits)) == len(list(slm_trap_indices)))
        self.aod_qubits = aod_qubits
        self.aod_qubit_positions_rowcol = aod_qubit_positions_rowcol
        self.slm_qubits = slm_qubits
        self.slm_trap_indices = slm_trap_indices
    def __str__(self):
        return f"initialize qubits on traps"

class DrawState(Instruction):
    pass