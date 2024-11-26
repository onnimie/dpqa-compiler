import cirq

class Trap:
    def __init__(self, x, y):
        self.y_pos = y
        self.x_pos = x
        self.qubits = []
    
    def get_position_xy(self):
        return (self.x_pos, self.y_pos)

    def add_qubits(self, qubit):
        self.qubits.append(qubit)
        assert(len(self.qubits) == 1)
    
    def remove_qubits(self) -> cirq.Qid:
        assert(len(self.qubits) > 0)
        q = self.qubits[0]
        self.qubits = []
        return q


class AODTrap(Trap):
    def __init__(self, row, col):
        super().__init__(col, row)
        self.movement_vector = (0, 0)

    def move_trap_by(self, offset_x, offset_y):
        self.x_pos += offset_x
        self.y_pos += offset_y
        self.movement_vector = (offset_x, offset_y)


class SLMTrap(Trap):
    def __init__(self, x, y):
        super().__init__(x, y)