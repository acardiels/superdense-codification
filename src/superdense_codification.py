"""
Superdense Coding:
— Bell State/ EPR State |Φ+⟩ = (|00⟩ + |11⟩) / √2   (default)
- Two classical bits (b1, b0), introduced by the user, are encoded by
  Alice onto her half of a shared Bell pair and recovered by Bob.
====================
Implementation of the superdense coding protocol using IBM Qiskit.

Author: Alejandro Cardiel Santos
GitHub: github.com/acardiels
"""

from __future__ import annotations

import os
from typing import Literal

import matplotlib.pyplot as plt
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, transpile, QuantumRegister, ClassicalRegister


# ── Type alias ────────────────────────────────────────────────────────────────
BellState = Literal["phi+"]

# ── Bell state circuit builder (shared EPR resource) ────────────────────────

def build_bell_circuit(state: BellState = "phi+") -> QuantumCircuit:
    """
    Build the quantum circuit for the specified Bell state.

    The construction follows two steps:
        1. Hadamard on qubit 0  →  creates superposition |+⟩ on q_0
        2. CNOT (q0 → q1)       →  entangles both qubits

    Additional single-qubit corrections are applied before H to reach
    the other three Bell states:
        |Φ-⟩  →  Z on q_0 after H  (phase flip)
        |Ψ+⟩  →  X on q_1 before H  (bit flip on target)
        |Ψ-⟩  →  X on q_1 + Z on q_0

    Args:
        state: One of "phi+", "phi-", "psi+", "psi-". Defaults to "phi+".

    Returns:
        QuantumCircuit: Parameterised circuit with 2 qubits and 2 classical bits.

    Raises:
        ValueError: If an unknown state label is provided.
    """
    valid = {"phi+", "phi-", "psi+", "psi-"}
    if state not in valid:
        raise ValueError(f"Unknown Bell state '{state}'. Choose from {valid}.")

    qc = QuantumCircuit(2, name=f"Bell |{_latex_label(state)}⟩")


    # ── Step 1: optional pre-corrections ────────────────────────────────────
    if state in ("psi+", "psi-"):
        # Flip target qubit so entanglement produces |01⟩ + |10⟩ basis
        qc.x(1)

    # ── Step 2: Hadamard on control qubit ───────────────────────────────────
    # H |0⟩ = (|0⟩ + |1⟩) / √2  →  equal superposition
    qc.h(0)

    # ── Step 3: optional phase flip ─────────────────────────────────────────
    if state in ("phi-", "psi-"):
        # Z introduces a relative phase: H Z |0⟩ = (|0⟩ - |1⟩) / √2
        qc.z(0)

    # ── Step 4: CNOT — creates entanglement ─────────────────────────────────
    # If q0 = |1⟩, flip q1.  Result: correlated |00⟩ + |11⟩ (or |01⟩ + |10⟩)
    qc.cx(0, 1)

    return qc

'''
def build_bell_circuit(state: BellState = "phi+") -> QuantumCircuit:
    """
    Build the quantum circuit for the specified Bell state.

    This is the entangled resource shared between Alice and Bob before
    the protocol starts: q0 stays with Alice, q1 is sent to Bob.

    The construction follows two steps:
        1. Hadamard on qubit 0  →  creates superposition |+⟩ on q_0
        2. CNOT (q0 → q1)       →  entangles both qubits

    Args:
        state: "phi+".

    Returns:
        QuantumCircuit: Parameterised circuit with 2 qubits.

    Raises:
        ValueError: If an unknown state label is provided.
    """
    valid = {"phi+"}
    if state not in valid:
        raise ValueError(f"Unknown Bell state '{state}'. Choose from {valid}.")

    qc_bell = QuantumCircuit(2)

    # ── Step 1: Hadamard on control qubit ───────────────────────────────────
    # H |0⟩ = (|0⟩ + |1⟩) / √2  →  equal superposition
    qc_bell.h(0)

    # ── Step 2: CNOT — creates entanglement ─────────────────────────────────
    # If q0 = |1⟩, flip q1.  Result: correlated |00⟩ + |11⟩
    qc_bell.cx(0, 1)

    return qc_bell
'''

