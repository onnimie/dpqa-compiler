# Attempts for compiling quantum circuits into DPQA instructions

Compiling quantum circuits on fixed planar architectures, e.g. Google's Sycamore, requires additional SWAP gates due to the device's restricted topology.
Dynamically Programmable Quantum Arrays are not as restricted, since the AOD traps may be moved, deactivated/activated to catch/drop qubits on SLM traps during runtime.
The instructions for DPQA processors include moving AOD rows/columns, deactivating/activating them, and shooting a Rydberg Laser to entangle qubits within a small area.

dependencies:

	poetry 1.8
		other dependencies managed by poetry ('poetry install' on the poetry-project directory)
	python 3.10
		use 'poetry env info' to see whether the poetry env uses the correct version. change it by 'poetry env use python{version}'
	
