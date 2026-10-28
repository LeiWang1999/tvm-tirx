# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Minimal LLVM compilation and execution coverage for wheel builds."""

import numpy as np
import pytest

import tvm_tirx
import tvm_tirx.testing
from tvm_tirx.script import tirx as T
from tvm_tirx.support import cc
from tvm_tirx.testing import env


@pytest.mark.skipif(not env.has_llvm(), reason="need llvm")
def test_llvm_add_pipeline():
    @T.function
    def add(
        A: T.Tensor((128,), "float32"),
        B: T.Tensor((128,), "float32"),
        C: T.Tensor((128,), "float32"),
    ):
        T.func_attr({"tirx.noalias": True})
        AA = T.alloc_tensor(ty_args=[T.Tensor((128,), "float32")])
        BB = T.alloc_tensor(ty_args=[T.Tensor((128,), "float32")])
        sum_buffer = T.alloc_tensor(ty_args=[T.Tensor((128,), "float32")])
        for i in range(128):
            AA[i] = A[i]
        for i in range(128):
            BB[i] = B[i]
        for i in range(128):
            sum_buffer[i] = AA[i] + BB[i]
        for outer in T.parallel(32):
            for inner in T.vectorized(4):
                C[outer * 4 + inner] = sum_buffer[outer * 4 + inner]

    kernel = tvm_tirx.compile(add, target="llvm")
    dev = tvm_tirx.cpu(0)
    rng = np.random.default_rng(0)
    a = tvm_tirx.runtime.tensor(rng.uniform(size=128).astype("float32"), dev)
    b = tvm_tirx.runtime.tensor(rng.uniform(size=128).astype("float32"), dev)
    c = tvm_tirx.runtime.tensor(np.zeros(128, dtype="float32"), dev)
    kernel(a, b, c)
    tvm_tirx.testing.assert_allclose(c.numpy(), a.numpy() + b.numpy())


@pytest.mark.skipif(not env.has_llvm(), reason="need llvm")
@pytest.mark.parametrize("fcompile", [None, cc.create_shared])
def test_llvm_export_and_reload(tmp_path, fcompile):
    n = T.dynamic("n")

    @T.function
    def add_one(A: T.Tensor((n,), "float32"), B: T.Tensor((n,), "float32")):
        for i in range(n):
            B[i] = A[i] + 1

    kernel = tvm_tirx.compile(add_one, target="llvm")
    path = tmp_path / "add_one.so"
    kernel.export_library(path, fcompile=fcompile)
    loaded = tvm_tirx.runtime.load_module(str(path))["add_one"]
    dev = tvm_tirx.cpu(0)
    a = tvm_tirx.runtime.tensor(np.arange(10, dtype="float32"), dev)
    b = tvm_tirx.runtime.tensor(np.zeros(10, dtype="float32"), dev)
    loaded(a, b)
    tvm_tirx.testing.assert_allclose(b.numpy(), a.numpy() + 1)

    # Exercise the generated error path that calls the FFI library directly.
    wrong_shape = tvm_tirx.runtime.tensor(np.zeros(11, dtype="float32"), dev)
    with pytest.raises(ValueError, match="shape"):
        loaded(a, wrong_shape)


if __name__ == "__main__":
    tvm_tirx.testing.main()
