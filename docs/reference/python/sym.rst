..  Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

..    http://www.apache.org/licenses/LICENSE-2.0

..  Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.

tvm_tirx.sym
============

.. automodule:: tvm_tirx.sym
   :no-members:

.. currentmodule:: tvm_tirx.sym

Classes
-------

.. autosummary::
   :toctree: generated/

   Constraint
   ConstraintContext
   BindingConstraint
   RangeConstraint
   PredicateConstraint
   IntSet
   IntervalSet
   ModularSet
   ConstIntBound
   Analyzer
   ProofStrength
   CompareResult
   IterMapExpr
   IterMark
   IterSplitExpr
   IterSumExpr

Functions
---------

.. autosummary::
   :toctree: generated/

   estimate_region_lower_bound
   estimate_region_strict_bound
   estimate_region_upper_bound
   allow_uint_as_index
   deduce_bound
   detect_iter_map
   iter_map_simplify
   normalize_iter_map_to_expr
   normalize_to_iter_sum
   subspace_divide
   inverse_affine_iter_map

Supporting classes
------------------

.. autosummary::
   :toctree: generated/

   ~iter_affine_map.IterMapResult
   ~iter_affine_map.IterMapLevel

Supporting functions
--------------------

.. autosummary::
   :toctree: generated/

   ~int_set.pos_inf
   ~int_set.neg_inf
   ~int_set.union_lower_bound

Proof strength and Z3 fallback
-----------------------------

Z3 fallback is an analyzer-instance policy, separate from native proof strength.
In a build with ``TVM_TIRX_USE_Z3=ON``:

* A fresh, unconfigured analyzer permits fallback only at ``SYMBOLIC_BOUND``.
* :py:meth:`Analyzer.enable_z3_fallback` also permits fallback for ``DEFAULT`` queries.
* :py:meth:`Analyzer.disable_z3_fallback` disables fallback for every strength,
  including ``SYMBOLIC_BOUND``. Native symbolic-bound analysis remains available.

Native analysis always runs before a permitted Z3 attempt:

.. code-block:: python

   from tvm_tirx import ir, sym

   x = ir.Var("x", ir.PrimType("int32"))
   y = ir.Var("y", ir.PrimType("int32"))
   condition = x * x + y * y >= 2 * x * y
   prover = sym.Analyzer()
   prover.enable_z3_fallback()
   print(prover.can_prove(condition))
   prover.disable_z3_fallback()
   # Native symbolic-bound analysis is still available, without Z3 fallback.
   print(prover.can_prove(condition, sym.ProofStrength.SYMBOLIC_BOUND))

Nested ``can_prove`` calls and queries reached from ``simplify`` and other
helpers follow the same instance policy. When enabled, each query may try Z3
after its native analysis fails. Disabling fallback prevents those queries
from invoking Z3 too.

The setting belongs to the analyzer instance; a clone inherits it and can
then be configured independently. Toggling it preserves accepted facts and
any existing solver state. Enabling it does not create a solver until needed.
Cloning an unconfigured analyzer preserves its strength-based default; cloning
an explicitly disabled analyzer preserves the prohibition at every strength.

The statement simplification pass owns its analyzers. Configure their fallback
policy at the pass entry instead of configuring an unrelated analyzer:

.. code-block:: python

   from tvm_tirx import tirx

   tirx.transform.StmtSimplify()                 # Preserve the default policy.
   tirx.transform.StmtSimplify(enable_z3=True)   # Permit Z3 fallback in this pass.
   tirx.transform.StmtSimplify(enable_z3=False)  # Prohibit fallback in this pass.

The optional argument defaults to ``None``, which preserves the strength-based
default. Each function gets its own analyzer; this setting does not affect
other passes. It enables Z3 for proof queries made by existing simplification
rules, without requesting an SMT proof of every boolean expression.

:py:attr:`Analyzer.is_z3_enabled` reports whether the build includes Z3,
independently of this setting. Enabling fallback in a build without Z3 has no
effect. Solver timeouts and resource limits still apply. A ``False`` result
means unproved, including when the solver cannot handle a condition or reaches
its limits.