# --- Superdense Coding Circuit Builder ---

def build_superdense_coding_circuit(bit1: int, bit0: int, epr_state: BellState = "phi+") -> QuantumCircuit:
    """
        Build the quantum circuit for the Superdense Coding protocol.

        The construction follows four steps:
            1. Bell state preparation (q0 and q1)  →  shared entangled pair
               between Alice (q0) and Bob (q1)
            2. Alice's encoding on q0: applies X if bit0 == 1, then Z if
               bit1 == 1, according to the two classical bits she wants
               to send
            3. Alice sends her qubit q0 to Bob (no gate — from this point
               on Bob holds both qubits)
            4. Bob's Bell-basis measurement: CNOT (q0 → q1), Hadamard on
               q0, then measurement of both qubits recovers (bit1, bit0)

        Encoding table (Alice's gate → resulting Bell state):
            b1 b0   Gate      Resulting state
             0  0   I          |Φ+⟩
             0  1   X          |Ψ+⟩
             1  0   Z          |Φ-⟩
             1  1   Z then X   |Ψ-⟩ (up to global phase)

        Args:
            bit1: first classical bit (0 or 1) Alice wants to send.
            bit0: second classical bit (0 or 1) Alice wants to send.
            epr_state: Bell state "phi+" used as the shared resource.

        Returns:
            QuantumCircuit: Parameterised circuit with 2 qubits and 2
            classical bits. c[0] carries the recovered bit1, c[1] the
            recovered bit0.

        Raises:
            ValueError: If bit1/bit0 are not 0 or 1, or epr_state is invalid.
    """

    valid = {"phi+"}

    if epr_state not in valid:
        raise ValueError(f"Invalid EPR state '{epr_state}'. Choose from {valid}.")

    for name, bit in (("bit1", bit1), ("bit0", bit0)):
        if bit not in (0, 1):
            raise ValueError(f"{name} must be 0 or 1, got {bit}.")

    qr = QuantumRegister(2, name="q")
    cr = ClassicalRegister(2, name="c")
    qc_superdense = QuantumCircuit(qr, cr, name="Superdense Coding")

    # ── Step 1: shared Bell pair — Alice keeps q0, Bob keeps q1 ─────────────
    qc_superdense.append(build_bell_circuit(epr_state), [0, 1])
    qc_superdense.barrier()

    # ── Step 2: Alice encodes (bit1, bit0) on her qubit q0 ──────────────────
    if bit0 == 1:
        qc_superdense.x(0)
    if bit1 == 1:
        qc_superdense.z(0)
    qc_superdense.barrier()

    # ── Step 3: Alice sends q0 to Bob — no gate, only a change of "owner" ──

    # ── Step 4: Bob's Bell-basis measurement ────────────────────────────────
    qc_superdense.cx(0, 1)
    qc_superdense.h(0)

    qc_superdense.measure(0, 0)  # c[0] -> recovered bit1
    qc_superdense.measure(1, 1)  # c[1] -> recovered bit0

    return qc_superdense


# ── Simulation ────────────────────────────────────────────────────────────────

def run_simulation(qc: QuantumCircuit) -> tuple[dict[str, int], int, int]:
    """
    Execute the circuit on the local Aer simulator and decode Bob's bits.

    The protocol is deterministic (no noise), so a single shot already
    gives the recovered bits with certainty.

    Args:
        qc: The quantum circuit to simulate.

    Returns:
        tuple: (counts, recovered_bit1, recovered_bit0)
    """
    backend = AerSimulator()
    transpiled = transpile(qc, backend, optimization_level=1)
    result = backend.run(transpiled, shots=1).result()
    counts = result.get_counts()

    # Qiskit reports bitstrings as "c[1]c[0]" (rightmost char = lowest
    # classical bit index), regardless of the order measure() was called in.
    bitstring = list(counts.keys())[0]
    recovered_bit1 = int(bitstring[-1])
    recovered_bit0 = int(bitstring[0])

    return counts, recovered_bit1, recovered_bit0


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


