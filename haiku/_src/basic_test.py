# Copyright 2019 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for haiku._src.basic."""

from absl.testing import absltest
from absl.testing import parameterized
from haiku._src import base
from haiku._src import basic
from haiku._src import test_utils
from haiku._src import transform
import jax
from jax import random
import jax.numpy as jnp
import numpy as np


class BasicTest(parameterized.TestCase):

  def test_onehot_shape(self):
    indices = jnp.arange(24, dtype=jnp.float32).reshape([2, 3, 4])
    num_classes = 24
    out = basic.one_hot(indices, num_classes=num_classes)
    self.assertEqual(out.shape, (2, 3, 4, num_classes))

  @parameterized.parameters(1, 10)
  def test_multinomial_r1(self, num_samples):
    out = basic.multinomial(random.PRNGKey(428), jnp.ones([4]), num_samples)
    self.assertEqual(out.shape, (num_samples,))

  @parameterized.parameters(1, 10)
  def test_multinomial_r2(self, num_samples):
    out = basic.multinomial(random.PRNGKey(428), jnp.ones([3, 4]), num_samples)
    self.assertEqual(out.shape, (3, num_samples))

  @test_utils.transform_and_run
  def test_sequential_params(self):
    seq = basic.Sequential([
        basic.Sequential([basic.Linear(2), basic.Linear(2)]),
        basic.Sequential([lambda x: basic.Linear(2)(x * 1)])
    ])
    for _ in range(2):
      # Connect seq to ensure params are created. Connect twice to ensure that
      # we see the two instances of the lambda Linear.
      seq(jnp.zeros([1, 1]))
    params = seq.params_dict()
    self.assertCountEqual(
        list(params), [
            "linear/w", "linear/b", "linear_1/w", "linear_1/b",
            "sequential_1/linear/w", "sequential_1/linear/b"
        ])

  @test_utils.transform_and_run
  def test_sequential(self):
    seq = basic.Sequential([basic.Linear(2), jax.nn.relu])
    out = seq(jnp.zeros([3, 2]))
    self.assertEqual(out.shape, (3, 2))

  @test_utils.transform_and_run
  def test_dropout(self):
    rate = 0.25
    x = basic.dropout(base.next_rng_key(),
                      rate,
                      jnp.ones([1000, 1000]))  # larger is less flaky test
    self.assertAlmostEqual(jnp.mean(x == 0), rate, delta=0.001)
    # The dropped out tensor is rescaled to preserve the same mean.
    self.assertAlmostEqual(jnp.mean(x), 1.0, delta=0.01)

  @test_utils.transform_and_run
  def test_dropout_broadcasts(self):
    x_in = jnp.ones([3, 3, 3, 3])
    x_out = basic.dropout(base.next_rng_key(),
                          0.5,
                          x_in,
                          broadcast_dims=(1,))
    np.testing.assert_allclose(x_out[:, 0], x_out[:, 1])
    np.testing.assert_allclose(x_out[:, 0], x_out[:, 2])
    self.assertRaises(AssertionError, np.testing.assert_allclose,
                      x_out[:, :, 0], x_out[:, :, 1])
    self.assertRaises(AssertionError, np.testing.assert_allclose,
                      x_out[:, :, 0], x_out[:, :, 2])
    self.assertRaises(AssertionError, np.testing.assert_allclose,
                      x_out[0], x_out[1])
    self.assertEqual(x_in.shape, x_out.shape)

    x_out = basic.dropout(base.next_rng_key(),
                          0.5,
                          x_in,
                          broadcast_dims=(1, 2))
    np.testing.assert_allclose(x_out[:, 0], x_out[:, 1])
    np.testing.assert_allclose(x_out[:, 0], x_out[:, 2])
    np.testing.assert_allclose(x_out[:, :, 0], x_out[:, :, 1])
    np.testing.assert_allclose(x_out[:, :, 0], x_out[:, :, 2])
    self.assertRaises(AssertionError, np.testing.assert_allclose,
                      x_out[0], x_out[1])
    self.assertEqual(x_in.shape, x_out.shape)

  @test_utils.transform_and_run
  def test_dropout_jit(self):
    jax.jit(basic.dropout)(base.next_rng_key(), 0.25, jnp.ones([3, 3]))

  @parameterized.parameters(jnp, np)
  def test_merge_leading_dims_preserves_type(self, xnp):
    inputs = xnp.ones(shape=(2, 3, 4))
    outputs = basic.merge_leading_dims(inputs, 2)
    self.assertEqual(type(inputs), type(outputs))

  @parameterized.parameters(jnp, np)
  def test_split_leading_dims_preserves_type(self, xnp):
    inputs = xnp.ones(shape=(2 * 3, 4))
    outputs = basic.split_leading_dim(inputs, (2, 3))
    self.assertEqual(type(inputs), type(outputs))

  def test_batchapply(self):

    def raises(a, b):
      if len(a.shape) != 2:
        raise ValueError("a must be shape 2")
      if len(b.shape) != 1:
        raise ValueError("b must be shape 1")
      return a + b

    out = basic.BatchApply(raises)(jnp.ones([2, 3, 4]), jnp.ones([4]))
    np.testing.assert_array_equal(out, 2 * jnp.ones([2, 3, 4]))

  def test_batchapply_accepts_float(self):

    def raises(a, b):
      if len(a.shape) != 2:
        raise ValueError("a must be shape 2")
      return a + b

    out = basic.BatchApply(raises)(jnp.ones([2, 3, 4]), 2.)
    np.testing.assert_array_equal(out, 3 * jnp.ones([2, 3, 4]))

  def test_batchapply_accepts_none(self):

    def raises(a, b):
      if a is not None:
        raise ValueError("a must be None.")
      if len(b.shape) != 2:
        raise ValueError("b must be shape 2")
      return 3 * b

    out = basic.BatchApply(raises)(None, jnp.ones([2, 3, 4]))
    np.testing.assert_array_equal(out, 3 * jnp.ones([2, 3, 4]))

  def test_batchapply_raises(self):
    with self.assertRaisesRegex(ValueError, "requires at least one input"):
      basic.BatchApply(lambda: 1)()

  def test_expand_apply(self):

    def raises(a, b):
      if len(a.shape) != 3:
        raise ValueError("a must be shape 3")
      if len(b.shape) != 2:
        raise ValueError("b must be shape 2")
      return a + b

    out = basic.expand_apply(raises)(jnp.ones([3, 4]), jnp.ones([4]))
    np.testing.assert_array_equal(out, 2 * jnp.ones([3, 4]))

  def test_expand_apply_raises(self):
    with self.assertRaisesRegex(ValueError, "only supports axis=0 or axis=-1"):
      basic.expand_apply(lambda: 1, axis=1)()

  @test_utils.transform_and_run
  def test_to_module(self):

    def bias_fn(x):
      b = base.get_parameter("b", [], init=jnp.ones)
      return x + b

    Bias = basic.to_module(bias_fn)  # pylint: disable=invalid-name
    mod = Bias()
    self.assertEqual(mod(jnp.ones([])), 2.)

  @test_utils.transform_and_run
  def test_to_module_error_invalid_name(self):

    def bias_fn(x):
      b = base.get_parameter("b", [], init=jnp.ones)
      return x + b

    cls = basic.to_module(bias_fn)
    garbage = object()
    with self.assertRaisesRegex(TypeError,
                                f"Expected a string name .* got: {garbage}"):
      cls(garbage)  # pytype: disable=wrong-arg-types

  @test_utils.transform_and_run
  def test_to_module_error_docs(self):

    def documented_fn():
      """Really great docs."""

    def undocumented_fn():
      pass

    cls = basic.to_module(documented_fn)
    documented = cls()
    self.assertEqual(documented.__doc__, "Really great docs.")
    self.assertEqual(documented.__call__.__doc__, "Really great docs.")

    cls = basic.to_module(undocumented_fn)
    undocumented = cls()
    self.assertEqual(undocumented.__doc__, "Module produced by `hk.to_module`.")
    self.assertIsNone(undocumented.__call__.__doc__)


