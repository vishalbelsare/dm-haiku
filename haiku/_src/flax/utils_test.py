# Copyright 2023 DeepMind Technologies Limited. All Rights Reserved.
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

"""Tests for haiku._src.flax.utils."""

from absl.testing import absltest
from absl.testing import parameterized
from haiku._src.flax import utils


class UtilsTest(parameterized.TestCase):

  def test_flatten_flax_to_haiku(self):
    variables = {'params': {'mod1': {'mod2': {'w': 0}}, '~': {'w': 1}}}
    hk_params = utils.flatten_flax_to_haiku(variables['params'])
    self.assertEqual(hk_params, {'mod1/mod2': {'w': 0}, '~': {'w': 1}})

  def test_flatten_flax_to_haiku_toplevel(self):
    variables = {'params': {'w': 0}}
    hk_params = utils.flatten_flax_to_haiku(variables['params'])
    self.assertEqual(hk_params, {'~': {'w': 0}})


if __name__ == '__main__':
  absltest.main()