def generate_superdense_coding(bit1: int, bit0: int, state: BellState = "phi+",
    save_images: bool = False,
    images_dir: str = "images",
) -> tuple[dict[str, int], int, int, bool]:
    """
    End-to-end pipeline: build → simulate → compare Alice's bits vs Bob's.

    Args:
        bit1:        First classical bit Alice wants to send.
        bit0:        Second classical bit Alice wants to send.
        state:       Bell state to generate. Defaults to "phi+".
        save_images: If True, save the circuit diagram to ``images_dir``.
        images_dir:  Directory for saved images. Created if absent.

    Returns:
        tuple: (counts, recovered_bit1, recovered_bit0, match) where
        ``match`` is True iff Bob's recovered bits equal Alice's input.

    Example:
        >>> counts, b1, b0, match = generate_superdense_coding(1, 0)
    """
    qc = build_superdense_coding_circuit(bit1, bit0, epr_state=state)
    counts, recovered_bit1, recovered_bit0 = run_simulation(qc)
    match = (recovered_bit1 == bit1) and (recovered_bit0 == bit0)

    if save_images:
        # 1. Obtain the absolute path of 'src/' (where this file is located)
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 2. Subimos un nivel atrás (a la raíz 'superdense_codification/')
        project_root = os.path.dirname(script_dir)

        # 3. Creamos la ruta definitiva hacia 'superdense_codification/images/'
        target_dir = os.path.join(project_root, images_dir)

        # Creamos la carpeta por si acaso no existiera
        os.makedirs(target_dir, exist_ok=True)

        # Guardamos el circuito usando la nueva ruta
        draw_circuit(
            qc,
            output_path=os.path.join(target_dir, f"superdense_coding_circuit_{bit0}{bit1}.png"),
        )

    return counts, recovered_bit1, recovered_bit0, match


# ── Helpers ───────────────────────────────────────────────────────────────────

def _latex_label(state: BellState) -> str:
    """Map state identifier to Unicode-friendly label."""
    return {"phi+": "Φ+"}[state]


def _save_or_show(fig: plt.Figure, path: str | None) -> None:
    """Save figure to path or display interactively."""
    fig.savefig(path, dpi=150, bbox_inches="tight")


def _read_bit(prompt: str) -> int:
    """Ask the user for a single classical bit (0 or 1), re-prompting on bad input."""
    while True:
        raw = input(prompt).strip()
        if raw in ("0", "1"):
            return int(raw)
        print("Entrada no válida: introduce 0 o 1.")


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and simulate the Superdense Coding protocol using Qiskit."
    )

    parser.add_argument(
        "--bit1",
        type=int,
        choices=[0, 1],
        default=None,
        help="First bit Alice wants to send (0 or 1). Prompted for if omitted.",
    )

    parser.add_argument(
        "--bit0",
        type=int,
        choices=[0, 1],
        default=None,
        help="Second bit Alice wants to send (0 or 1). Prompted for if omitted.",
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save circuit image to ./images/",
    )

    parser.add_argument(
        "--state",
        choices=["phi+"],
        default="phi+",
        help="Bell state/ EPR state (phi+)",
    )

    args = parser.parse_args()

    bit1 = args.bit1 if args.bit1 is not None else _read_bit("Introduce the first bit  b1 (0/1): ")
    bit0 = args.bit0 if args.bit0 is not None else _read_bit("Introduce the second bit b0 (0/1): ")

    print(f"\n{'='*50}")
    print(f"Superdense Coding Protocol")
    print(f"{'='*50}")

    print(f"\nBits introduced by Alice: b0={bit0} b1={bit1}  ")
    print(f"Bell State/ EPR State — {args.state} ({_latex_label(args.state)})\n")

    counts, recovered_bit1, recovered_bit0, match = generate_superdense_coding(
        bit1=bit1,
        bit0=bit0,
        state=args.state,
        save_images=args.save,
    )

    print("--- Bob's Measurement in Bell basis ---")
    print(f"Counts: {counts}")
    print(f"Bits recovered: b0={recovered_bit0} b1={recovered_bit1}")

    print("\n--- Comparison ---")
    print(f"Bits sent by Alice:    ({bit0}, {bit1})")
    print(f"Bits recovered by Bob:   ({recovered_bit0}, {recovered_bit1})")
    print(f"Match: {'YES' if match else 'NO'}\n")
