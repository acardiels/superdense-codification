"""
Quantum Teleportation:
— Bell State/ EPR State |Φ+⟩ = (|00⟩ + |11⟩) / √2   (default)
- Random Quantum State Ψ to teleport: |Ψ⟩ = α|0⟩ + β|1⟩
====================
Implementation of the quantum teleportation protocol using IBM Qiskit.

Author: Alejandro Cardiel Santos
GitHub: github.com/acardiels
"""

from __future__ import annotations

import os
from typing import Literal
import numpy as np

import matplotlib.pyplot as plt
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, transpile, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import random_statevector, Statevector, partial_trace, state_fidelity



# ── Type alias ────────────────────────────────────────────────────────────────
BellState = Literal["phi+"]

# ── Bell state circuit builder ──────────────────────────────────────────────────────

def build_bell_circuit(state: BellState = "phi+") -> QuantumCircuit:
    """
    Build the quantum circuit for the specified Bell state.

    The construction follows two steps:
        1. Hadamard on qubit 0  →  creates superposition |+⟩ on q_0
        2. CNOT (q0 → q1)       →  entangles both qubits


    Args:
        state: "phi+".

    Returns:
        QuantumCircuit: Parameterised circuit with 2 qubits and 2 classical bits.

    Raises:
        ValueError: If an unknown state label is provided.
    """
    valid = {"phi+"}
    if state not in valid:
        raise ValueError(f"Unknown Bell state '{state}'. Choose from {valid}.")

    qc_bell = QuantumCircuit(2)

    # ── Step 1: optional pre-corrections ────────────────────────────────────
    if state in ("psi+", "psi-"):
        # Flip target qubit so entanglement produces |01⟩ + |10⟩ basis
        qc_bell.x(1)
    
    # ── Step 2: Hadamard on control qubit ───────────────────────────────────
    # H |0⟩ = (|0⟩ + |1⟩) / √2  →  equal superposition
    qc_bell.h(0)
    
    # ── Step 3: optional phase flip ─────────────────────────────────────────
    if state in ("phi-", "psi-"):
        # Z introduces a relative phase: H Z |0⟩ = (|0⟩ - |1⟩) / √2
        qc_bell.z(0)
    
    # ── Step 4: CNOT — creates entanglement ─────────────────────────────────
    # If q0 = |1⟩, flip q1.  Result: correlated |00⟩ + |11⟩ (or |01⟩ + |10⟩)
    qc_bell.cx(0, 1)


    return qc_bell

# --- Quantum Teleportation Circuit Builder ---

def build_quantum_teleportation_circuit(quantum_state, epr_state: BellState = "phi+") -> QuantumCircuit:
    """
        Build the quantum circuit for the Quantum Teleportation protocol.
    
        The construction follows two steps:
            1. Bell state preparation (q1 and q2)  →  creates entangled pair
            2. CNOT (q0 → q1)       →  entangles both qubits
            3. Hadamard on qubit 0  →  creates superposition |+⟩ on q_0
            4. Measurement of q0 and q1  →  collapses the state of q2 to the teleported state
    
        Args:
            state: Bell state "phi+" as EPR state.
            quantum_state: The quantum state to be teleported.
    
        Returns:
            QuantumCircuit: Parameterised circuit with 3 qubits and 2 classical bits.
    
        Raises:
            ValueError: If an unknown Bell state "phi+" label is provided.
    """

    valid = {"phi+"}

    if epr_state not in valid:
            raise ValueError(f"Invalid EPR state '{epr_state}'. Choose from {valid}.")

    qr = QuantumRegister(3, name="q")
    cr = ClassicalRegister(2, name="c")    
    qc_quantum_teleportation = QuantumCircuit(qr, cr, name="Quantum Teleportation for State Ψ")

    qc_quantum_teleportation.initialize(quantum_state, 0)

    qc_quantum_teleportation.append(build_bell_circuit(epr_state), [1, 2])

    qc_quantum_teleportation.cx(0, 1)
    qc_quantum_teleportation.h(0)

    qc_quantum_teleportation.measure([0, 1], [0, 1])

    # If bit 1 is 1 (c[1] == 1) -> Apply X gate
    with qc_quantum_teleportation.if_test((cr[1], 1)):
        qc_quantum_teleportation.x(qr[2])

    # If bit 0 is 1 (c[0] == 1) -> Apply Z gate
    with qc_quantum_teleportation.if_test((cr[0], 1)):
        qc_quantum_teleportation.z(qr[2])

    return qc_quantum_teleportation



# ── Simulation ────────────────────────────────────────────────────────────────