class LinearTest(parameterized.TestCase):

  def test_linear_rank1(self):

    def f():
      return basic.Linear(output_size=2)(jnp.zeros([6]))

    init_fn, apply_fn = transform.transform(f)
    params = init_fn(random.PRNGKey(428))
    self.assertEqual(params["linear"]["w"].shape, (6, 2))
    self.assertEqual(params["linear"]["b"].shape, (2,))
    self.assertEqual(apply_fn(params, None).shape, (2,))

  def test_linear_rank2(self):

    def f():
      return basic.Linear(output_size=2)(jnp.zeros((5, 6)))

    init_fn, apply_fn = transform.transform(f)
    params = init_fn(random.PRNGKey(428))
    self.assertEqual(params["linear"]["w"].shape, (6, 2))
    self.assertEqual(params["linear"]["b"].shape, (2,))
    self.assertEqual(apply_fn(params, None).shape, (5, 2))

  def test_linear_rank3(self):

    def f():
      return basic.Linear(output_size=2)(jnp.zeros((2, 5, 6)))

    init_fn, apply_fn = transform.transform(f)
    params = init_fn(random.PRNGKey(428))
    self.assertEqual(params["linear"]["w"].shape, (6, 2))
    self.assertEqual(params["linear"]["b"].shape, (2,))
    self.assertEqual(apply_fn(params, None).shape, (2, 5, 2))

  def test_linear_without_bias_has_zero_in_null_space(self):

    def f():
      return basic.Linear(output_size=6, with_bias=False)(jnp.zeros((5, 6)))

    init_fn, apply_fn = transform.transform(f)
    params = init_fn(random.PRNGKey(428))
    self.assertEqual(params["linear"]["w"].shape, (6, 6))
    self.assertNotIn("b", params["linear"])
    np.testing.assert_array_almost_equal(
        apply_fn(params, None), jnp.zeros((5, 6)))

  @parameterized.parameters(None,
                            jax.lax.Precision.DEFAULT,
                            jax.lax.Precision.HIGH,
                            jax.lax.Precision.HIGHEST)
  def test_precision(self, precision):

    def f(x):
      return basic.Linear(1)(x, precision=precision)

    f = transform.transform(f)
    rng = jax.random.PRNGKey(42)
    x = np.ones([1, 1])
    params = f.init(rng, x)
    c = (
        jax.jit(lambda x: f.apply(params, None, x))
        .lower(x)
        .compiler_ir(dialect="hlo")
    )
    hlo = c.as_hlo_text()
    op_line = next(l for l in hlo.split("\n") if "dot(" in l)
    if precision is not None and precision != jax.lax.Precision.DEFAULT:
      name = str(precision).lower()
      self.assertRegex(op_line, f"operand_precision={{{name},{name}}}")
    else:
      self.assertNotIn("operand_precision", op_line)

if __name__ == "__main__":
  absltest.main()
