#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import pytest

from projectq import MainEngine
from projectq.cengines import (InstructionFilter,
                               AutoReplacer,
                               DecompositionRuleSet)
from projectq.backends import Simulator
from projectq.ops import (All, BasicMathGate, ClassicalInstructionGate,
                          Measure, X)

import projectq.libs.math
from projectq.setups.decompositions import qft2crandhadamard, swap2cnot
from projectq.libs.math import (AddQuantum,
                                SubtractQuantum,
                                Comparator,
                                QuantumConditionalAdd,
                                QuantumDivision,)

def init(engine, quint, value):
    for i in range(len(quint)):
        if ((value >> i) & 1) == 1:
            X | quint[i]


def get_all_probabilities(eng,qureg):
    i = 0
    y = len(qureg)
    while i < (2**y):
       qubit_list = [int(x) for x in list(('{0:0b}'.format(i)).zfill(y))]
       qubit_list = qubit_list[::-1]
       l = eng.backend.get_probability(qubit_list,qureg)
       if l != 0.0:
           print(l,qubit_list, i)
       i += 1

def no_math_emulation(eng, cmd):
    if isinstance(cmd.gate, BasicMathGate):
        return False
    if isinstance(cmd.gate, ClassicalInstructionGate):
        return True
    try:
        return len(cmd.gate.matrix) == 2
    except:
        return False

rule_set = DecompositionRuleSet(modules=[projectq.libs.math, swap2cnot])

def test_quantum_adder():
    sim = Simulator()
    eng = MainEngine(sim, [AutoReplacer(rule_set),
                           InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    c = eng.allocate_qubit()
    init(eng, qureg_a, 2)
    init(eng, qureg_b, 1)
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1,0,0,0],qureg_b))

    AddQuantum() | (qureg_a, qureg_b, c) 
    
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1,1,0,0],qureg_b))

    init(eng, qureg_a, 2) #reset
    init(eng, qureg_b, 3) #reset
    
    init(eng,qureg_a, 15)
    init(eng,qureg_b, 15)

    AddQuantum() | (qureg_a, qureg_b, c)
    
    assert 1. == pytest.approx(eng.backend.get_probability([1,1,1,1],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,1,1],qureg_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1],c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    Measure | c

def test_quantumsubtraction():
    sim = Simulator()
    eng = MainEngine(sim, [AutoReplacer(rule_set),
                           InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(5)
    qureg_b = eng.allocate_qureg(5)

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 7)

    SubtractQuantum() | (qureg_a, qureg_b)

    assert 1. == pytest.approx(eng.backend.get_probability([1,0,1,0,0], qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0,0], qureg_b))

    All(Measure) | qureg_a
    All(Measure) | qureg_b

def test_comparator():

    sim = Simulator()
    eng = MainEngine(sim, [AutoReplacer(rule_set),
                           InstructionFilter(no_math_emulation)])
    qureg_a = eng.allocate_qureg(3)
    qureg_b = eng.allocate_qureg(3)
    compare_qubit = eng.allocate_qubit()

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 3)

    Comparator() | (qureg_a, qureg_b, compare_qubit)

    assert 1. == pytest.approx(eng.backend.get_probability([1], compare_qubit))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    Measure | compare_qubit

def test_quantumconditionaladd():

    sim = Simulator()
    eng = MainEngine(sim, [AutoReplacer(rule_set),
                           InstructionFilter(no_math_emulation)])
    qureg_a = eng.allocate_qureg(5)
    qureg_b = eng.allocate_qureg(5)
    c = eng.allocate_qubit()

    init(eng, qureg_a, 29)
    init(eng, qureg_b, 3)

    QuantumConditionalAdd() | (qureg_a, qureg_b, c)

    assert 1. == pytest.approx(eng.backend.get_probability([0], c)
)

    assert 1. == pytest.approx(eng.backend.get_probability([1,1,0,0,0], qureg_b))

    X | c
    QuantumConditionalAdd() | (qureg_a, qureg_b, c)

    assert 1. == pytest.approx(eng.backend.get_probability([1,1,1,1,1], qureg_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1,1,0,0,0], qureg_a))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    Measure | c

def test_quantumdivision():
    sim = Simulator()
    eng = MainEngine(sim, [AutoReplacer(rule_set),
                           InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    qureg_c = eng.allocate_qureg(4)

    init(eng, qureg_a, 7)
    init(eng, qureg_c, 2)
    

    QuantumDivision() | (qureg_a, qureg_b, qureg_c)

    print(get_all_probabilities(eng, qureg_a))
    print(get_all_probabilities(eng, qureg_b))
    print(get_all_probabilities(eng, qureg_c))

    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0], qureg_a)
)
    assert 1. == pytest.approx(eng.backend.get_probability([1,0,0,0], qureg_b)
)
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0], qureg_c))