def run_simulation(quantum_state, qc: QuantumCircuit) -> dict[str, int]:
    """
    Execute the circuit on the local Aer statevector simulator.

    Args:
            qc: The quantum circuit to simulate.
            quantum_state: The quantum state to be teleported.
    
        Returns:
            dict: Fidelity, Bob's final state, and Alice's initial state.
    """
    backend = AerSimulator(method="statevector")
    qc_sim = qc.copy()
    qc_sim.save_density_matrix()

    transpiled = transpile(qc_sim, backend, optimization_level=1)
    result = backend.run(transpiled).result()

    rho_total = result.data()["density_matrix"]

    rho_bob = partial_trace(rho_total, [0, 1])

    state_alice = Statevector(quantum_state)

    fidelity = state_fidelity(state_alice, rho_bob)

    state_bob = rho_bob.to_statevector()

    state_bob_corrected = fix_global_phase(state_bob, state_alice)

    return result.get_counts(), fidelity, state_bob_corrected, state_alice

    
# ── Visualisation ─────────────────────────────────────────────────────────────

def draw_circuit(qc: QuantumCircuit, output_path: str | None = None) -> None:
    """
    Render and optionally save the circuit diagram.

    Args:
        qc:          Circuit to draw.
        output_path: File path for saving (PNG). If None, displays interactively.
    """
    fig = qc.draw(output="mpl", fold=-1)
    _save_or_show(fig, output_path)


# ── Convenience runner ────────────────────────────────────────────────────────


def generate_quantum_teleportation(quantum_state, state: BellState = "phi+", save_images: bool = False, images_dir: str = "images",) -> tuple[dict[str, int], float, np.ndarray, Statevector]:
    """
    End-to-end pipeline: build → simulate → Check the results

    Args:
        state:       Bell state to generate. Defaults to "phi+".
        save_images: If True, save circuit and histogram to ``images_dir``.
        images_dir:  Directory for saved images. Created if absent.
        quantum_state: The quantum state to be teleported.

    Returns:
        dict: Fidelity, Bob's final state, and Alice's initial state.

    Example:
        >>> counts = generate_quantum_teleportation(quantum_state, "phi+", save_images=True)
    """
    qc = build_quantum_teleportation_circuit(quantum_state, epr_state=state)
    counts, fidelity, state_bob_corrected, state_alice = run_simulation(quantum_state, qc)

    if save_images:
        # 1. Obtain the absolute path of 'src/' (where this file is located)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Subimos un nivel atrás (a la raíz 'bell_states/')
        project_root = os.path.dirname(script_dir)
        
        # 3. Creamos la ruta definitiva hacia 'bell_states/images/'
        target_dir = os.path.join(project_root, images_dir)
        
        # Creamos la carpeta por si acaso no existiera
        os.makedirs(target_dir, exist_ok=True)
        
        # Guardamos el circuito y los resultados usando la nueva ruta
        draw_circuit(
            qc,
            output_path=os.path.join(target_dir, f"quantum_teleportation_circuit_quantum_state.png"),
        )

    return counts, fidelity, state_bob_corrected, state_alice

# ── Helpers ───────────────────────────────────────────────────────────────────

def _latex_label(state: BellState) -> str:
    """Map state identifier to Unicode-friendly label."""
    return {"phi+": "Φ+", "phi-": "Φ-", "psi+": "Ψ+", "psi-": "Ψ-"}[state]


def _save_or_show(fig: plt.Figure, path: str | None) -> None:
    """Save figure to path or display interactively."""
    fig.savefig(path, dpi=150, bbox_inches="tight")
    

def fix_global_phase(state_target: Statevector, state_source: Statevector) -> Statevector:
    """ Delete global phase from state_target to align it with state_source."""
    # Obtain the difference in phase for the first element |0>
    phase_diff = np.angle(state_source.data[0]) - np.angle(state_target.data[0])
    # Apply the inverse phase rotation
    corrected_data = state_target.data * np.exp(1j * phase_diff)
    return Statevector(corrected_data)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    quantum_state = random_statevector(2, seed=42) 

    quantum_state_latex = quantum_state.draw('text')

    parser = argparse.ArgumentParser(
        description="Generate and simulate Quantum Teleportation using Qiskit."
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save circuit images to ./images/",
    )
    
    parser.add_argument(
        "--state",
        choices=["phi+"],
        default="phi+",
        help="Bell state/ EPR state (phi+)",
    )
        
    args = parser.parse_args()


    print(f"\n{'='*50}")
    print(f"Quantum Teleportation Protocol")
    print(f"{'='*50}")

    print(f"\nRandom Quantum State Ψ to teleport: |Ψ⟩ = α|0⟩ + β|1⟩")
    print(f"Quantum State Ψ — {quantum_state_latex}")

    print(f"Bell State/ EPR State — {args.state} ({_latex_label(args.state)})\n")

    counts, fidelity, state_bob_corrected, state_alice = generate_quantum_teleportation(
        state=args.state,
        quantum_state=quantum_state, 
        save_images=args.save,
)
    print("--- Qubit 0 state (Alice initial) ---")
    print(state_alice.draw('text')) 
    print()
    print("--- Qubit 2 state (Bob final - Density Matrix) ---")
    print(state_bob_corrected.draw('text'))

    print("\n")
    print(f"Fidelity: {fidelity:.6f}\n")