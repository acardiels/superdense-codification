# Superdense Coding Simulator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.5.0-6929C4.svg)](https://github.com/Qiskit/qiskit)

A Python simulation of the **superdense coding protocol** built with [Qiskit](https://github.com/Qiskit/qiskit): Alice sends **two classical bits** to Bob by manipulating only **one qubit** of a shared entangled pair (an EPR pair). The project checks that the protocol worked by comparing the two bits Alice input with the two bits Bob recovers after his Bell-basis measurement.

<p align="center">
  <img src="images/superdense_coding_circuit.png" alt="Superdense coding circuit" width="800">
</p>

## 📖 The protocol in brief

The circuit uses two qubits: `q0` is Alice's and `q1` is Bob's. Both start out entangled in the EPR pair $|\Phi^+\rangle = (|00\rangle + |11\rangle)/\sqrt{2}$.

1. **EPR pair:** `q0` and `q1` are entangled with a Hadamard gate on `q0` followed by a CNOT `q0 → q1`. This is the resource Alice and Bob share *before* Alice knows which bits she wants to send.
2. **Encoding (Alice):** Alice wants to send two classical bits, `b1` and `b0`. She acts only on her own qubit `q0`: applies $X$ if `b0 = 1`, then $Z$ if `b1 = 1`.
3. **Transmission:** Alice sends her single qubit `q0` to Bob — no classical bit is sent, only the qubit. Bob now holds both qubits.
4. **Bell measurement (Bob):** Bob applies a CNOT `q0 → q1` followed by a Hadamard on `q0`, then measures both qubits.
5. **Decoding:** the two classical outcomes are exactly the bits Alice encoded: `c0 = b1` and `c1 = b0`.

Alice's encoding maps the shared pair onto one of the four Bell states:

| `b1 b0` | Gate on `q0` | Resulting state |
|:-------:|:------------:|:----------------:|
| `00`    | none ($I$)   | $\|\Phi^+\rangle = (\|00\rangle+\|11\rangle)/\sqrt2$ |
| `01`    | $X$          | $\|\Psi^+\rangle = (\|10\rangle+\|01\rangle)/\sqrt2$ |
| `10`    | $Z$          | $\|\Phi^-\rangle = (\|00\rangle-\|11\rangle)/\sqrt2$ |
| `11`    | $Z$ then $X$ | $\|\Psi^-\rangle = (\|10\rangle-\|01\rangle)/\sqrt2$ (up to global phase) |

Because the four Bell states are orthogonal, Bob's CNOT + Hadamard step maps each one back to a distinct computational basis state — `00`, `01`, `10`, `11` respectively — so his measurement recovers Alice's two bits with certainty, having transmitted only one qubit.

## ⚛️ Features

*   **Full protocol**: EPR-pair generation, Alice's single-qubit encoding, and Bob's Bell-basis measurement, in a circuit with 2 qubits and 2 classical bits.
*   **User-defined input:** the two bits to send (`b1`, `b0`) are provided by the user, either via CLI flags or interactive prompts.
*   **Deterministic verification:** the protocol is noise-free, so Bob's recovered bits are decoded from a single shot and compared directly against Alice's input.
*   **Command-line interface** to run the simulation and save the circuit diagram.
*   **Explanatory notebook** that walks through the protocol step by step.

## 🚀 Getting started

### 🛠️ Requirements

*   **Python 3.12 or higher** (required by the pinned `numpy` and `scipy` versions in `requeriments.txt`).
*   Main dependencies: `qiskit`, `qiskit-aer`, `numpy`, `matplotlib` and `jupyterlab` (for the notebook).

### ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/acardiels/superdense_codification
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate        # Windows: venv\Scripts\activate
    ```
3.  **Install the dependencies:**
    ```bash
    pip install -r requeriments.txt
    ```

## 💻 Usage

### Script

From the project root:

```bash
python src/superdense_codification.py                     # prompts for b1 and b0
python src/superdense_codification.py --bit1 1 --bit0 0   # bits given directly
python src/superdense_codification.py --bit1 1 --bit0 0 --save   # also save the circuit to images/
```

| Option    | Description                                                          | Default  |
|-----------|-----------------------------------------------------------------------|:--------:|
| `--bit1`  | First bit `b1` Alice wants to send (`0` or `1`). Prompted for if omitted. | —    |
| `--bit0`  | Second bit `b0` Alice wants to send (`0` or `1`). Prompted for if omitted. | —   |
| `--state` | Bell/EPR state used as the shared resource. Only `phi+` for now.      | `phi+`   |
| `--save`  | Saves the circuit diagram (PNG) in the `images/` folder.              | off      |

### Notebook

```bash
jupyter lab
```

Open `superdense_codification.ipynb`: it contains the same implementation split into cells, asks for `b1` and `b0` interactively, draws the circuit, and checks the results.

### Example output

```text
==================================================
Superdense Coding Protocol
==================================================

Bell State/ EPR State — Φ+ (phi+)

--- Bob's Measurement in Bell basis ---
Counts: {'01': 1}
Bits recovered: b1=1  b0=0

--- Comparison ---
Bits sent by Alice:    (1, 0)
Bits recovered by Bob:   (1, 0)
Match: YES
```

`March: YES` means Bob recovered exactly the two bits Alice wanted to send.

## 🧩 How the code works

All functions live in `src/superdense_codification.py`:

| Function | What it does |
|----------|--------------|
| `build_bell_circuit(state)` | Builds the 2-qubit circuit that generates the shared EPR pair $\|\Phi^+\rangle$ (Hadamard + CNOT). |
| `build_superdense_coding_circuit(bit1, bit0, epr_state)` | Assembles the full circuit: EPR pair, Alice's encoding on `q0`, and Bob's Bell-basis measurement. |
| `run_simulation(qc)` | Runs the circuit on `AerSimulator`, executes a single shot (the protocol is deterministic), and decodes the recovered bits from the classical register. |
| `draw_circuit(qc, output_path)` | Draws the circuit with Matplotlib and saves it as a PNG. |
| `generate_superdense_coding(bit1, bit0, ...)` | Full pipeline: build, simulate, and compare Alice's input bits against Bob's recovered bits. |

## 📂 Project structure

```text
superdense_codification/
├── src/
│   └── superdense_codification.py    # Implementation and CLI
├── images/                           # Circuit diagrams
│   └── superdense_coding_circuit_{bit0}{bit1}.png
├── superdense_codification.ipynb     # Step-by-step Jupyter version
├── requeriments.txt                  # Python dependencies
├── LICENSE
└── README.md
```

## 🔭 Future improvements

- [ ] Support all four Bell states as the shared resource (currently only `phi+`).
- [ ] Let the user send a random 2-bit message instead of typing it manually.
- [ ] Add an Aer noise model to study how often Bob misdecodes the bits.
- [ ] Run the circuit on real IBM quantum hardware.
- [ ] Add automated tests that check all four `(b1, b0)` combinations.

## 📚 References

*   C. H. Bennett and S. J. Wiesner, *Communication via one- and two-particle operators on Einstein-Podolsky-Rosen states*, Physical Review Letters **69**, 2881 (1992).
*   M. A. Nielsen and I. L. Chuang, *Quantum Computation and Quantum Information*, Cambridge University Press.
*   [Qiskit documentation](https://github.com/Qiskit/qiskit)

## 🤝 Contributing

Contributions are welcome! If you find bugs or have ideas to improve the simulation:

1.  Fork the project.
2.  Create a new branch (`git checkout -b feature/AmazingFeature`).
3.  Make your changes and commit them (`git commit -m 'feat: Added AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 👤 Author

**Alejandro Cardiel Santos** — [GitHub](https://github.com/acardiels) · [LinkedIn](https://linkedin.com/in/alejandrocardiel)

## 📜 License

This project is distributed under the MIT license. See the `LICENSE` file for details.
