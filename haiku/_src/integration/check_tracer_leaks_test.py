# Copyright 2021 DeepMind Technologies Limited. All Rights Reserved.
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
"""Tests for Haiku modules running with leak checking."""

from absl.testing import absltest
from absl.testing import parameterized
import haiku as hk
from haiku._src import test_utils
from haiku._src.integration import descriptors
import jax
import jax.numpy as jnp

ModuleFn = descriptors.ModuleFn


def get_module_cls(module_fn: ModuleFn) -> type[hk.Module]:
  get_cls = lambda: type(descriptors.unwrap(module_fn()))
  return hk.testing.transform_and_run(get_cls)()


class LeakCheckerTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    jax.config.update('jax_check_tracer_leaks', True)

  def tearDown(self):
    super().tearDown()
    jax.config.update('jax_check_tracer_leaks', False)

  @test_utils.combined_named_parameters(descriptors.ALL_MODULES)
  def test_run(self, module_fn: ModuleFn, shape, dtype):
    def g(x):
      return module_fn()(x)

    f = hk.transform_with_state(g)

    def run():
      rng = jax.random.PRNGKey(42)
      x = jnp.zeros(shape, dtype)
      params, state = f.init(rng, x)
      return f.apply(params, state, rng, x)

    jax.eval_shape(run)

if __name__ == '__main__':
  absltest.main()
